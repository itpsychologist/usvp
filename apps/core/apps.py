from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    verbose_name = "Ядро сайту"

    def ready(self):
        from django.db.models.signals import post_delete, post_save
        from wagtail.models import Page
        from wagtail.signals import (
            page_published,
            page_slug_changed,
            page_unpublished,
            post_page_move,
        )

        from apps.core.models import MenuItem, NavigationMenu
        from apps.core.navigation import clear_navigation_cache

        # Меню кешується: скидаємо кеш, коли змінюються сторінки чи саме меню
        for signal in (page_published, page_unpublished, page_slug_changed, post_page_move):
            signal.connect(clear_navigation_cache, dispatch_uid=f"nav-cache-{signal}")
        for model in (Page, NavigationMenu, MenuItem):
            post_save.connect(
                clear_navigation_cache, sender=model, dispatch_uid=f"nav-save-{model}"
            )
            post_delete.connect(
                clear_navigation_cache, sender=model, dispatch_uid=f"nav-delete-{model}"
            )
