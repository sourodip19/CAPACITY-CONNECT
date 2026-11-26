from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Course, Enrollment
from notifications.models import Notification


class NotificationTests(TestCase):
    def setUp(self):
        self.trainer = User.objects.create_user(username="trainer1", email="trainer1@example.com", password="pass12345", role=User.Role.TRAINER)
        self.student = User.objects.create_user(username="student1", email="student1@example.com", password="pass12345", role=User.Role.STUDENT)
        self.course = Course.objects.create(
            title="Notify Course",
            description="Desc",
            category="Testing",
            trainer=self.trainer,
            status=Course.Status.PUBLISHED,
        )

    def test_enrollment_creates_notifications(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("courses:enroll_course", args=[self.course.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Notification.objects.filter(recipient=self.trainer, message__icontains="enrolled").exists())
        self.assertTrue(Notification.objects.filter(recipient=self.student, message__icontains="You enrolled").exists())

    def test_notification_list_and_mark_read(self):
        notification = Notification.objects.create(recipient=self.student, message="Hello", link="/courses/")
        self.client.force_login(self.student)

        list_response = self.client.get(reverse("notifications:notification_list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Hello")

        read_response = self.client.get(reverse("notifications:notification_mark_read", args=[notification.pk]))
        self.assertEqual(read_response.status_code, 302)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(recipient=self.student, message="N1")
        Notification.objects.create(recipient=self.student, message="N2")
        self.client.force_login(self.student)
        response = self.client.post(reverse("notifications:notification_mark_all_read"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Notification.objects.filter(recipient=self.student, is_read=False).count(), 0)
