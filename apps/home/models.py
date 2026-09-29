from wagtail.models import Page


class HomePage(Page):
    """Головна сторінка сайту. Блоки (hero, швидкі дії, новини) додаються у Фазі 2."""

    max_count_per_parent = 1
    parent_page_types = ["wagtailcore.Page"]

    class Meta:
        verbose_name = "Головна сторінка"
        verbose_name_plural = "Головні сторінки"
