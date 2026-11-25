from django.contrib import admin

from .models import LearningMaterial, MaterialCompletion


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "material_type", "order", "created_at")
    list_filter = ("material_type",)
    search_fields = ("title", "course__title")


@admin.register(MaterialCompletion)
class MaterialCompletionAdmin(admin.ModelAdmin):
    list_display = ("student", "material", "completed_at")
    search_fields = ("student__username", "material__title")
