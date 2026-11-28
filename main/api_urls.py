from django.urls import path
from rest_framework.authtoken import views as authtoken_views

from main import api_views

app_name = "api"

urlpatterns = [
    path("auth/token/", authtoken_views.obtain_auth_token, name="auth-token"),
    path("auth/logout/", api_views.api_logout, name="auth-logout"),
    path("education/", api_views.education_list, name="education-list"),
    path(
        "education/<uuid:education_id>/",
        api_views.education_detail,
        name="education-detail",
    ),
    path(
        "education/<uuid:education_id>/star/",
        api_views.education_star,
        name="education-star",
    ),
    path("experience/", api_views.experience_list, name="experience-list"),
    path(
        "experience/<uuid:experience_id>/",
        api_views.experience_detail,
        name="experience-detail",
    ),
]
