import datetime
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from main.decorators import LOGIN_URL, permission_required_or_403
from main.forms import EducationForm
from main.models import Experience, Education

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

    star_counts = dict(
        Education.objects.annotate(total=Count("starred_by")).values_list("pk", "total")
    )
    starred_ids = set()
    if request.user.is_authenticated:
        starred_ids = set(request.user.starred_education.values_list("pk", flat=True))

    data = [
        {
            "pk": str(education.pk),
            "fields": {
                "institution": education.institution,
                "degree": education.degree,
                "description": education.description,
                "started_year": education.started_at.year,
                "ended_year": education.ended_at.year if education.ended_at else None,
                "is_ongoing": education.is_ongoing,
                "star_count": star_counts.get(education.pk, 0),
                "is_starred": education.pk in starred_ids,
            },
        }
        for education in educations
    ]
    return JsonResponse(data, safe=False)


def show_education(request):
    institution_query = request.GET.get("institution", "").strip()

    context = {
        "name": "Muhammad Reyhan Attarizky",
        "institution_query": institution_query,
        "form": EducationForm(),
    }
    return render(request, "education.html", context)


@login_required(login_url=LOGIN_URL)
@require_POST
def toggle_star(request, education_id):
    education = get_object_or_404(Education, pk=education_id)

    if education.starred_by.filter(pk=request.user.pk).exists():
        education.starred_by.remove(request.user)
    else:
        education.starred_by.add(request.user)

    return redirect("main:show_education")


@require_POST
def create_education_ajax(request):
    if not request.user.has_perm("main.add_education"):
        return JsonResponse(
            {"message": "Only the portfolio owner can add education entries."},
            status=403,
        )

    form = EducationForm(request.POST)
    if form.is_valid():
        education = form.save()
        return JsonResponse(
            {"message": "Education entry added successfully.", "pk": str(education.pk)},
            status=201,
        )
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)


@permission_required_or_403("main.add_education")
def create_education(request):
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


@permission_required_or_403("main.change_education")
def update_education(request, education_id):
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


@permission_required_or_403("main.delete_education")
@require_POST
def delete_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)
    education.delete()
    messages.success(request, "Education entry deleted!")
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


def get_safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    is_safe = url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )
    return next_url if is_safe else ""


def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)
    next_url = get_safe_next_url(request)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect(next_url or "main:show_main")
        response.set_cookie("last_login", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return response

    context = {
        "name": "Muhammad Reyhan Attarizky",
        "form": form,
        "next": next_url,
    }
    return render(request, "login.html", context)


def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie("last_login")
    return response
