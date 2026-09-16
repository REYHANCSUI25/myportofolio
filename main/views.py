from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from main.forms import EducationForm
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

def get_educations_json(request):
    institution_query = request.GET.get("institution", "").strip()
    educations = Education.objects.all().order_by("-started_at")

    if institution_query:
        educations = educations.filter(institution__icontains=institution_query)

    educations_json = serializers.serialize("json", educations)
    return HttpResponse(educations_json, content_type="application/json")


def show_education(request):
    json_response = get_educations_json(request)

    educations = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    educations = [education.object for education in educations]
    institution_query = request.GET.get("institution", "").strip()

    context = {
        "name": "Muhammad Reyhan Attarizky",
        "education_list": educations,
        "institution_query": institution_query,
    }
    return render(request, "education.html", context)

def create_education(request):
    form = EducationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "New education entry added successfully!")
        return redirect("main:show_education")

    context = {
        "name": "Muhammad Reyhan Attarizky",
        "form": form,
    }
    return render(request, "education_form.html", context)


def delete_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)

    if request.method == "POST":
        education.delete()
        messages.success(request, "Education entry deleted!")
        return redirect("main:show_education")

    return redirect("main:show_education")
