import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from courses.models import Course, Enrollment
from .models import LearningMaterial, MaterialCompletion


class MaterialPhase4Tests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._temp_media = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._temp_media)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        shutil.rmtree(cls._temp_media, ignore_errors=True)
        super().tearDownClass()

    def create_user(self, username, role):
        return User.objects.create_user(
            username=username, email=f"{username}@example.com", password="Testpass123!", role=role
        )

    def setUp(self):
        self.trainer = self.create_user("trainer1", User.Role.TRAINER)
        self.student = self.create_user("student1", User.Role.STUDENT)
        self.other_student = self.create_user("student2", User.Role.STUDENT)
        self.course = Course.objects.create(
            title="Course A", description="Desc", category="Cat", trainer=self.trainer, status=Course.Status.PUBLISHED
        )
        Enrollment.objects.create(student=self.student, course=self.course)
        self.material = LearningMaterial.objects.create(
            course=self.course,
            title="Doc Link",
            material_type=LearningMaterial.MaterialType.EXTERNAL_LINK,
            external_url="https://example.com/doc",
        )

    def test_enrolled_student_can_view_materials(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("materials:material_list", args=[self.course.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Doc Link")

    def test_non_enrolled_student_cannot_view_materials(self):
        self.client.force_login(self.other_student)
        response = self.client.get(reverse("materials:material_list", args=[self.course.pk]))
        self.assertEqual(response.status_code, 302)

    def test_trainer_can_add_pdf_material(self):
        self.client.force_login(self.trainer)
        pdf = SimpleUploadedFile("lesson.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        response = self.client.post(
            reverse("materials:material_create", args=[self.course.pk]),
            {
                "title": "Lesson PDF",
                "description": "PDF lesson",
                "material_type": LearningMaterial.MaterialType.PDF,
                "file": pdf,
                "external_url": "",
                "order": 1,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LearningMaterial.objects.filter(course=self.course, title="Lesson PDF").exists())

    def test_student_can_mark_material_complete_once(self):
        self.client.force_login(self.student)
        url = reverse("materials:material_complete", args=[self.material.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(MaterialCompletion.objects.filter(student=self.student, material=self.material).count(), 1)
