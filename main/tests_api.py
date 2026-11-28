import uuid
from datetime import date
from pathlib import Path

from django.contrib.auth.models import Group, Permission, User
from django.contrib.staticfiles import finders
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from main.models import Education, Experience
from main.permissions import IsPortfolioOwnerOrEditorOrReadOnly


def make_editor(user):
    group, _ = Group.objects.get_or_create(name="Editor")
    group.permissions.add(Permission.objects.get(codename="change_education"))
    user.groups.add(group)


class EducationAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.regular = User.objects.create_user(username="regular", password="test-password")
        self.editor = User.objects.create_user(username="editor", password="test-password")
        make_editor(self.editor)

        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            degree="S1 Ilmu Komputer KKI",
            description="Studying computer science.",
            started_at=date(2025, 8, 1),
        )
        self.list_url = reverse("api:education-list")
        self.detail_url = reverse("api:education-detail", args=[self.education.id])
        self.star_url = reverse("api:education-star", args=[self.education.id])
        self.payload = {
            "institution": "The University of Queensland",
            "degree": "Bachelor of Computer Science",
            "description": "Continuing under the 2.5+1.5 scheme.",
            "started_at": "2027-07-01",
            "ended_at": None,
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.education.id))
        self.assertFalse(response.data[0]["is_starred"])
        self.assertTrue(response.data[0]["is_ongoing"])
        self.assertNotIn("fields", response.data[0])
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    def test_search_and_empty_results(self):
        response = self.client.get(self.list_url, {"institution": "UNIVERSITAS"})
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.list_url, {"institution": "not-found"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_missing_education_returns_404(self):
        url = reverse("api:education-detail", args=[uuid.uuid4()])

        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_visitor_and_regular_user_cannot_write(self):
        for user, expected in ((None, 401), (self.regular, 403)):
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                self.assertEqual(
                    self.client.post(self.list_url, self.payload, format="json").status_code, expected,
                )
                self.assertEqual(
                    self.client.patch(self.detail_url, {"institution": "Changed"}, format="json").status_code,
                    expected,
                )
                self.assertEqual(self.client.delete(self.detail_url).status_code, expected)

        self.assertEqual(Education.objects.count(), 1)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Universitas Indonesia")

    def test_editor_can_update_but_not_create_or_delete(self):
        self.client.force_authenticate(user=self.editor)

        response = self.client.patch(self.detail_url, {"degree": "S1 Ilmu Komputer"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.put(self.detail_url, self.payload, format="json").status_code, 200,
        )
        self.assertEqual(
            self.client.post(self.list_url, self.payload, format="json").status_code, 403,
        )
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)

        self.assertEqual(Education.objects.count(), 1)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "The University of Queensland")

    def test_staff_flag_alone_grants_no_write_access(self):
        self.regular.is_staff = True
        self.regular.save()
        self.client.force_authenticate(user=self.regular)

        response = self.client.patch(self.detail_url, {"institution": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_create(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Education.objects.filter(pk=response.data["id"]).exists())
        self.assertTrue(response.data["is_ongoing"])

    def test_validation_rejects_bad_input(self):
        self.client.force_authenticate(user=self.owner)
        cases = [
            ({"institution": "   "}, "institution"),
            ({"institution": '<img src="x" onerror="alert(1)">'}, "institution"),
            ({"degree": "<b></b>"}, "degree"),
            ({"started_at": "not-a-date"}, "started_at"),
        ]
        for changes, field in cases:
            with self.subTest(field=field, changes=changes):
                response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

        self.assertEqual(Education.objects.count(), 1)

    def test_html_is_stripped_before_saving(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload,
            "institution": "<script>alert('XSS!')</script>The University of Queensland",
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        saved = Education.objects.get(pk=response.data["id"])
        self.assertNotIn("<script>", saved.institution)
        self.assertIn("The University of Queensland", saved.institution)

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(self.detail_url, {"institution": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.education.refresh_from_db()
        self.assertEqual(self.education.description, "Studying computer science.")

        response = self.client.put(self.detail_url, {"institution": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Education.objects.filter(pk=self.education.id).exists())

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.regular)
        response = self.client.post(self.star_url)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)

        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)

    def test_star_status_is_per_user(self):
        self.education.starred_by.add(self.regular)
        self.client.force_authenticate(user=self.editor)

        response = self.client.get(self.detail_url)
        self.assertEqual(response.data["star_count"], 1)
        self.assertFalse(response.data["is_starred"])

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        forged_id = str(uuid.uuid4())
        response = self.client.post(self.list_url, {
            **self.payload,
            "id": forged_id,
            "star_count": 99,
            "is_starred": True,
            "is_ongoing": False,
            "starred_by": [self.regular.id],
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["id"], forged_id)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertTrue(response.data["is_ongoing"])
        self.assertEqual(Education.objects.get(pk=response.data["id"]).starred_by.count(), 0)

    def test_api_does_not_expose_account_data(self):
        self.education.starred_by.add(self.regular)
        response = self.client.get(self.detail_url)

        self.assertNotIn("starred_by", response.data)
        self.assertNotIn("starred_by_names", response.data)
        self.assertNotIn("regular", response.content.decode())
        self.assertEqual(response.data["star_count"], 1)

    def test_wrong_method_returns_405(self):
        self.client.force_authenticate(user=self.owner)

        self.assertEqual(self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.get(self.star_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_list_query_count_does_not_grow_with_rows(self):
        self.client.force_authenticate(user=self.regular)
        with CaptureQueriesContext(connection) as one_row:
            self.client.get(self.list_url)

        for index in range(5):
            education = Education.objects.create(
                institution=f"Institution {index}",
                degree="Degree",
                description="Description",
                started_at=date(2020 + index, 1, 1),
            )
            education.starred_by.add(self.regular, self.owner)

        with CaptureQueriesContext(connection) as six_rows:
            response = self.client.get(self.list_url)

        self.assertEqual(len(response.data), 6)
        self.assertEqual(len(six_rows.captured_queries), len(one_row.captured_queries))

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))

        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Education.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="owner", password="test-password")
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)

        token = client.cookies["csrftoken"].value
        response = client.post(self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class EducationPageUsesApiTest(APITestCase):
    def setUp(self):
        self.regular = User.objects.create_user(username="regular", password="test-password")
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            degree="S1 Ilmu Komputer KKI",
            description="Studying computer science.",
            started_at=date(2025, 8, 1),
        )
        self.page_url = reverse("main:show_education")

    def test_page_script_targets_the_v1_api(self):
        response = self.client.get(self.page_url)

        self.assertEqual(response.context["page_config"]["listUrl"], reverse("api:education-list"))
        self.assertContains(response, 'id="education-page-config"')
        self.assertNotContains(response, reverse("main:get_educations_json"))

    def test_config_urls_point_at_real_entries_once_the_id_is_filled_in(self):
        config = self.client.get(self.page_url).context["page_config"]
        real_id = str(self.education.id)

        detail_url = config["detailUrl"].replace(config["placeholderId"], real_id)
        star_url = config["starUrl"].replace(config["placeholderId"], real_id)
        self.assertEqual(detail_url, reverse("api:education-detail", args=[self.education.id]))
        self.assertEqual(star_url, reverse("api:education-star", args=[self.education.id]))
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_200_OK)

    def test_shared_helpers_and_config_load_before_the_page_script(self):
        html = self.client.get(self.page_url).content.decode()

        helpers = html.index("js/ajax-utils.js")
        config = html.index('id="education-page-config"')
        page_script = html.index("js/education.js")
        self.assertLess(helpers, page_script)
        self.assertLess(config, page_script)

    def test_page_and_page_script_have_no_inline_event_handlers(self):
        response = self.client.get(self.page_url)
        script = Path(finders.find("js/education.js")).read_text(encoding="utf-8")

        self.assertNotContains(response, "onclick=")
        self.assertNotIn("onclick", script)

    def test_page_gives_regular_users_a_csrf_cookie_that_the_api_accepts(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="regular", password="test-password")
        client.get(self.page_url)
        token = client.cookies["csrftoken"].value

        response = client.post(
            reverse("api:education-star", args=[self.education.id]),
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])


class EducationEditFlowTest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.editor = User.objects.create_user(username="editor", password="test-password")
        self.regular = User.objects.create_user(username="regular", password="test-password")
        make_editor(self.editor)

        self.ongoing = Education.objects.create(
            institution="Universitas Indonesia",
            degree="S1 Ilmu Komputer KKI",
            description="Studying computer science.",
            started_at=date(2025, 8, 1),
        )
        self.finished = Education.objects.create(
            institution="SMA Labschool Rawamangun",
            degree="MIPA",
            description="Completed secondary education.",
            started_at=date(2020, 7, 1),
            ended_at=date(2023, 6, 1),
        )
        self.ongoing_url = reverse("api:education-detail", args=[self.ongoing.id])
        self.finished_url = reverse("api:education-detail", args=[self.finished.id])
        self.page_url = reverse("main:show_education")

    def session_client(self, username):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username=username, password="test-password"))
        client.get(self.page_url)
        return client, client.cookies["csrftoken"].value

    def test_editor_can_patch_through_a_real_session_with_the_csrf_token(self):
        client, token = self.session_client("editor")
        response = client.patch(
            self.ongoing_url, {"degree": "S1 Ilmu Komputer"}, format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ongoing.refresh_from_db()
        self.assertEqual(self.ongoing.degree, "S1 Ilmu Komputer")
        self.assertEqual(self.ongoing.institution, "Universitas Indonesia")

    def test_editor_patch_without_the_csrf_token_is_rejected(self):
        client, _ = self.session_client("editor")
        response = client.patch(self.ongoing_url, {"degree": "Changed"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.ongoing.refresh_from_db()
        self.assertEqual(self.ongoing.degree, "S1 Ilmu Komputer KKI")

    def test_valid_csrf_token_does_not_give_a_regular_user_edit_rights(self):
        client, token = self.session_client("regular")
        response = client.patch(
            self.ongoing_url, {"degree": "Changed"}, format="json", HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], IsPortfolioOwnerOrEditorOrReadOnly.message)
        self.ongoing.refresh_from_db()
        self.assertEqual(self.ongoing.degree, "S1 Ilmu Komputer KKI")

    def test_patch_response_is_ready_to_render_as_a_card(self):
        self.ongoing.starred_by.add(self.editor)
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.ongoing_url, {"description": "Updated."}, format="json")

        self.assertEqual(response.data["description"], "Updated.")
        self.assertEqual(response.data["star_count"], 1)
        self.assertTrue(response.data["is_starred"])
        self.assertTrue(response.data["is_ongoing"])

    def test_end_date_before_the_stored_start_date_is_rejected(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.ongoing_url, {"ended_at": "2024-12-31"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ended_at", response.data)
        self.ongoing.refresh_from_db()
        self.assertIsNone(self.ongoing.ended_at)

    def test_start_date_after_the_stored_end_date_is_rejected(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.finished_url, {"started_at": "2024-01-01"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ended_at", response.data)
        self.finished.refresh_from_db()
        self.assertEqual(self.finished.started_at, date(2020, 7, 1))

    def test_put_and_post_reject_an_end_date_before_the_start_date(self):
        self.client.force_authenticate(user=self.owner)
        payload = {
            "institution": "The University of Queensland",
            "degree": "Bachelor of Computer Science",
            "description": "Partner university.",
            "started_at": "2028-02-13",
            "ended_at": "2027-06-15",
        }

        self.assertEqual(
            self.client.put(self.ongoing_url, payload, format="json").status_code, 400,
        )
        self.assertEqual(
            self.client.post(reverse("api:education-list"), payload, format="json").status_code,
            400,
        )
        self.assertEqual(Education.objects.count(), 2)

    def test_patch_without_dates_skips_the_period_check_for_older_rows(self):
        legacy = Education.objects.create(
            institution="Legacy",
            degree="Saved before date checks existed",
            description="Old text.",
            started_at=date(2022, 1, 1),
            ended_at=date(2021, 1, 1),
        )
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(
            reverse("api:education-detail", args=[legacy.id]),
            {"description": "New text."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        legacy.refresh_from_db()
        self.assertEqual(legacy.description, "New text.")

    def test_patch_can_clear_the_end_date_to_mark_an_entry_ongoing(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.finished_url, {"ended_at": None}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_ongoing"])
        self.finished.refresh_from_db()
        self.assertIsNone(self.finished.ended_at)

    def test_html_only_description_is_rejected_on_create_and_edit(self):
        self.client.force_authenticate(user=self.owner)
        create = self.client.post(reverse("api:education-list"), {
            "institution": "The University of Queensland",
            "degree": "Bachelor of Computer Science",
            "description": "<p></p>",
            "started_at": "2028-02-13",
        }, format="json")
        edit = self.client.patch(self.ongoing_url, {"description": "<b></b>"}, format="json")

        self.assertEqual(create.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", create.data)
        self.assertEqual(edit.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Education.objects.count(), 2)
        self.ongoing.refresh_from_db()
        self.assertEqual(self.ongoing.description, "Studying computer science.")

    def test_missing_entry_is_404_for_permitted_roles_and_refused_for_others(self):
        missing = uuid.uuid4()
        detail = reverse("api:education-detail", args=[missing])
        star = reverse("api:education-star", args=[missing])

        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.patch(detail, {"degree": "x"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(detail).status_code, 404)
        self.assertEqual(self.client.post(star).status_code, 404)

        self.client.force_authenticate(user=self.editor)
        self.assertEqual(self.client.patch(detail, {"degree": "x"}, format="json").status_code, 404)

        self.client.force_authenticate(user=self.regular)
        self.assertEqual(self.client.patch(detail, {"degree": "x"}, format="json").status_code, 403)

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(star).status_code, 401)


class TokenAuthAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.regular = User.objects.create_user(username="regular", password="test-password")
        self.token_url = reverse("api:auth-token")
        self.logout_url = reverse("api:auth-logout")
        self.list_url = reverse("api:education-list")
        self.payload = {
            "institution": "The University of Queensland",
            "degree": "Bachelor of Computer Science",
            "description": "Continuing under the 2.5+1.5 scheme.",
            "started_at": "2027-07-01",
            "ended_at": None,
        }

    def obtain_token(self, username):
        response = self.client.post(
            self.token_url, {"username": username, "password": "test-password"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data["token"]

    def test_token_login_returns_the_users_token(self):
        token = self.obtain_token("owner")

        self.assertEqual(token, Token.objects.get(user=self.owner).key)

    def test_token_login_rejects_a_wrong_password(self):
        response = self.client.post(
            self.token_url, {"username": "owner", "password": "wrong-password"}, format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Token.objects.exists())

    def test_owner_can_create_with_a_token_and_no_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        client.credentials(HTTP_AUTHORIZATION=f"Token {self.obtain_token('owner')}")

        response = client.post(self.list_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Education.objects.get().degree, "Bachelor of Computer Science")

    def test_regular_users_token_still_cannot_create(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.obtain_token('regular')}")

        response = self.client.post(self.list_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Education.objects.exists())

    def test_missing_or_invalid_token_gets_401_with_a_token_challenge(self):
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["WWW-Authenticate"], "Token")

        self.client.credentials(HTTP_AUTHORIZATION="Token not-a-real-token")
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Education.objects.exists())

    def test_logout_deletes_the_token(self):
        token = self.obtain_token("owner")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=token).exists())

        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_a_token(self):
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cors_allows_any_origin_outside_production(self):
        response = self.client.get(self.list_url, HTTP_ORIGIN="http://localhost:5000")

        self.assertEqual(response["Access-Control-Allow-Origin"], "*")

    def test_cors_preflight_allows_the_authorization_header(self):
        response = self.client.options(
            self.list_url,
            HTTP_ORIGIN="http://localhost:5000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization, content-type",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("authorization", response["Access-Control-Allow-Headers"])

    def test_android_emulator_host_is_allowed_outside_production(self):
        response = self.client.get(self.list_url, HTTP_HOST="10.0.2.2:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ExperienceAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.regular = User.objects.create_user(username="regular", password="test-password")
        self.editor = User.objects.create_user(username="editor", password="test-password")
        make_editor(self.editor)

        self.experience = Experience.objects.create(
            title="PBP Teaching Assistant",
            description="Help students understand web development.",
            category="part-time",
        )
        self.list_url = reverse("api:experience-list")
        self.detail_url = reverse("api:experience-detail", args=[self.experience.id])
        self.payload = {
            "title": "Software Engineering Intern",
            "category": "internship",
            "description": "Built internal tools.",
            "thumbnail": "https://example.com/intern.png",
            "ended_at": "2025-06-30T00:00:00",
        }

    def use_token(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_public_list_and_detail(self):
        newer = Experience.objects.create(title="Volunteer Tutor", description="Taught kids.")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [entry["id"] for entry in response.data],
            [str(newer.id), str(self.experience.id)],
        )
        self.assertEqual(
            set(response.data[1]),
            {
                "id",
                "title",
                "category",
                "description",
                "thumbnail",
                "started_at",
                "ended_at",
                "is_ongoing",
            },
        )
        self.assertEqual(response.data[1]["category"], "part-time")
        self.assertIsNone(response.data[1]["thumbnail"])
        self.assertTrue(response.data[1]["is_ongoing"])
        detail = self.client.get(self.detail_url)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["title"], "PBP Teaching Assistant")

    def test_missing_experience_returns_404(self):
        response = self.client.get(reverse("api:experience-detail", args=[uuid.uuid4()]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_visitor_regular_user_and_editor_cannot_create_or_delete(self):
        for user, expected in ((None, 401), (self.regular, 403), (self.editor, 403)):
            if user is None:
                self.client.credentials()
            else:
                self.use_token(user)

            created = self.client.post(self.list_url, self.payload, format="json")
            deleted = self.client.delete(self.detail_url)

            self.assertEqual(created.status_code, expected)
            self.assertEqual(deleted.status_code, expected)
        self.assertEqual(Experience.objects.count(), 1)

    def test_experience_permissions_are_separate_from_education_permissions(self):
        curator = User.objects.create_user(username="curator", password="test-password")
        curator.user_permissions.add(
            Permission.objects.get(codename="add_experience"),
            Permission.objects.get(codename="delete_experience"),
        )
        self.use_token(curator)

        created = self.client.post(self.list_url, self.payload, format="json")
        deleted = self.client.delete(self.detail_url)
        education = self.client.post(
            reverse("api:education-list"),
            {
                "institution": "Universitas Indonesia",
                "degree": "S1 Ilmu Komputer KKI",
                "description": "Studying computer science.",
                "started_at": "2025-08-01",
            },
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(education.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_create_with_a_token_and_no_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        token, _ = Token.objects.get_or_create(user=self.owner)
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = client.post(self.list_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["category"], "internship")
        self.assertEqual(response.data["thumbnail"], "https://example.com/intern.png")
        self.assertEqual(response.data["ended_at"], "2025-06-30T00:00:00Z")
        self.assertFalse(response.data["is_ongoing"])
        self.assertTrue(Experience.objects.filter(title="Software Engineering Intern").exists())

    def test_created_experience_shows_on_the_experience_page(self):
        self.use_token(self.owner)
        self.client.post(self.list_url, self.payload, format="json")
        self.client.credentials()

        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Software Engineering Intern")

    def test_optional_fields_can_be_left_out(self):
        self.use_token(self.owner)

        response = self.client.post(
            self.list_url,
            {"title": "Volunteer Tutor", "description": "Taught kids.", "thumbnail": None},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["category"], "full-time")
        self.assertIsNone(response.data["thumbnail"])
        self.assertIsNone(response.data["ended_at"])
        self.assertTrue(response.data["is_ongoing"])

    def test_server_fields_are_read_only(self):
        self.use_token(self.owner)
        payload = {
            **self.payload,
            "id": str(uuid.uuid4()),
            "started_at": "2000-01-01T00:00:00Z",
            "is_ongoing": True,
        }

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["id"], payload["id"])
        self.assertFalse(response.data["started_at"].startswith("2000"))
        self.assertFalse(response.data["is_ongoing"])

    def test_validation_rejects_bad_input(self):
        self.use_token(self.owner)

        response = self.client.post(
            self.list_url,
            {
                "title": "   ",
                "category": "partTime",
                "description": "<b></b>",
                "thumbnail": "not a link",
                "ended_at": "yesterday",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            set(response.data),
            {"title", "category", "description", "thumbnail", "ended_at"},
        )
        self.assertEqual(response.data["category"], ['"partTime" is not a valid choice.'])
        self.assertEqual(Experience.objects.count(), 1)

    def test_html_is_stripped_before_saving(self):
        self.use_token(self.owner)

        response = self.client.post(
            self.list_url,
            {**self.payload, "title": "<i>Volunteer</i>", "description": "Taught <b>kids</b>."},
            format="json",
        )

        self.assertEqual(response.data["title"], "Volunteer")
        self.assertEqual(response.data["description"], "Taught kids.")

    def test_owner_can_delete(self):
        self.use_token(self.owner)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Experience.objects.exists())
        self.assertEqual(self.client.delete(self.detail_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_editing_is_not_supported(self):
        self.use_token(self.owner)

        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
