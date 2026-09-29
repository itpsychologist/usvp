from django.db import migrations

TITLE = "Головна"


def create_homepage(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Locale = apps.get_model("wagtailcore.Locale")
    Page = apps.get_model("wagtailcore.Page")
    Site = apps.get_model("wagtailcore.Site")
    HomePage = apps.get_model("home.HomePage")

    # Прибрати стандартну сторінку-привітання Wagtail
    Page.objects.filter(depth=2, url_path="/home/").delete()

    locale = Locale.objects.filter(language_code="uk").first() or Locale.objects.first()
    content_type, _ = ContentType.objects.get_or_create(model="homepage", app_label="home")

    homepage = HomePage.objects.create(
        title=TITLE,
        draft_title=TITLE,
        slug="home",
        content_type=content_type,
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/home/",
        locale=locale,
    )

    Site.objects.update_or_create(
        is_default_site=True,
        defaults={"hostname": "localhost", "root_page": homepage, "site_name": "УСВП Лубни"},
    )


def remove_homepage(apps, schema_editor):
    apps.get_model("home.HomePage").objects.filter(slug="home", depth=2).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0001_initial"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]

    operations = [migrations.RunPython(create_homepage, remove_homepage)]
