from django.urls import path

from . import views

app_name = "materials"

urlpatterns = [
    path("course/<int:course_pk>/", views.material_list, name="material_list"),
    path("course/<int:course_pk>/add/", views.material_create, name="material_create"),
    path("<int:pk>/edit/", views.material_edit, name="material_edit"),
    path("<int:pk>/delete/", views.material_delete, name="material_delete"),
    path("<int:pk>/complete/", views.material_complete, name="material_complete"),
]
