from django.conf import settings
from django.db import models


class LearningMaterial(models.Model):
    class MaterialType(models.TextChoices):
        PDF = "PDF", "PDF"
        EXTERNAL_LINK = "EXTERNAL_LINK", "External Link"

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="materials",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=MaterialType.choices)
    file = models.FileField(upload_to="learning_materials/", blank=True, null=True)
    external_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.course.title})"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.material_type == self.MaterialType.PDF and not self.file:
            raise ValidationError("A PDF file is required for PDF materials.")
        if self.material_type == self.MaterialType.EXTERNAL_LINK and not self.external_url:
            raise ValidationError("An external URL is required for link materials.")


class MaterialCompletion(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="material_completions",
    )
    material = models.ForeignKey(
        LearningMaterial,
        on_delete=models.CASCADE,
        related_name="completions",
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "material"],
                name="unique_student_material_completion",
            )
        ]

    def __str__(self) -> str:
        return f"{self.student} completed {self.material}"