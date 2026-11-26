from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Course, Enrollment


class CoursePhase3Tests(TestCase):
    def create_user(self, username, role, password="Testpass123!"):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=password,
            role=role,
        )

    def setUp(self):
        self.admin = self.create_user("admin1", User.Role.ADMIN)
        self.trainer = self.create_user("trainer1", User.Role.TRAINER)
        self.trainer2 = self.create_user("trainer2", User.Role.TRAINER)
        self.student = self.create_user("student1", User.Role.STUDENT)
        self.course = Course.objects.create(
            title="Python Basics",
            description="Intro course",
            category="Programming",
            trainer=self.trainer,
            status=Course.Status.PUBLISHED,
        )
        self.draft = Course.objects.create(
            title="Draft Course",
            description="Draft",
            category="Programming",
            trainer=self.trainer,
            status=Course.Status.DRAFT,
        )

    def test_student_sees_only_published_courses(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("courses:course_list"))
        self.assertContains(response, "Python Basics")
        self.assertNotContains(response, "Draft Course")

    def test_trainer_can_create_course(self):
        self.client.force_login(self.trainer)
        response = self.client.post(
            reverse("courses:course_create"),
            {
                "title": "New Course",
                "description": "Desc",
                "category": "Testing",
                "status": Course.Status.DRAFT,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(title="New Course", trainer=self.trainer).exists())

    def test_trainer_cannot_edit_other_trainers_course(self):
        self.client.force_login(self.trainer2)
        response = self.client.post(
            reverse("courses:course_edit", args=[self.course.pk]),
            {
                "title": "Hacked",
                "description": "x",
                "category": "x",
                "status": Course.Status.PUBLISHED,
            },
        )
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "Python Basics")
        self.assertNotEqual(response.status_code, 200)

    def test_student_can_enroll_once(self):
        self.client.force_login(self.student)
        url = reverse("courses:enroll_course", args=[self.course.pk])
        first = self.client.post(url)
        second = self.client.post(url)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(Enrollment.objects.filter(student=self.student, course=self.course).count(), 1)

    def test_anonymous_can_view_published_course_detail(self):
        response = self.client.get(reverse("courses:course_detail", args=[self.course.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Basics")

    def test_course_search_filters_results(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("courses:course_list"), {"q": "Python"})
        self.assertContains(response, "Python Basics")
        response = self.client.get(reverse("courses:course_list"), {"q": "Nonexistent"})
        self.assertNotContains(response, "Python Basics")

    def test_student_cannot_access_course_manage(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("courses:course_manage"))
        self.assertEqual(response.status_code, 403)
