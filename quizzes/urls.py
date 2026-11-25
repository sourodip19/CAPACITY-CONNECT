from django.urls import path

from . import views

app_name = "quizzes"

urlpatterns = [
    path("course/<int:course_pk>/", views.quiz_list, name="quiz_list"),
    path("course/<int:course_pk>/create/", views.quiz_create, name="quiz_create"),
    path("<int:pk>/", views.quiz_detail, name="quiz_detail"),
    path("<int:pk>/edit/", views.quiz_edit, name="quiz_edit"),
    path("<int:pk>/delete/", views.quiz_delete, name="quiz_delete"),
    path("<int:pk>/take/", views.quiz_take, name="quiz_take"),
    path("<int:pk>/result/", views.quiz_result, name="quiz_result"),
    path("<int:quiz_pk>/questions/add/", views.question_add, name="question_add"),
    path("questions/<int:question_pk>/edit/", views.question_edit, name="question_edit"),
    path("questions/<int:question_pk>/delete/", views.question_delete, name="question_delete"),
]
