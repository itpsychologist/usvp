from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from apps.organization.models import Department, Person, VeteranSpace, VeteranSpecialist


class DepartmentViewSet(SnippetViewSet):
    model = Department
    icon = "group"
    list_display = ["name", "phone", "sort_order"]
    search_fields = ["name"]


class PersonViewSet(SnippetViewSet):
    model = Person
    icon = "user"
    list_display = ["name", "position", "is_leadership", "sort_order"]
    list_filter = ["is_leadership", "department"]
    search_fields = ["name", "position"]


class VeteranSpecialistViewSet(SnippetViewSet):
    model = VeteranSpecialist
    icon = "user"
    list_display = ["name", "territory", "phone"]
    search_fields = ["name", "territory"]


class VeteranSpaceViewSet(SnippetViewSet):
    model = VeteranSpace
    icon = "home"
    list_display = ["name", "address"]


class OrganizationViewSetGroup(SnippetViewSetGroup):
    menu_label = "Структура"
    menu_icon = "group"
    menu_order = 250
    items = (DepartmentViewSet, PersonViewSet, VeteranSpecialistViewSet, VeteranSpaceViewSet)


register_snippet(OrganizationViewSetGroup)
