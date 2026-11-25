from django.contrib import admin

from .models import Course, Enrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "trainer", "category", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "description", "trainer__username")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "enrolled_at")
    list_filter = ("status",)
    search_fields = ("student__username", "course__title")
