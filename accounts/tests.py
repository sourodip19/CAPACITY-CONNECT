from django.test import TestCase
from django.urls import reverse

from .models import StudentProfile, TrainerProfile, User


class AccountsPhase2Tests(TestCase):
    def create_user(self, username, role, password="Testpass123!", **kwargs):
        return User.objects.create_user(
            username=username,
            email=kwargs.get("email", f"{username}@example.com"),
            password=password,
            first_name=kwargs.get("first_name", username.title()),
            last_name=kwargs.get("last_name", "User"),
            role=role,
        )

    def test_student_registration_creates_student_and_profile(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "student1",
                "first_name": "Student",
                "last_name": "One",
                "email": "student1@example.com",
                "phone_number": "1234567890",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, reverse("accounts:dashboard_redirect"), fetch_redirect_response=False)
        user = User.objects.get(username="student1")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())

    def test_trainer_cannot_self_register_through_student_form(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertContains(response, "Create your student account")
        self.assertNotContains(response, "Trainer")

    def test_admin_can_create_trainer_account(self):
        admin = self.create_user("admin1", User.Role.ADMIN)
        admin.is_staff = True
        admin.save()
        self.client.force_login(admin)
        response = self.client.post(
            reverse("accounts:create_trainer"),
            {
                "username": "trainer1",
                "first_name": "Trainer",
                "last_name": "One",
                "email": "trainer1@example.com",
                "expertise": "Data Science",
                "phone_number": "9999999999",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, reverse("accounts:manage_users"))
        trainer = User.objects.get(username="trainer1")
        self.assertEqual(trainer.role, User.Role.TRAINER)
        self.assertTrue(TrainerProfile.objects.filter(user=trainer, expertise="Data Science").exists())

    def test_non_admin_cannot_create_trainer(self):
        student = self.create_user("student2", User.Role.STUDENT)
        self.client.force_login(student)
        response = self.client.get(reverse("accounts:create_trainer"))
        self.assertEqual(response.status_code, 403)

    def test_role_based_dashboard_redirects(self):
        admin = self.create_user("admin2", User.Role.ADMIN)
        trainer = self.create_user("trainer2", User.Role.TRAINER)
        student = self.create_user("student3", User.Role.STUDENT)

        self.client.force_login(admin)
        self.assertRedirects(self.client.get(reverse("accounts:dashboard_redirect")), reverse("accounts:admin_dashboard"))
        self.client.force_login(trainer)
        self.assertRedirects(self.client.get(reverse("accounts:dashboard_redirect")), reverse("accounts:trainer_dashboard"))
        self.client.force_login(student)
        self.assertRedirects(self.client.get(reverse("accounts:dashboard_redirect")), reverse("accounts:student_dashboard"))

    def test_inactive_user_cannot_login(self):
        user = self.create_user("student4", User.Role.STUDENT)
        user.is_active = False
        user.save()
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "student4", "password": "Testpass123!"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "alert-danger")
