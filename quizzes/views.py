from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import User
from courses.models import Course, Enrollment
from notifications.services import notify_user, notify_users
from progress.services import sync_enrollment_status

from .forms import AnswerOptionFormSet, QuestionForm, QuizForm
from .models import AnswerOption, Question, Quiz, QuizAttempt, StudentAnswer


def _can_manage_course(user, course):
    return user.is_authenticated and (
        user.is_superuser or user.role == User.Role.ADMIN or course.trainer_id == user.id
    )


def _is_enrolled(user, course):
    return user.is_authenticated and user.role == User.Role.STUDENT and Enrollment.objects.filter(student=user, course=course).exists()


@login_required
def quiz_list(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    can_manage = _can_manage_course(request.user, course)
    if not can_manage and not _is_enrolled(request.user, course):
        messages.error(request, "You must be enrolled in this course to view quizzes.")
        return redirect("courses:course_detail", pk=course.pk)

    quizzes = list(course.quizzes.all())
    if not can_manage:
        quizzes = [q for q in quizzes if q.is_published]

    attempts = {}
    if request.user.role == User.Role.STUDENT:
        attempts = {
            a.quiz_id: a
            for a in QuizAttempt.objects.filter(student=request.user, quiz__course=course)
        }
    for quiz in quizzes:
        quiz.user_attempt = attempts.get(quiz.id)
    return render(request, "quizzes/quiz_list.html", {"course": course, "quizzes": quizzes, "can_manage": can_manage})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def quiz_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if not _can_manage_course(request.user, course):
        messages.error(request, "You do not have permission to create quizzes for this course.")
        return redirect("courses:course_detail", pk=course.pk)
    form = QuizForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quiz = form.save(commit=False)
        quiz.course = course
        quiz.created_by = request.user
        quiz.save()
        if quiz.is_published:
            recipients = User.objects.filter(enrollments__course=course, role=User.Role.STUDENT, is_active=True).distinct()
            notify_users(
                recipients,
                f"New quiz published in {course.title}: {quiz.title}.",
                sender=request.user,
                link=f"/quizzes/{quiz.pk}/",
            )
        messages.success(request, "Quiz created successfully. Add questions next.")
        return redirect("quizzes:quiz_detail", pk=quiz.pk)
    return render(request, "quizzes/quiz_form.html", {"form": form, "course": course, "title": "Create Quiz"})


@login_required
def quiz_detail(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course", "created_by"), pk=pk)
    course = quiz.course
    can_manage = _can_manage_course(request.user, course)
    if not can_manage and not (_is_enrolled(request.user, course) and quiz.is_published):
        messages.error(request, "You do not have access to this quiz.")
        return redirect("courses:course_detail", pk=course.pk)

    questions = quiz.questions.prefetch_related("options").all()
    attempt = None
    if request.user.role == User.Role.STUDENT:
        attempt = QuizAttempt.objects.filter(quiz=quiz, student=request.user).first()
    return render(
        request,
        "quizzes/quiz_detail.html",
        {"quiz": quiz, "course": course, "questions": questions, "can_manage": can_manage, "attempt": attempt},
    )


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def quiz_edit(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course"), pk=pk)
    if not _can_manage_course(request.user, quiz.course):
        messages.error(request, "You do not have permission to edit this quiz.")
        return redirect("quizzes:quiz_detail", pk=pk)
    was_published = quiz.is_published
    form = QuizForm(request.POST or None, instance=quiz)
    if request.method == "POST" and form.is_valid():
        quiz = form.save()
        if quiz.is_published and not was_published:
            recipients = User.objects.filter(enrollments__course=quiz.course, role=User.Role.STUDENT, is_active=True).distinct()
            notify_users(
                recipients,
                f"New quiz published in {quiz.course.title}: {quiz.title}.",
                sender=request.user,
                link=f"/quizzes/{quiz.pk}/",
            )
        messages.success(request, "Quiz updated successfully.")
        return redirect("quizzes:quiz_detail", pk=quiz.pk)
    return render(request, "quizzes/quiz_form.html", {"form": form, "course": quiz.course, "quiz": quiz, "title": "Edit Quiz"})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course"), pk=pk)
    course = quiz.course
    if not _can_manage_course(request.user, course):
        messages.error(request, "You do not have permission to delete this quiz.")
        return redirect("quizzes:quiz_detail", pk=pk)
    if request.method == "POST":
        quiz.delete()
        messages.success(request, "Quiz deleted.")
        return redirect("quizzes:quiz_list", course_pk=course.pk)
    return render(request, "quizzes/quiz_confirm_delete.html", {"quiz": quiz, "course": course})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def question_add(request, quiz_pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course"), pk=quiz_pk)
    if not _can_manage_course(request.user, quiz.course):
        messages.error(request, "Permission denied.")
        return redirect("quizzes:quiz_detail", pk=quiz.pk)
    question = Question(quiz=quiz)
    form = QuestionForm(request.POST or None, instance=question)
    formset = AnswerOptionFormSet(request.POST or None, instance=question)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        correct_count = sum(1 for f in formset.cleaned_data if f and f.get("is_correct") and not f.get("DELETE"))
        if correct_count != 1:
            messages.error(request, "Each question must have exactly one correct answer.")
        else:
            question = form.save()
            formset.instance = question
            formset.save()
            messages.success(request, "Question added successfully.")
            return redirect("quizzes:quiz_detail", pk=quiz.pk)
    return render(request, "quizzes/question_form.html", {"quiz": quiz, "course": quiz.course, "form": form, "formset": formset, "title": "Add Question"})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def question_edit(request, question_pk):
    question = get_object_or_404(Question.objects.select_related("quiz__course"), pk=question_pk)
    quiz = question.quiz
    if not _can_manage_course(request.user, quiz.course):
        messages.error(request, "Permission denied.")
        return redirect("quizzes:quiz_detail", pk=quiz.pk)
    form = QuestionForm(request.POST or None, instance=question)
    formset = AnswerOptionFormSet(request.POST or None, instance=question)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        correct_count = sum(1 for f in formset.cleaned_data if f and f.get("is_correct") and not f.get("DELETE"))
        if correct_count != 1:
            messages.error(request, "Each question must have exactly one correct answer.")
        else:
            form.save()
            formset.save()
            messages.success(request, "Question updated successfully.")
            return redirect("quizzes:quiz_detail", pk=quiz.pk)
    return render(request, "quizzes/question_form.html", {"quiz": quiz, "course": quiz.course, "form": form, "formset": formset, "question": question, "title": "Edit Question"})


@role_required(User.Role.TRAINER, User.Role.ADMIN)
def question_delete(request, question_pk):
    question = get_object_or_404(Question.objects.select_related("quiz__course"), pk=question_pk)
    quiz = question.quiz
    if not _can_manage_course(request.user, quiz.course):
        messages.error(request, "Permission denied.")
        return redirect("quizzes:quiz_detail", pk=quiz.pk)
    if request.method == "POST":
        question.delete()
        messages.success(request, "Question deleted.")
    return redirect("quizzes:quiz_detail", pk=quiz.pk)


@login_required
@role_required(User.Role.STUDENT)
def quiz_take(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course").prefetch_related("questions__options"), pk=pk)
    course = quiz.course
    if not quiz.is_published:
        messages.error(request, "This quiz is not available.")
        return redirect("quizzes:quiz_list", course_pk=course.pk)
    if not _is_enrolled(request.user, course):
        messages.error(request, "You must be enrolled in this course to take this quiz.")
        return redirect("courses:course_detail", pk=course.pk)
    if QuizAttempt.objects.filter(quiz=quiz, student=request.user).exists():
        messages.info(request, "You have already attempted this quiz.")
        return redirect("quizzes:quiz_result", pk=quiz.pk)

    questions = list(quiz.questions.prefetch_related("options").all())
    if not questions:
        messages.error(request, "This quiz has no questions yet.")
        return redirect("quizzes:quiz_list", course_pk=course.pk)

    if request.method == "POST":
        if QuizAttempt.objects.filter(quiz=quiz, student=request.user).exists():
            messages.info(request, "You have already attempted this quiz.")
            return redirect("quizzes:quiz_result", pk=quiz.pk)

        answers_to_create = []
        score = 0
        for question in questions:
            selected_id = request.POST.get(f"question_{question.id}")
            selected_option = None
            if selected_id:
                selected_option = question.options.filter(pk=selected_id).first()
            if selected_option and selected_option.is_correct:
                score += 1
            answers_to_create.append((question, selected_option))

        total = len(questions)
        percentage = (score / total * 100) if total else 0
        try:
            with transaction.atomic():
                attempt = QuizAttempt.objects.create(
                    quiz=quiz,
                    student=request.user,
                    score=score,
                    total_questions=total,
                    percentage=percentage,
                )
                StudentAnswer.objects.bulk_create([
                    StudentAnswer(attempt=attempt, question=q, selected_option=opt)
                    for q, opt in answers_to_create
                ])
        except IntegrityError:
            messages.info(request, "You have already attempted this quiz.")
            return redirect("quizzes:quiz_result", pk=quiz.pk)

        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        if enrollment:
            sync_enrollment_status(enrollment)
        notify_user(
            request.user,
            f"You completed {quiz.title} with a score of {score}/{total} ({percentage:.2f}%).",
            link=f"/quizzes/{quiz.pk}/result/",
        )

        messages.success(request, f"Quiz submitted. Your score: {score}/{total} ({percentage:.2f}%).")
        return redirect("quizzes:quiz_result", pk=quiz.pk)

    return render(request, "quizzes/quiz_take.html", {"quiz": quiz, "course": course, "questions": questions})


@login_required
@role_required(User.Role.STUDENT)
def quiz_result(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course"), pk=pk)
    attempt = get_object_or_404(
        QuizAttempt.objects.prefetch_related("answers__selected_option", "answers__question__options"),
        quiz=quiz,
        student=request.user,
    )
    return render(request, "quizzes/quiz_result.html", {"quiz": quiz, "course": quiz.course, "attempt": attempt})
