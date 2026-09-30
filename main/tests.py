import json

from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import date

from main.models import Experience, Education
# Create your tests here.

class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="PBP Teaching Assistant",
            description="Help students understand web development.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/a-page-that-does-not-exist/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "PBP Teaching Assistant")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Ongoing")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "No experience has been added yet.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Completed")
        self.assertNotContains(response, "Ongoing")

class EducationTest(TestCase):
    def setUp(self):
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            degree="S1 Ilmu Komputer KKI",
            description="Studying computer science as part of the KKI double-degree program.",
            started_at=date(2025, 8, 1),
        )

    def test_education_url_is_accessible(self):
        response = self.client.get(reverse("main:show_education"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education.html")

    def test_education_data_appears_in_json_when_not_empty(self):
        response = self.client.get(reverse("main:get_educations_json"))
        data = json.loads(response.content)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["fields"]["institution"], self.education.institution)
        self.assertEqual(data[0]["fields"]["degree"], self.education.degree)

    def test_empty_education_json(self):
        Education.objects.all().delete()
        response = self.client.get(reverse("main:get_educations_json"))

        self.assertEqual(json.loads(response.content), [])

    def test_education_page_ships_the_ajax_skeleton(self):
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, 'id="grid"')
        self.assertContains(response, 'id="loading"')
        self.assertContains(response, 'id="empty"')
        self.assertNotContains(response, self.education.degree)


class RoleBasedAccessTest(TestCase):
    def setUp(self):
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            degree="S1 Ilmu Komputer KKI",
            description="Studying computer science.",
            started_at=date(2025, 8, 1),
        )
        self.owner = User.objects.create_superuser("owner", password="pass12345")
        self.regular = User.objects.create_user("regular", password="pass12345")
        self.editor = User.objects.create_user("editor", password="pass12345")

        editor_group = Group.objects.create(name="Editor")
        editor_group.permissions.add(Permission.objects.get(codename="change_education"))
        self.editor.groups.add(editor_group)

        self.create_url = reverse("main:create_education")
        self.update_url = reverse("main:update_education", args=[self.education.id])
        self.delete_url = reverse("main:delete_education", args=[self.education.id])
        self.star_url = reverse("main:toggle_star", args=[self.education.id])
        self.form_data = {
            "institution": "ANU",
            "degree": "Bachelor of Computing",
            "description": "Partner university.",
            "started_at": "2027-07-01",
        }

    def login_as(self, user):
        self.client.force_login(user)

    def assert_redirects_to_login(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_visitor_can_read_education_page_and_json(self):
        self.assertEqual(self.client.get(reverse("main:show_education")).status_code, 200)
        self.assertEqual(self.client.get(reverse("main:get_educations_json")).status_code, 200)

    def test_visitor_is_redirected_to_login_for_protected_views(self):
        self.assert_redirects_to_login(self.client.get(self.create_url))
        self.assert_redirects_to_login(self.client.get(self.update_url))
        self.assert_redirects_to_login(self.client.post(self.delete_url))
        self.assert_redirects_to_login(self.client.post(self.star_url))

    def test_regular_user_gets_403_on_create_update_delete(self):
        self.login_as(self.regular)

        self.assertEqual(self.client.get(self.create_url).status_code, 403)
        self.assertEqual(self.client.post(self.create_url, self.form_data).status_code, 403)
        self.assertEqual(self.client.get(self.update_url).status_code, 403)
        self.assertEqual(self.client.post(self.update_url, self.form_data).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertEqual(Education.objects.count(), 1)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Universitas Indonesia")

    def test_editor_can_update_but_not_create_or_delete(self):
        self.login_as(self.editor)

        self.assertEqual(self.client.get(self.update_url).status_code, 200)
        response = self.client.post(self.update_url, self.form_data)
        self.assertRedirects(response, reverse("main:show_education"))
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "ANU")

        self.assertEqual(self.client.get(self.create_url).status_code, 403)
        self.assertEqual(self.client.post(self.create_url, self.form_data).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertEqual(Education.objects.count(), 1)

    def test_owner_can_create_update_and_delete(self):
        self.login_as(self.owner)

        self.assertRedirects(
            self.client.post(self.create_url, self.form_data),
            reverse("main:show_education"),
        )
        self.assertEqual(Education.objects.count(), 2)

        self.assertRedirects(
            self.client.post(self.update_url, {**self.form_data, "institution": "UQ"}),
            reverse("main:show_education"),
        )
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "UQ")

        self.assertRedirects(
            self.client.post(self.delete_url),
            reverse("main:show_education"),
        )
        self.assertEqual(Education.objects.count(), 1)

    def test_delete_rejects_get_requests(self):
        self.login_as(self.owner)

        self.assertEqual(self.client.get(self.delete_url).status_code, 405)
        self.assertEqual(Education.objects.count(), 1)

    def test_forbidden_response_uses_custom_403_template(self):
        self.login_as(self.regular)
        response = self.client.get(self.create_url)

        self.assertTemplateUsed(response, "403.html")

    def test_visitor_gets_no_add_modal_and_false_js_permission_flags(self):
        response = self.client.get(reverse("main:show_education"))

        self.assertNotContains(response, 'id="add-education-modal"')
        self.assertContains(response, 'const IS_AUTHENTICATED = "false" === "true";')
        self.assertContains(response, 'const CAN_EDIT = "false" === "true";')
        self.assertContains(response, 'const CAN_DELETE = "false" === "true";')

    def test_regular_user_is_authenticated_with_no_edit_or_delete_flags(self):
        self.login_as(self.regular)
        response = self.client.get(reverse("main:show_education"))

        self.assertNotContains(response, 'id="add-education-modal"')
        self.assertContains(response, 'const IS_AUTHENTICATED = "true" === "true";')
        self.assertContains(response, 'const CAN_EDIT = "false" === "true";')
        self.assertContains(response, 'const CAN_DELETE = "false" === "true";')

    def test_editor_gets_edit_flag_but_no_add_modal(self):
        self.login_as(self.editor)
        response = self.client.get(reverse("main:show_education"))

        self.assertNotContains(response, 'id="add-education-modal"')
        self.assertContains(response, 'const CAN_EDIT = "true" === "true";')
        self.assertContains(response, 'const CAN_DELETE = "false" === "true";')
        self.assertContains(response, "Editor")

    def test_owner_gets_add_modal_and_full_flags(self):
        self.login_as(self.owner)
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, 'id="add-education-modal"')
        self.assertContains(response, 'const CAN_EDIT = "true" === "true";')
        self.assertContains(response, 'const CAN_DELETE = "true" === "true";')
        self.assertContains(response, "Owner")


class ToggleStarTest(TestCase):
    def setUp(self):
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            degree="S1 Ilmu Komputer KKI",
            description="Studying computer science.",
            started_at=date(2025, 8, 1),
        )
        self.first = User.objects.create_user("first", password="pass12345")
        self.second = User.objects.create_user("second", password="pass12345")
        self.star_url = reverse("main:toggle_star", args=[self.education.id])

    def test_toggle_star_rejects_get_requests(self):
        self.client.force_login(self.first)

        self.assertEqual(self.client.get(self.star_url).status_code, 405)
        self.assertEqual(self.education.starred_by.count(), 0)

    def test_toggle_star_adds_then_removes_star(self):
        self.client.force_login(self.first)

        self.client.post(self.star_url)
        self.assertEqual(self.education.starred_by.count(), 1)

        self.client.post(self.star_url)
        self.assertEqual(self.education.starred_by.count(), 0)

    def test_star_count_is_shared_across_users_but_status_is_per_user(self):
        self.client.force_login(self.first)
        self.client.post(self.star_url)
        self.client.force_login(self.second)
        self.client.post(self.star_url)

        self.assertEqual(self.education.starred_by.count(), 2)
        fields = json.loads(self.client.get(reverse("main:get_educations_json")).content)[0]["fields"]
        self.assertEqual(fields["star_count"], 2)
        self.assertTrue(fields["is_starred"])

    def test_star_status_differs_per_requesting_user(self):
        self.client.force_login(self.first)
        self.client.post(self.star_url)
        fields = json.loads(self.client.get(reverse("main:get_educations_json")).content)[0]["fields"]
        self.assertEqual(fields["star_count"], 1)
        self.assertTrue(fields["is_starred"])

        self.client.force_login(self.second)
        fields = json.loads(self.client.get(reverse("main:get_educations_json")).content)[0]["fields"]
        self.assertEqual(fields["star_count"], 1)
        self.assertFalse(fields["is_starred"])

        self.client.logout()
        fields = json.loads(self.client.get(reverse("main:get_educations_json")).content)[0]["fields"]
        self.assertEqual(fields["star_count"], 1)
        self.assertFalse(fields["is_starred"])

    def test_toggle_star_on_missing_education_returns_404(self):
        self.client.force_login(self.first)
        missing = reverse("main:toggle_star", args=["00000000-0000-0000-0000-000000000000"])

        self.assertEqual(self.client.post(missing).status_code, 404)


class JsonEndpointSecurityTest(TestCase):
    def setUp(self):
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            degree="S1 Ilmu Komputer KKI",
            description="Studying computer science.",
            started_at=date(2025, 8, 1),
        )
        self.user = User.objects.create_user("starrer", password="pass12345")
        self.education.starred_by.add(self.user)

    def test_education_json_still_works_for_visitors(self):
        response = self.client.get(reverse("main:get_educations_json"))
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["fields"]["institution"], "Universitas Indonesia")

    def test_education_json_does_not_leak_starring_users(self):
        response = self.client.get(reverse("main:get_educations_json"))
        fields = json.loads(response.content)[0]["fields"]

        self.assertNotIn("starred_by", fields)
        self.assertNotIn("starred_by_names", fields)
        self.assertNotIn("starred_by", response.content.decode())
        self.assertNotIn("starrer", response.content.decode())

    def test_education_json_includes_star_state_for_requesting_user(self):
        self.client.force_login(self.user)
        fields = json.loads(self.client.get(reverse("main:get_educations_json")).content)[0]["fields"]

        self.assertEqual(fields["star_count"], 1)
        self.assertTrue(fields["is_starred"])

    def test_education_json_includes_year_and_ongoing_fields(self):
        response = self.client.get(reverse("main:get_educations_json"))
        fields = json.loads(response.content)[0]["fields"]

        self.assertEqual(fields["started_year"], 2025)
        self.assertIsNone(fields["ended_year"])
        self.assertTrue(fields["is_ongoing"])

    def test_institution_search_still_filters_json(self):
        response = self.client.get(reverse("main:get_educations_json"), {"institution": "nothing"})

        self.assertEqual(json.loads(response.content), [])


class CreateEducationAjaxTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser("owner", password="pass12345")
        self.regular = User.objects.create_user("regular", password="pass12345")
        self.editor = User.objects.create_user("editor", password="pass12345")

        editor_group = Group.objects.create(name="Editor")
        editor_group.permissions.add(Permission.objects.get(codename="change_education"))
        self.editor.groups.add(editor_group)

        self.url = reverse("main:create_education_ajax")
        self.form_data = {
            "institution": "Australian National University",
            "degree": "Bachelor of Computing",
            "description": "Continuing under the 2+2 scheme.",
            "started_at": "2027-07-01",
        }

    def test_get_is_rejected_with_405(self):
        self.client.force_login(self.owner)

        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_anonymous_visitor_gets_json_403(self):
        response = self.client.post(self.url, self.form_data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(Education.objects.count(), 0)

    def test_regular_user_gets_json_403(self):
        self.client.force_login(self.regular)
        response = self.client.post(self.url, self.form_data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Education.objects.count(), 0)

    def test_editor_gets_json_403(self):
        self.client.force_login(self.editor)
        response = self.client.post(self.url, self.form_data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Education.objects.count(), 0)

    def test_owner_can_create_and_receives_the_new_pk(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url, self.form_data)
        body = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Education.objects.count(), 1)
        self.assertEqual(str(Education.objects.get().pk), body["pk"])

    def test_invalid_data_returns_400_with_field_errors(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url, {**self.form_data, "institution": ""})
        body = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertIn("institution", body["errors"])
        self.assertEqual(Education.objects.count(), 0)

    def test_html_only_title_is_rejected_as_empty(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url, {**self.form_data, "institution": "<b></b>"})
        body = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertIn("institution", body["errors"])
        self.assertEqual(Education.objects.count(), 0)

    def test_script_tag_is_stripped_from_saved_institution(self):
        self.client.force_login(self.owner)
        self.client.post(self.url, {
            **self.form_data,
            "institution": "<script>alert('XSS!')</script>Universitas Indonesia",
        })

        saved = Education.objects.get()
        self.assertNotIn("<script>", saved.institution)
        self.assertIn("Universitas Indonesia", saved.institution)


class LoginRedirectTest(TestCase):
    def setUp(self):
        User.objects.create_user("someone", password="pass12345")

    def test_login_redirects_back_to_next_url(self):
        response = self.client.post(
            reverse("main:login"),
            {"username": "someone", "password": "pass12345", "next": "/education/"},
        )

        self.assertRedirects(response, "/education/", fetch_redirect_response=False)
        self.assertIn("last_login", response.cookies)

    def test_login_ignores_external_next_url(self):
        response = self.client.post(
            reverse("main:login"),
            {"username": "someone", "password": "pass12345", "next": "https://evil.example/"},
        )

        self.assertRedirects(response, reverse("main:show_main"), fetch_redirect_response=False)
