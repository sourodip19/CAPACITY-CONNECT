from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    path("profile/", views.profile_view, name="profile"),
    path("password-change/", views.password_change_view, name="password_change"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/trainer/", views.trainer_dashboard, name="trainer_dashboard"),
    path("dashboard/student/", views.student_dashboard, name="student_dashboard"),
    path("admin/users/", views.manage_users, name="manage_users"),
    path("admin/users/create-trainer/", views.create_trainer, name="create_trainer"),
    path("admin/users/<int:user_id>/toggle-active/", views.toggle_user_active, name="toggle_user_active"),
]
