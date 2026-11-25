from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Course, Enrollment
from .models import AnswerOption, Question, Quiz, QuizAttempt


class QuizPhase5Tests(TestCase):
    def create_user(self, username, role):
        return User.objects.create_user(
            username=username, email=f"{username}@example.com", password="Testpass123!", role=role
        )

    def setUp(self):
        self.trainer = self.create_user("trainer1", User.Role.TRAINER)
        self.student = self.create_user("student1", User.Role.STUDENT)
        self.student2 = self.create_user("student2", User.Role.STUDENT)
        self.course = Course.objects.create(
            title="Course A", description="D", category="Cat", trainer=self.trainer, status=Course.Status.PUBLISHED
        )
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=self.student2, course=self.course)
        self.quiz = Quiz.objects.create(
            course=self.course, title="Quiz 1", description="", created_by=self.trainer, is_published=True
        )
        self.q1 = Question.objects.create(quiz=self.quiz, text="2+2?", order=1)
        self.opt1 = AnswerOption.objects.create(question=self.q1, text="3", is_correct=False)
        self.opt2 = AnswerOption.objects.create(question=self.q1, text="4", is_correct=True)
        self.opt3 = AnswerOption.objects.create(question=self.q1, text="5", is_correct=False)

    def test_trainer_can_create_quiz(self):
        self.client.force_login(self.trainer)
        response = self.client.post(
            reverse("quizzes:quiz_create", args=[self.course.pk]),
            {"title": "New Quiz", "description": "Desc", "is_published": True},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Quiz.objects.filter(course=self.course, title="New Quiz").exists())

    def test_student_can_take_quiz_and_get_scored(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("quizzes:quiz_take", args=[self.quiz.pk]),
            {f"question_{self.q1.pk}": str(self.opt2.pk)},
        )
        self.assertRedirects(response, reverse("quizzes:quiz_result", args=[self.quiz.pk]))
        attempt = QuizAttempt.objects.get(quiz=self.quiz, student=self.student)
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.total_questions, 1)
        self.assertEqual(float(attempt.percentage), 100.0)

    def test_student_cannot_attempt_quiz_twice(self):
        self.client.force_login(self.student)
        url = reverse("quizzes:quiz_take", args=[self.quiz.pk])
        self.client.post(url, {f"question_{self.q1.pk}": str(self.opt2.pk)})
        response = self.client.post(url, {f"question_{self.q1.pk}": str(self.opt1.pk)})
        self.assertEqual(QuizAttempt.objects.filter(quiz=self.quiz, student=self.student).count(), 1)
        attempt = QuizAttempt.objects.get(quiz=self.quiz, student=self.student)
        self.assertEqual(attempt.score, 1)  # original score preserved

    def test_unpublished_quiz_not_visible_to_student(self):
        self.quiz.is_published = False
        self.quiz.save()
        self.client.force_login(self.student)
        response = self.client.get(reverse("quizzes:quiz_list", args=[self.course.pk]))
        self.assertNotContains(response, "Quiz 1")
