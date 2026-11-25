from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from courses.models import Course, Enrollment
from notifications.models import Notification

from .decorators import admin_required, student_required, trainer_required
from .forms import (
    StudentProfileForm,
    StudentRegistrationForm,
    StyledAuthenticationForm,
    StyledPasswordChangeForm,
    TrainerCreationForm,
    TrainerProfileForm,
    UserProfileForm,
)
from .models import StudentProfile, TrainerProfile, User


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard_redirect")
    form = StyledAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if not user.is_active:
            messages.error(request, "Your account is inactive. Please contact an administrator.")
            return redirect("accounts:login")
        login(request, user)
        messages.success(request, f"Welcome back, {user.get_short_name() or user.username}!")
        next_url = request.GET.get("next") or "accounts:dashboard_redirect"
        return redirect(next_url)
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have been logged out.")
    return redirect("home")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard_redirect")
    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Registration successful. Welcome to Capacity Connect!")
        return redirect("accounts:dashboard_redirect")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser or user.role == User.Role.ADMIN:
        return redirect("accounts:admin_dashboard")
    if user.role == User.Role.TRAINER:
        return redirect("accounts:trainer_dashboard")
    return redirect("accounts:student_dashboard")


@login_required
def profile_view(request):
    user = request.user
    profile_form = None
    if user.role == User.Role.STUDENT:
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        profile_form = StudentProfileForm(request.POST or None, instance=profile)
    elif user.role == User.Role.TRAINER:
        profile, _ = TrainerProfile.objects.get_or_create(user=user)
        profile_form = TrainerProfileForm(request.POST or None, instance=profile)

    user_form = UserProfileForm(request.POST or None, instance=user)
    if request.method == "POST" and user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
        user_form.save()
        if profile_form is not None:
            profile_form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("accounts:profile")

    return render(
        request,
        "accounts/profile.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


@login_required
def password_change_view(request):
    form = StyledPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Your password was changed successfully.")
        return redirect("accounts:profile")
    return render(request, "accounts/password_change.html", {"form": form})


@admin_required
def admin_dashboard(request):
    context = {
        "total_users": User.objects.count(),
        "total_students": User.objects.filter(role=User.Role.STUDENT).count(),
        "total_trainers": User.objects.filter(role=User.Role.TRAINER).count(),
        "total_courses": Course.objects.count(),
        "total_enrollments": Enrollment.objects.count(),
        "recent_users": User.objects.order_by("-date_joined")[:5],
        "recent_courses": Course.objects.select_related("trainer").order_by("-created_at")[:5],
    }
    return render(request, "accounts/admin_dashboard.html", context)


@admin_required
def manage_users(request):
    role = request.GET.get("role", "").upper()
    users = User.objects.all().order_by("-date_joined")
    if role in {User.Role.ADMIN, User.Role.TRAINER, User.Role.STUDENT}:
        users = users.filter(role=role)
    return render(request, "accounts/manage_users.html", {"users": users, "selected_role": role})


@admin_required
def create_trainer(request):
    form = TrainerCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Trainer account created successfully.")
        return redirect("accounts:manage_users")
    return render(request, "accounts/create_trainer.html", {"form": form})


@admin_required
def toggle_user_active(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        if target == request.user:
            messages.error(request, "You cannot deactivate your own account.")
        elif target.is_superuser:
            messages.error(request, "Superuser accounts cannot be modified here.")
        else:
            target.is_active = not target.is_active
            target.save(update_fields=["is_active"])
            state = "activated" if target.is_active else "deactivated"
            messages.success(request, f"User {target.username} {state}.")
    return redirect("accounts:manage_users")


@trainer_required
def trainer_dashboard(request):
    courses = Course.objects.filter(trainer=request.user).order_by("-created_at")
    course_ids = courses.values_list("id", flat=True)
    context = {
        "courses": courses[:5],
        "course_count": courses.count(),
        "published_count": courses.filter(status=Course.Status.PUBLISHED).count(),
        "enrollment_count": Enrollment.objects.filter(course_id__in=course_ids).count(),
    }
    return render(request, "accounts/trainer_dashboard.html", context)


@student_required
def student_dashboard(request):
    enrollments = (
        Enrollment.objects.filter(student=request.user)
        .select_related("course", "course__trainer")
        .order_by("-enrolled_at")
    )
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
    context = {
        "enrollments": enrollments[:5],
        "enrollment_count": enrollments.count(),
        "completed_count": enrollments.filter(status=Enrollment.Status.COMPLETED).count(),
        "unread_notifications": unread_notifications,
    }
    return render(request, "accounts/student_dashboard.html", context)
