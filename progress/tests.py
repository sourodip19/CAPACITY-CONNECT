from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Course, Enrollment
from materials.models import LearningMaterial, MaterialCompletion
from progress.services import get_course_progress, sync_enrollment_status
from quizzes.models import AnswerOption, Question, Quiz, QuizAttempt


class ProgressServiceTests(TestCase):
    def setUp(self):
        self.trainer = User.objects.create_user(username="trainer1", email="trainer1@example.com", password="pass12345", role=User.Role.TRAINER)
        self.student = User.objects.create_user(username="student1", email="student1@example.com", password="pass12345", role=User.Role.STUDENT)
        self.course = Course.objects.create(
            title="Progress Course",
            description="Desc",
            category="Testing",
            trainer=self.trainer,
            status=Course.Status.PUBLISHED,
        )
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.material = LearningMaterial.objects.create(
            course=self.course,
            title="Material 1",
            material_type=LearningMaterial.MaterialType.EXTERNAL_LINK,
            external_url="https://example.com/1",
        )
        self.quiz = Quiz.objects.create(course=self.course, title="Quiz 1", created_by=self.trainer, is_published=True)
        question = Question.objects.create(quiz=self.quiz, text="Q1", order=1)
        AnswerOption.objects.create(question=question, text="A", is_correct=True)
        AnswerOption.objects.create(question=question, text="B", is_correct=False)

    def test_progress_counts_materials_and_published_quizzes(self):
        progress = get_course_progress(self.student, self.course)
        self.assertEqual(progress["total_items"], 2)
        self.assertEqual(progress["completed_items"], 0)
        self.assertEqual(progress["percentage"], 0.0)

        MaterialCompletion.objects.create(student=self.student, material=self.material)
        progress = get_course_progress(self.student, self.course)
        self.assertEqual(progress["completed_items"], 1)
        self.assertEqual(progress["percentage"], 50.0)

        QuizAttempt.objects.create(quiz=self.quiz, student=self.student, score=1, total_questions=1, percentage=100)
        progress = get_course_progress(self.student, self.course)
        self.assertEqual(progress["completed_items"], 2)
        self.assertEqual(progress["percentage"], 100.0)

    def test_sync_enrollment_status_marks_completed(self):
        MaterialCompletion.objects.create(student=self.student, material=self.material)
        QuizAttempt.objects.create(quiz=self.quiz, student=self.student, score=1, total_questions=1, percentage=100)
        sync_enrollment_status(self.enrollment)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, Enrollment.Status.COMPLETED)
