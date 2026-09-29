from django.urls import Resolver404, resolve
from wagtail_2fa.middleware import VerifyUserMiddleware as BaseVerifyUserMiddleware

# Публічні сторінки сайту: 2FA на них не потрібна, щоб редактор без налаштованого пристрою
# міг переглядати сайт. Чернетки й попередній перегляд відкриваються через адмінку — там 2FA діє.
PUBLIC_URL_NAMES = {"wagtail_serve"}


class VerifyUserMiddleware(BaseVerifyUserMiddleware):
    """2FA-middleware wagtail-2fa з двома відмінностями від оригіналу.

    1. Не падає на адресах без маршруту: оригінал викликає resolve() без обробки Resolver404,
       тож для адміністратора, який увійшов, але ще не пройшов 2FA, будь-яка неіснуюча адреса
       (наприклад, /favicon.ico) давала 500 замість 404.
    2. Не вимагає 2FA на публічних сторінках сайту (PUBLIC_URL_NAMES).
    """

    def _require_verified_user(self, request):
        try:
            if resolve(request.path_info).url_name in PUBLIC_URL_NAMES:
                return False
            return super()._require_verified_user(request)
        except Resolver404:
            return False
