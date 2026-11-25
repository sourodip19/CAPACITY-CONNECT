from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from courses.models import Course, Enrollment

from .forms import LearningMaterialForm
from .models import LearningMaterial, MaterialCompletion


def _can_manage_course(user, course):
    return user.is_authenticated and (
        user.is_superuser or user.role == User.Role.ADMIN or course.trainer_id == user.id
    )


def _can_view_course_materials(user, course):
    if _can_manage_course(user, course):
        return True
    if not user.is_authenticated or user.role != User.Role.STUDENT:
        return False
    return Enrollment.objects.filter(student=user, course=course).exists()


@login_required
def material_list(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if not _can_view_course_materials(request.user, course):
        messages.error(request, "You must be enrolled in this course to view materials.")
        return redirect("courses:course_detail", pk=course.pk)

    materials = course.materials.all()
    completed_ids = set()
    if request.user.role == User.Role.STUDENT:
        completed_ids = set(
            MaterialCompletion.objects.filter(student=request.user, material__course=course).values_list("material_id", flat=True)
        )
    return render(
        request,
        "materials/material_list.html",
        {
            "course": course,
            "materials": materials,
            "completed_ids": completed_ids,
            "can_manage": _can_manage_course(request.user, course),
        },
    )


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def material_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if not _can_manage_course(request.user, course):
        messages.error(request, "You do not have permission to add materials to this course.")
        return redirect("courses:course_detail", pk=course.pk)
    form = LearningMaterialForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        material = form.save(commit=False)
        material.course = course
        material.save()
        messages.success(request, "Learning material added successfully.")
        return redirect("materials:material_list", course_pk=course.pk)
    return render(request, "materials/material_form.html", {"form": form, "course": course, "title": "Add Material"})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def material_edit(request, pk):
    material = get_object_or_404(LearningMaterial.objects.select_related("course"), pk=pk)
    course = material.course
    if not _can_manage_course(request.user, course):
        messages.error(request, "You do not have permission to edit this material.")
        return redirect("materials:material_list", course_pk=course.pk)
    form = LearningMaterialForm(request.POST or None, request.FILES or None, instance=material)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Learning material updated successfully.")
        return redirect("materials:material_list", course_pk=course.pk)
    return render(request, "materials/material_form.html", {"form": form, "course": course, "material": material, "title": "Edit Material"})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def material_delete(request, pk):
    material = get_object_or_404(LearningMaterial.objects.select_related("course"), pk=pk)
    course = material.course
    if not _can_manage_course(request.user, course):
        messages.error(request, "You do not have permission to delete this material.")
        return redirect("materials:material_list", course_pk=course.pk)
    if request.method == "POST":
        material.delete()
        messages.success(request, "Learning material deleted.")
        return redirect("materials:material_list", course_pk=course.pk)
    return render(request, "materials/material_confirm_delete.html", {"material": material, "course": course})


@login_required
@role_required(User.Role.STUDENT)
def material_complete(request, pk):
    material = get_object_or_404(LearningMaterial.objects.select_related("course"), pk=pk)
    course = material.course
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, "You must be enrolled in this course.")
        return redirect("courses:course_detail", pk=course.pk)
    if request.method == "POST":
        _, created = MaterialCompletion.objects.get_or_create(student=request.user, material=material)
        if created:
            messages.success(request, f"Marked '{material.title}' as complete.")
        else:
            messages.info(request, "This material is already marked as complete.")
    return redirect("materials:material_list", course_pk=course.pk)
