import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse

from apps.core.management.commands.setup_roles import ADMINS, EDITORS

ADMIN_URL = f"/{settings.WAGTAIL_ADMIN_PATH}"


@pytest.fixture
def roles():
    call_command("setup_roles", stdout=None)


def make_user(username, group_name=None, **extra):
    user = get_user_model().objects.create_user(username, password="Pa55word-test", **extra)
    if group_name:
        user.groups.add(Group.objects.get(name=group_name))
    return user


def test_setup_roles_is_idempotent(roles):
    call_command("setup_roles")
    assert Group.objects.filter(name__in=[ADMINS, EDITORS]).count() == 2


def test_editor_permissions(roles):
    editor = make_user("editor", EDITORS)
    assert editor.has_perm("wagtailadmin.access_admin")
    assert editor.has_perm("organization.change_person")
    assert editor.has_perm("news.add_newstopic")
    assert not editor.has_perm("core.change_sitesettings")
    assert not editor.has_perm("core.change_navigationmenu")
    assert not editor.has_perm("auth.change_user")


def test_admin_permissions(roles):
    admin = make_user("admin", ADMINS)
    assert admin.has_perm("core.change_sitesettings")
    assert admin.has_perm("core.change_navigationmenu")
    assert admin.has_perm("auth.change_user")


def test_editor_can_edit_pages_but_not_settings_or_users(client, roles):
    client.force_login(make_user("editor", EDITORS))

    assert client.get(ADMIN_URL).status_code == 200
    assert client.get(reverse("wagtailadmin_explore_root")).status_code == 200
    # Wagtail перенаправляє на головну адмінки з повідомленням про брак прав
    for url in (reverse("wagtailusers_users:index"), f"{ADMIN_URL}settings/core/sitesettings/"):
        response = client.get(url)
        assert response.status_code == 302, url
        assert response["Location"] == ADMIN_URL, url


def test_login_is_locked_after_repeated_failures(client):
    make_user("editor")
    login_url = reverse("wagtailadmin_login")
    for _ in range(settings.AXES_FAILURE_LIMIT):
        client.post(login_url, {"username": "editor", "password": "wrong"})

    response = client.post(login_url, {"username": "editor", "password": "Pa55word-test"})

    assert response.status_code == 429
    assert "Вхід тимчасово заблоковано" in response.content.decode()


def test_2fa_required_for_admin_users(client, settings, roles):
    settings.WAGTAIL_2FA_REQUIRED = True
    client.force_login(make_user("editor", EDITORS))

    response = client.get(ADMIN_URL)
    assert response.status_code == 302
    assert reverse("wagtail_2fa_device_new") in response["Location"]

    # Адреса без маршруту для такого користувача — 404, а не помилка сервера
    assert client.get("/favicon.ico").status_code == 404


def test_2fa_does_not_affect_visitors(client, settings):
    settings.WAGTAIL_2FA_REQUIRED = True
    assert client.get("/").status_code == 200


def test_2fa_passes_after_verification(client, settings, roles):
    from django_otp.plugins.otp_totp.models import TOTPDevice

    settings.WAGTAIL_2FA_REQUIRED = True
    user = make_user("editor", EDITORS)
    device = TOTPDevice.objects.create(user=user, name="телефон", confirmed=True)
    client.force_login(user)

    response = client.get(ADMIN_URL)
    assert response.status_code == 302
    assert reverse("wagtail_2fa_auth") in response["Location"]

    # Так django-otp позначає сесію після введення коду
    session = client.session
    session["otp_device_id"] = device.persistent_id
    session.save()
    assert client.get(ADMIN_URL).status_code == 200


def test_2fa_not_required_on_public_pages(client, settings, roles):
    settings.WAGTAIL_2FA_REQUIRED = True
    client.force_login(make_user("editor", EDITORS))
    assert client.get("/").status_code == 200


def test_svg_images_are_rejected():
    from django.core.exceptions import ValidationError
    from django.core.files.uploadedfile import SimpleUploadedFile
    from wagtail.images.fields import WagtailImageField

    svg = SimpleUploadedFile("herb.svg", b'<svg xmlns="http://www.w3.org/2000/svg"></svg>')
    with pytest.raises(ValidationError):
        WagtailImageField().clean(svg)
