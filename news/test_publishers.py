from django.contrib.staticfiles import finders
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from .models import Article, Publisher, User


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PublisherWorkflowTests(TestCase):
    def setUp(self):
        self.editor = User.objects.create_user(
            "lead", "lead@example.com", "StrongPass!883", role="editor"
        )
        self.other = User.objects.create_user(
            "other", "other@example.com", "StrongPass!883", role="editor"
        )
        self.writer = User.objects.create_user(
            "writer", "writer@example.com", "StrongPass!883", role="journalist"
        )
        self.reader = User.objects.create_user(
            "reader", "reader@example.com", "StrongPass!883"
        )
        self.company = Publisher.objects.create(
            name="Dispatch", description="Local news"
        )
        self.company.editors.add(self.editor)
        self.client.force_login(self.editor)

    def test_editor_creates_company_and_becomes_member(self):
        response = self.client.post(
            reverse("publisher_create"), {"name": "New Times", "description": "Science"}
        )
        company = Publisher.objects.get(name="New Times")
        self.assertRedirects(response, reverse("publisher", args=[company.pk]))
        self.assertTrue(company.editors.filter(pk=self.editor.pk).exists())

    def test_registration_roles_and_no_admin_escalation(self):
        for role in ["reader", "editor", "journalist"]:
            self.client.logout()
            response = self.client.post(
                reverse("register"),
                {
                    "username": "new_" + role,
                    "email": "new_" + role + "@example.com",
                    "role": role,
                    "password1": "UnusualSecret!883",
                    "password2": "UnusualSecret!883",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            self.assertEqual(response.status_code, 302)
            user = User.objects.get(username="new_" + role)
            self.assertEqual(user.role, role)
            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)
            self.assertTrue(user.groups.filter(name=role.title()).exists())

    def test_invalid_registration_role_rejected(self):
        self.client.post(
            reverse("register"),
            {
                "username": "invalid",
                "email": "invalid@example.com",
                "role": "admin",
                "password1": "UnusualSecret!883",
                "password2": "UnusualSecret!883",
            },
        )
        self.assertFalse(User.objects.filter(username="invalid").exists())

    def test_add_editor_and_journalist_idempotently(self):
        for employee in [self.writer, self.other]:
            for _ in range(2):
                self.assertEqual(
                    self.client.post(
                        reverse("publisher", args=[self.company.pk]),
                        {"username": employee.username},
                    ).status_code,
                    302,
                )
        self.assertEqual(self.company.editors.count(), 2)
        self.assertEqual(self.company.journalists.count(), 1)

    def test_reader_unknown_and_inactive_employees_rejected(self):
        self.writer.is_active = False
        self.writer.save()
        for username in ["reader", "missing", "writer"]:
            response = self.client.post(
                reverse("publisher", args=[self.company.pk]), {"username": username}
            )
            self.assertContains(response, "No active editor or journalist")
        self.assertEqual(self.company.journalists.count(), 0)

    def test_unassigned_editor_cannot_manage_other_company(self):
        self.client.force_login(self.other)
        for url, data in [
            (reverse("publisher", args=[self.company.pk]), {"username": "writer"}),
            (
                reverse("publisher_edit", args=[self.company.pk]),
                {"name": "Stolen", "description": "x"},
            ),
            (reverse("employee_remove", args=[self.company.pk, self.editor.pk]), {}),
        ]:
            self.assertEqual(self.client.post(url, data).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("publisher", args=[self.company.pk])).status_code,
            403,
        )

    def test_journalist_can_view_own_company_but_not_manage_it(self):
        self.company.journalists.add(self.writer)
        self.client.force_login(self.writer)
        self.assertContains(
            self.client.get(reverse("publisher", args=[self.company.pk])), "Dispatch"
        )
        self.assertEqual(
            self.client.post(
                reverse("publisher", args=[self.company.pk]), {"username": "other"}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("publisher_create"), {"name": "Blocked"}
            ).status_code,
            403,
        )

    def test_reader_cannot_manage_publishers(self):
        self.client.force_login(self.reader)
        for url in [
            reverse("publishers"),
            reverse("publisher_create"),
            reverse("publisher", args=[self.company.pk]),
        ]:
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_employee_removal_revokes_company_content_access(self):
        self.company.journalists.add(self.writer)
        article = Article.objects.create(
            author=self.writer, publisher=self.company, title="Draft", content="Body"
        )
        url = reverse("employee_remove", args=[self.company.pk, self.writer.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.assertTrue(User.objects.filter(pk=self.writer.pk).exists())
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())
        self.client.force_login(self.writer)
        self.assertEqual(
            self.client.get(reverse("article_edit", args=[article.pk])).status_code, 403
        )
        self.client.post(
            reverse("article_create"),
            {"title": "New", "content": "Body", "publisher": self.company.pk},
        )
        self.assertFalse(Article.objects.filter(title="New").exists())

    def test_last_editor_cannot_remove_self(self):
        self.client.post(
            reverse("employee_remove", args=[self.company.pk, self.editor.pk])
        )
        self.assertTrue(self.company.editors.filter(pk=self.editor.pk).exists())

    def test_editor_can_leave_when_another_active_editor_exists(self):
        self.company.editors.add(self.other)
        response = self.client.post(
            reverse("employee_remove", args=[self.company.pk, self.editor.pk])
        )
        self.assertRedirects(response, reverse("publishers"))
        self.assertFalse(self.company.editors.filter(pk=self.editor.pk).exists())

    def test_edit_profile_and_duplicate_name_validation(self):
        self.client.post(
            reverse("publisher_edit", args=[self.company.pk]),
            {"name": "Updated", "description": "Changed"},
        )
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, "Updated")
        self.assertEqual(
            self.client.post(
                reverse("publisher_create"),
                {"name": "Updated", "description": "Duplicate"},
            ).status_code,
            200,
        )
        self.assertEqual(Publisher.objects.count(), 1)

    def test_membership_changes_require_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.editor)
        self.assertEqual(
            client.post(
                reverse("publisher", args=[self.company.pk]), {"username": "writer"}
            ).status_code,
            403,
        )

    def test_anonymous_management_redirects_to_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("publishers")).status_code, 302)

    def test_home_has_stylesheet_and_business_navigation(self):
        self.client.logout()
        response = self.client.get(reverse("home"))
        self.assertContains(response, "/static/news/style.css")
        self.assertContains(response, "Start your newsroom")
        self.assertNotContains(response, "Join as a reader")
        self.assertIsNotNone(finders.find("news/style.css"))
