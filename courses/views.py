from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User

from .forms import CourseForm
from .models import Course, Enrollment


def course_list(request):
    courses = Course.objects.select_related("trainer").all()
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()

    if not request.user.is_authenticated or request.user.role == User.Role.STUDENT:
        courses = courses.filter(status=Course.Status.PUBLISHED)
    elif request.user.role == User.Role.TRAINER:
        courses = courses.filter(Q(status=Course.Status.PUBLISHED) | Q(trainer=request.user))
    # admins/superusers see all

    if query:
        courses = courses.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(category__icontains=query)
        )
    if category:
        courses = courses.filter(category__iexact=category)
    if status and request.user.is_authenticated and request.user.role in {User.Role.ADMIN, User.Role.TRAINER} or request.user.is_superuser:
        courses = courses.filter(status=status)

    categories = (
        Course.objects.filter(status=Course.Status.PUBLISHED)
        .order_by("category")
        .values_list("category", flat=True)
        .distinct()
    )
    return render(
        request,
        "courses/course_list.html",
        {
            "courses": courses,
            "query": query,
            "selected_category": category,
            "selected_status": status,
            "categories": categories,
            "status_choices": Course.Status.choices,
        },
    )


def course_detail(request, pk):
    course = get_object_or_404(Course.objects.select_related("trainer"), pk=pk)
    is_owner = request.user.is_authenticated and course.trainer_id == request.user.id
    is_admin = request.user.is_authenticated and (request.user.is_superuser or request.user.role == User.Role.ADMIN)
    if course.status != Course.Status.PUBLISHED and not (is_owner or is_admin):
        messages.error(request, "This course is not available.")
        return redirect("courses:course_list")

    enrollment = None
    if request.user.is_authenticated and request.user.role == User.Role.STUDENT:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()

    enrollments_count = course.enrollments.count()
    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "enrollment": enrollment,
            "is_owner": is_owner,
            "is_admin": is_admin,
            "enrollments_count": enrollments_count,
        },
    )


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def course_create(request):
    form = CourseForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        course = form.save()
        messages.success(request, "Course created successfully.")
        return redirect("courses:course_detail", pk=course.pk)
    return render(request, "courses/course_form.html", {"form": form, "title": "Create Course"})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    is_admin = request.user.is_superuser or request.user.role == User.Role.ADMIN
    if not is_admin and course.trainer_id != request.user.id:
        messages.error(request, "You do not have permission to edit this course.")
        return redirect("courses:course_detail", pk=pk)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Course updated successfully.")
        return redirect("courses:course_detail", pk=course.pk)
    return render(request, "courses/course_form.html", {"form": form, "title": "Edit Course", "course": course})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    is_admin = request.user.is_superuser or request.user.role == User.Role.ADMIN
    if not is_admin and course.trainer_id != request.user.id:
        messages.error(request, "You do not have permission to delete this course.")
        return redirect("courses:course_detail", pk=pk)
    if request.method == "POST":
        course.delete()
        messages.success(request, "Course deleted successfully.")
        return redirect("courses:course_manage")
    return render(request, "courses/course_confirm_delete.html", {"course": course})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def course_manage(request):
    courses = Course.objects.select_related("trainer").all()
    if request.user.role == User.Role.TRAINER:
        courses = courses.filter(trainer=request.user)
    return render(request, "courses/course_manage.html", {"courses": courses})


@login_required
@role_required(User.Role.STUDENT)
def enroll_course(request, pk):
    course = get_object_or_404(Course, pk=pk, status=Course.Status.PUBLISHED)
    if request.method == "POST":
        enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
        if created:
            messages.success(request, f"You have enrolled in {course.title}.")
        else:
            messages.info(request, "You are already enrolled in this course.")
    return redirect("courses:course_detail", pk=pk)
