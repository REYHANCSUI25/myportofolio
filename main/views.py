from django.shortcuts import render

from main.models import Experience, Education
# Create your views here.

def show_main(request):
    context = {
        "name": "Muhammad Reyhan Attarizky",
        "npm": "2506637086",
        "study_program": "S1 Ilmu Komputer KKI",
        "bio": "Sophomore CS student barely surviving at Universitas Indonesia with delusions of working in artificial intelligence someday.",
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Muhammad Reyhan Attarizky",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

def show_education(request):
    context = {
        "name": "Muhammad Reyhan Attarizky",
        "education_list": Education.objects.all().order_by("-started_at"),
    }
    return render(request, "education.html", context)
