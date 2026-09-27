import datetime
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import PermissionDenied
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from main.forms import EducationForm
from main.models import Experience, Education
# Create your views here.

def show_main(request):
    last_login = request.COOKIES.get("last_login", "No active login session / Cookie not found")
    context = {
        "name": "Muhammad Reyhan Attarizky",
        "npm": "2506637086",
        "study_program": "S1 Ilmu Komputer KKI",
        "bio": "Sophomore CS student barely surviving at Universitas Indonesia with delusions of working in artificial intelligence someday.",
        "last_login": last_login,
    }
    return render(request, "index.html", context)

def show_experience(request):
    context = {
        "name": "Muhammad Reyhan Attarizky",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

def get_experiences_json(request):
    experiences = Experience.objects.all()
    experiences_json = serializers.serialize("json", experiences)
    return HttpResponse(experiences_json, content_type="application/json")

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


@login_required(login_url="/login/")
def toggle_star(request, education_id):
    education = get_object_or_404(Education, pk=education_id)

    if request.user in education.starred_by.all():
        education.starred_by.remove(request.user)
    else:
        education.starred_by.add(request.user)

    return redirect("main:show_education")

@login_required(login_url="/login/")
def create_education(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    form = EducationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "New education entry added successfully!")
        return redirect("main:show_education")

    context = {
        "name": "Muhammad Reyhan Attarizky",
        "form": form,
        "is_edit": False,
    }
    return render(request, "education_form.html", context)


@login_required(login_url="/login/")
def update_education(request, education_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    education = get_object_or_404(Education, pk=education_id)
    form = EducationForm(request.POST or None, instance=education)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Education entry updated successfully!")
        return redirect("main:show_education")

    context = {
        "name": "Muhammad Reyhan Attarizky",
        "form": form,
        "is_edit": True,
    }
    return render(request, "education_form.html", context)

@login_required(login_url="/login/")
def delete_education(request, education_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    education = get_object_or_404(Education, pk=education_id)

    if request.method == "POST":
        education.delete()
        messages.success(request, "Education entry deleted!")
        return redirect("main:show_education")

    return redirect("main:show_education")


def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created successfully. Please log in.")
        return redirect("main:login")

    context = {
        "name": "Muhammad Reyhan Attarizky",
        "form": form,
    }
    return render(request, "register.html", context)


def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("main:show_main")
        response.set_cookie("last_login", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return response

    context = {
        "name": "Muhammad Reyhan Attarizky",
        "form": form,
    }
    return render(request, "login.html", context)


def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie("last_login")
    return response
