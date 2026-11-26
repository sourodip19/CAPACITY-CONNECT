from django.db.models import Count, Q

from courses.models import Enrollment
from materials.models import LearningMaterial, MaterialCompletion
from quizzes.models import Quiz, QuizAttempt


def get_course_progress(student, course):
    material_ids = list(LearningMaterial.objects.filter(course=course).values_list("id", flat=True))
    quiz_ids = list(Quiz.objects.filter(course=course, is_published=True).values_list("id", flat=True))

    total_items = len(material_ids) + len(quiz_ids)
    completed_materials = 0
    completed_quizzes = 0
    if material_ids:
        completed_materials = MaterialCompletion.objects.filter(student=student, material_id__in=material_ids).count()
    if quiz_ids:
        completed_quizzes = QuizAttempt.objects.filter(student=student, quiz_id__in=quiz_ids).count()

    completed_items = completed_materials + completed_quizzes
    percentage = round((completed_items / total_items) * 100, 1) if total_items else 0.0
    return {
        "total_items": total_items,
        "completed_items": completed_items,
        "completed_materials": completed_materials,
        "total_materials": len(material_ids),
        "completed_quizzes": completed_quizzes,
        "total_quizzes": len(quiz_ids),
        "percentage": percentage,
    }


def attach_progress_to_enrollments(enrollments):
    enrollments = list(enrollments)
    if not enrollments:
        return enrollments

    course_ids = [e.course_id for e in enrollments]
    student_ids = {e.student_id for e in enrollments}

    material_counts = {
        row["course_id"]: row["count"]
        for row in LearningMaterial.objects.filter(course_id__in=course_ids)
        .values("course_id")
        .annotate(count=Count("id"))
    }
    quiz_counts = {
        row["course_id"]: row["count"]
        for row in Quiz.objects.filter(course_id__in=course_ids, is_published=True)
        .values("course_id")
        .annotate(count=Count("id"))
    }

    material_completions = {}
    for row in (
        MaterialCompletion.objects.filter(student_id__in=student_ids, material__course_id__in=course_ids)
        .values("student_id", "material__course_id")
        .annotate(count=Count("id"))
    ):
        material_completions[(row["student_id"], row["material__course_id"])] = row["count"]

    quiz_attempts = {}
    for row in (
        QuizAttempt.objects.filter(student_id__in=student_ids, quiz__course_id__in=course_ids, quiz__is_published=True)
        .values("student_id", "quiz__course_id")
        .annotate(count=Count("id"))
    ):
        quiz_attempts[(row["student_id"], row["quiz__course_id"])] = row["count"]

    for enrollment in enrollments:
        total_materials = material_counts.get(enrollment.course_id, 0)
        total_quizzes = quiz_counts.get(enrollment.course_id, 0)
        completed_materials = material_completions.get((enrollment.student_id, enrollment.course_id), 0)
        completed_quizzes = quiz_attempts.get((enrollment.student_id, enrollment.course_id), 0)
        total_items = total_materials + total_quizzes
        completed_items = completed_materials + completed_quizzes
        percentage = round((completed_items / total_items) * 100, 1) if total_items else 0.0
        enrollment.progress = {
            "total_items": total_items,
            "completed_items": completed_items,
            "completed_materials": completed_materials,
            "total_materials": total_materials,
            "completed_quizzes": completed_quizzes,
            "total_quizzes": total_quizzes,
            "percentage": percentage,
        }
    return enrollments


def sync_enrollment_status(enrollment):
    progress = get_course_progress(enrollment.student, enrollment.course)
    if progress["total_items"] > 0 and progress["completed_items"] >= progress["total_items"]:
        new_status = Enrollment.Status.COMPLETED
    elif enrollment.status == Enrollment.Status.COMPLETED:
        new_status = Enrollment.Status.ACTIVE
    else:
        new_status = enrollment.status
    if new_status != enrollment.status:
        enrollment.status = new_status
        enrollment.save(update_fields=["status", "updated_at"])
    enrollment.progress = progress
    return progress
