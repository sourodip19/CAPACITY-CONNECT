from django.shortcuts import render

from courses.models import Course


def home(request):
    featured_courses = Course.objects.filter(status=Course.Status.PUBLISHED).select_related("trainer")[:6]
    return render(request, "core/home.html", {"featured_courses": featured_courses})
