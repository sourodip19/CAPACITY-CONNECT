from django.http import HttpResponse


def home(request):
    return HttpResponse("Capacity Connect - setup in progress")
