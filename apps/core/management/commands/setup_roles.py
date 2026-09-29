"""Створює (або оновлює) групи «Адміністратори» й «Контент-менеджери» з правами Wagtail.

Команда ідемпотентна: її можна запускати після кожного деплою, вона лише додає відсутні права.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from wagtail.models import Collection, GroupCollectionPermission, GroupPagePermission, Page

ADMINS = "Адміністратори"
EDITORS = "Контент-менеджери"
WAGTAIL_DEFAULT_GROUPS = ["Editors", "Moderators"]

# Права на сторінки від кореня дерева
PAGE_PERMISSIONS = [
    "add_page",
    "change_page",
    "publish_page",
    "bulk_delete_page",
    "lock_page",
    "unlock_page",
]

# Права на зображення й документи в кореневій колекції
COLLECTION_PERMISSIONS = [
    "wagtailimages.add_image",
    "wagtailimages.change_image",
    "wagtailimages.delete_image",
    "wagtailimages.choose_image",
    "wagtaildocs.add_document",
    "wagtaildocs.change_document",
    "wagtaildocs.delete_document",
    "wagtaildocs.choose_document",
]

# Загальні права: контент-менеджер лише входить в адмінку
EDITOR_PERMISSIONS = ["wagtailadmin.access_admin"]

# Адміністратор додатково керує налаштуваннями сайту, меню, редиректами, користувачами й групами
ADMIN_PERMISSIONS = [
    *EDITOR_PERMISSIONS,
    "core.change_sitesettings",
    "core.add_navigationmenu",
    "core.change_navigationmenu",
    "core.delete_navigationmenu",
    "wagtailredirects.add_redirect",
    "wagtailredirects.change_redirect",
    "wagtailredirects.delete_redirect",
    "auth.add_user",
    "auth.change_user",
    "auth.delete_user",
    "auth.add_group",
    "auth.change_group",
    "auth.delete_group",
    "wagtailcore.add_workflow",
    "wagtailcore.change_workflow",
    "wagtailcore.add_task",
    "wagtailcore.change_task",
]


def get_permission(label):
    app_label, codename = label.split(".")
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


class Command(BaseCommand):
    help = "Створює групи «Адміністратори» й «Контент-менеджери» з потрібними правами."

    def handle(self, *args, **options):
        root_page = Page.get_first_root_node()
        root_collection = Collection.get_first_root_node()

        for name, general in ((EDITORS, EDITOR_PERMISSIONS), (ADMINS, ADMIN_PERMISSIONS)):
            group, created = Group.objects.get_or_create(name=name)
            group.permissions.add(*[get_permission(label) for label in general])
            for codename in PAGE_PERMISSIONS:
                GroupPagePermission.objects.get_or_create(
                    group=group,
                    page=root_page,
                    permission=get_permission(f"wagtailcore.{codename}"),
                )
            for label in COLLECTION_PERMISSIONS:
                GroupCollectionPermission.objects.get_or_create(
                    group=group, collection=root_collection, permission=get_permission(label)
                )
            status = "створено" if created else "оновлено"
            self.stdout.write(self.style.SUCCESS(f"Групу «{name}» {status}."))

        # Команда лише додає права. Стандартні групи Wagtail мають власні права на сторінки —
        # попереджаємо, якщо в них є користувачі, щоб ролі не розходилися з цією моделлю.
        for group in Group.objects.filter(
            name__in=WAGTAIL_DEFAULT_GROUPS, user__isnull=False
        ).distinct():
            self.stdout.write(
                self.style.WARNING(
                    f"У стандартній групі Wagtail «{group.name}» є користувачі. "
                    f"Перенесіть їх у «{EDITORS}» або «{ADMINS}»."
                )
            )
