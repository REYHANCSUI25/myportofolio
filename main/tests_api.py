import uuid
from datetime import date

from django.contrib.auth.models import Group, Permission, User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from main.models import Education


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
        for user in (None, self.regular):
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                self.assertEqual(
                    self.client.post(self.list_url, self.payload, format="json").status_code, 403,
                )
                self.assertEqual(
                    self.client.patch(self.detail_url, {"institution": "Changed"}, format="json").status_code,
                    403,
                )
                self.assertEqual(self.client.delete(self.detail_url).status_code, 403)

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
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)

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

        self.assertContains(response, reverse("api:education-list"))
        self.assertNotContains(response, reverse("main:get_educations_json"))

    def test_shared_helpers_load_before_the_page_script(self):
        html = self.client.get(self.page_url).content.decode()

        self.assertLess(html.index("js/ajax-utils.js"), html.index("const EDUCATION_LIST_ENDPOINT"))

    def test_page_script_has_no_inline_event_handlers(self):
        response = self.client.get(self.page_url)

        self.assertNotContains(response, "onclick=")

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
