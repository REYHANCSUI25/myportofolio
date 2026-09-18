from django.urls import path

from main.views import (
    show_main,
    show_experience,
    show_education,
    create_education,
    update_education,
    delete_education,
    get_educations_json,
    get_experiences_json,
)

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("education/", show_education, name="show_education"),
    path("education/add/", create_education, name="create_education"),
    path("api/education/", get_educations_json, name="get_educations_json"),
    path("education/<uuid:education_id>/delete/", delete_education, name="delete_education"),
    path("education/<uuid:education_id>/edit/", update_education, name="update_education"),
    path("api/experience/", get_experiences_json, name="get_experiences_json"),
]
