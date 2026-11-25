from django.http import HttpResponse


def login_view(request):
    return HttpResponse("login")


def logout_view(request):
    return HttpResponse("logout")


def register_view(request):
    return HttpResponse("register")


def dashboard_redirect(request):
    return HttpResponse("dashboard")


def profile_view(request):
    return HttpResponse("profile")


def password_change_view(request):
    return HttpResponse("password change")
