from django.urls import path

from apps.core import styleguide

app_name = "styleguide"

urlpatterns = [
    path("", styleguide.index, name="index"),
    path("wireframes/<slug:name>/", styleguide.wireframe, name="wireframe"),
]
