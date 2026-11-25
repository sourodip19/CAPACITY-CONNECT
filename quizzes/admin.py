from django.contrib import admin

from .models import AnswerOption, Question, Quiz, QuizAttempt, StudentAnswer


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "created_by", "is_published", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title", "course__title")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order", "text")
    inlines = [AnswerOptionInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("quiz", "student", "score", "total_questions", "percentage", "submitted_at")
    search_fields = ("quiz__title", "student__username")


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "selected_option")
