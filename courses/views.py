from django.http import HttpResponse


def course_list(request):
    return HttpResponse("courses")


def course_detail(request, pk):
    return HttpResponse(f"course {pk}")
