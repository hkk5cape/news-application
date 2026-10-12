from unittest.mock import Mock, patch
from django.contrib.auth.models import Group
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import LiveServerTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from .models import (
    ApprovalEvent,
    ApprovedLog,
    Article,
    ArticleEmail,
    Newsletter,
    NewsletterEmail,
    Publisher,
    User,
)
from .services import approve_article, dispatch_approval, send_newsletter


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class NewsTests(TestCase):
    def setUp(self):
        self.j = User.objects.create_user(
            "writer", "writer@example.com", "Password!778", role="journalist"
        )
        self.j2 = User.objects.create_user(
            "other", "other@example.com", "Password!778", role="journalist"
        )
        self.e = User.objects.create_user(
            "editor", "editor@example.com", "Password!778", role="editor"
        )
        self.r = User.objects.create_user(
            "reader", "reader@example.com", "Password!778", role="reader"
        )
        self.r2 = User.objects.create_user(
            "reader2", "reader2@example.com", "Password!778", role="reader"
        )
        self.pub = Publisher.objects.create(name="Daily", description="Local reporting")
        self.pub.editors.add(self.e)
        self.pub.journalists.add(self.j)
        self.a = Article.objects.create(
            title="Local news", content="Story", author=self.j, publisher=self.pub
        )
        self.independent = Article.objects.create(
            title="Independent",
            content="Independent story",
            author=self.j2,
            approved=True,
        )
        self.api = APIClient()

    def auth(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.api.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def test_role_groups_and_permissions(self):
        self.assertTrue(self.j.groups.filter(name="Journalist").exists())
        self.assertTrue(self.e.has_perm("news.approve_article"))
        self.assertTrue(self.e.has_perm("news.add_newsletter"))
        self.assertFalse(self.e.has_perm("news.add_article"))
        self.assertTrue(self.r.has_perm("news.view_article"))
        self.assertFalse(self.r.has_perm("news.change_article"))

    def test_role_specific_fields_and_transition(self):
        self.assertIsNone(self.j.reader_subscriptions)
        self.assertIsNone(self.r.independent_articles)
        self.r.subscribed_publishers.add(self.pub)
        self.r.role = "journalist"
        self.r.save()
        self.assertFalse(self.r.subscribed_publishers.exists())
        self.assertTrue(self.r.groups.filter(name="Journalist").exists())
        self.assertFalse(self.r.groups.filter(name="Reader").exists())

    def test_journalist_cannot_hold_subscriptions(self):
        with self.assertRaises(ValidationError):
            self.j.subscribed_publishers.add(self.pub)

    def test_only_journalists_are_subscription_targets(self):
        with self.assertRaises(ValidationError):
            self.r.subscribed_journalists.add(self.e)

    def test_registration_selects_role_without_admin_privileges(self):
        self.client.post(
            reverse("register"),
            {
                "username": "new",
                "email": "new@example.com",
                "password1": "GoodSecret!77781",
                "password2": "GoodSecret!77781",
                "role": "editor",
                "is_staff": True,
            },
        )
        user = User.objects.get(username="new")
        self.assertEqual(user.role, "editor")
        self.assertFalse(user.is_staff)

    def test_token_endpoint_and_wrong_password(self):
        response = self.api.post(
            reverse("api_token"), {"username": "reader", "password": "Password!778"}
        )
        self.assertIn("token", response.data)
        response = self.api.post(
            reverse("api_token"), {"username": "reader", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_access_denied(self):
        self.assertEqual(self.api.get(reverse("api_articles")).status_code, 401)

    def test_all_roles_read_approved_only(self):
        for user in (self.r, self.j, self.e):
            self.auth(user)
            response = self.api.get(reverse("api_articles"))
            self.assertEqual(
                [item["id"] for item in response.data["results"]], [self.independent.pk]
            )

    def test_subscribed_publisher_filter(self):
        self.a.approved = True
        self.a.save()
        self.r.subscribed_publishers.add(self.pub)
        self.auth(self.r)
        response = self.api.get(reverse("api_subscribed"))
        self.assertEqual([item["id"] for item in response.data["results"]], [self.a.pk])

    def test_subscribed_journalist_and_deduplication(self):
        self.a.approved = True
        self.a.save()
        self.r.subscribed_publishers.add(self.pub)
        self.r.subscribed_journalists.add(self.j)
        self.auth(self.r)
        self.assertEqual(self.api.get(reverse("api_subscribed")).data["count"], 1)

    def test_subscribed_feed_isolated_and_no_draft_leak(self):
        self.r.subscribed_publishers.add(self.pub)
        self.r2.subscribed_journalists.add(self.j2)
        self.auth(self.r)
        response = self.api.get(reverse("api_subscribed"), {"reader": self.r2.pk})
        self.assertEqual(response.data["count"], 0)

    def test_nonreader_subscribed_endpoint_denied(self):
        self.auth(self.j)
        self.assertEqual(self.api.get(reverse("api_subscribed")).status_code, 403)

    def test_journalist_creates_article_with_approval_ignored(self):
        self.auth(self.j)
        response = self.api.post(
            reverse("api_articles"),
            {
                "title": "New",
                "content": "Body",
                "publisher": self.pub.pk,
                "approved": True,
                "author": self.j2.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        item = Article.objects.get(pk=response.data["id"])
        self.assertEqual(item.author, self.j)
        self.assertFalse(item.approved)

    def test_editor_and_reader_cannot_create_articles(self):
        for user in (self.e, self.r):
            self.auth(user)
            self.assertEqual(
                self.api.post(
                    reverse("api_articles"),
                    {"title": "Bad", "content": "Body"},
                    format="json",
                ).status_code,
                403,
            )

    def test_invalid_publisher_and_fields_rejected(self):
        self.auth(self.j2)
        response = self.api.post(
            reverse("api_articles"),
            {"title": "Bad", "content": "Body", "publisher": self.pub.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self.api.post(reverse("api_articles"), {}, format="json").status_code, 400
        )

    def test_owner_update_resets_approval(self):
        self.a.approved = True
        self.a.save()
        self.auth(self.j)
        response = self.api.put(
            reverse("api_article", args=[self.a.pk]),
            {"title": "Updated", "content": "New text", "publisher": self.pub.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.a.refresh_from_db()
        self.assertFalse(self.a.approved)
        self.assertEqual(self.a.revision, 2)

    def test_reader_cannot_mutate(self):
        self.auth(self.r)
        for method in (self.api.put, self.api.delete):
            self.assertEqual(
                method(
                    reverse("api_article", args=[self.independent.pk]),
                    {},
                    format="json",
                ).status_code,
                403,
            )

    def test_other_journalist_cannot_update(self):
        self.a.approved = True
        self.a.save()
        self.auth(self.j2)
        self.assertEqual(
            self.api.patch(
                reverse("api_article", args=[self.a.pk]),
                {"title": "Bad"},
                format="json",
            ).status_code,
            403,
        )

    def test_reader_cannot_retrieve_draft(self):
        self.auth(self.r)
        self.assertEqual(
            self.api.get(reverse("api_article", args=[self.a.pk])).status_code, 404
        )

    def test_editor_can_delete(self):
        self.auth(self.e)
        self.assertEqual(
            self.api.delete(reverse("api_article", args=[self.a.pk])).status_code, 204
        )
        self.assertFalse(Article.objects.filter(pk=self.a.pk).exists())

    def test_missing_article_returns_404(self):
        self.auth(self.r)
        self.assertEqual(
            self.api.get(reverse("api_article", args=[999])).status_code, 404
        )

    def test_journalist_cannot_approve(self):
        self.auth(self.j)
        self.assertEqual(
            self.api.post(reverse("api_approve", args=[self.a.pk])).status_code, 403
        )

    def test_unassigned_editor_cannot_approve(self):
        other = User.objects.create_user(
            "e2", "e2@example.com", "Password!778", role="editor"
        )
        with self.assertRaises(PermissionDenied):
            approve_article(self.a.pk, other)

    def test_editor_group_can_approve_independent_article(self):
        self.r.groups.add(Group.objects.get(name="Editor"))
        event = approve_article(self.independent.pk, self.r)
        self.assertEqual(event.approved_by, self.r)

    @patch("news.services.requests.post")
    def test_approval_dispatch_email_and_post(self, post):
        self.r.subscribed_publishers.add(self.pub)
        self.r.subscribed_journalists.add(self.j)
        event = approve_article(self.a.pk, self.e)
        post.return_value = Mock(
            status_code=201, json=Mock(return_value={"event_id": event.pk})
        )
        dispatch_approval(event)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.r.email])
        self.assertIn("Story", mail.outbox[0].body)
        self.assertEqual(post.call_args.kwargs["json"], {"event_id": event.pk})
        self.assertTrue(
            post.call_args.kwargs["headers"]["Authorization"].startswith("Token ")
        )
        self.assertTrue(event.api_logged)

    @patch("news.services.requests.post")
    def test_reapproval_is_idempotent(self, post):
        event = approve_article(self.a.pk, self.e)
        post.return_value = Mock(
            status_code=201, json=Mock(return_value={"event_id": event.pk})
        )
        dispatch_approval(event)
        again = approve_article(self.a.pk, self.e)
        dispatch_approval(again)
        self.assertEqual(ApprovalEvent.objects.count(), 1)
        self.assertEqual(post.call_count, 1)

    @patch("news.services.requests.post")
    @patch("news.services.send_mail", side_effect=OSError("offline"))
    def test_failures_remain_retryable(self, send, post):
        import requests

        post.side_effect = requests.Timeout()
        self.r.subscribed_publishers.add(self.pub)
        event = approve_article(self.a.pk, self.e)
        dispatch_approval(event)
        self.a.refresh_from_db()
        self.assertTrue(self.a.approved)
        self.assertFalse(event.api_logged)
        self.assertFalse(ArticleEmail.objects.get().sent)
        self.assertTrue(event.api_error)

    def test_approved_log_post_uses_trusted_snapshot(self):
        event = approve_article(self.a.pk, self.e)
        self.auth(self.e)
        for code in (201, 200):
            response = self.api.post(
                reverse("api_approved"),
                {"event_id": event.pk, "title": "Spoofed"},
                format="json",
            )
            self.assertEqual(response.status_code, code)
        self.assertEqual(ApprovedLog.objects.count(), 1)
        self.assertEqual(ApprovedLog.objects.get().payload["title"], "Local news")

    def test_reader_cannot_log_or_list_approval_events(self):
        self.auth(self.r)
        self.assertEqual(
            self.api.post(reverse("api_approved"), {"event_id": 1}).status_code, 403
        )
        self.assertEqual(self.api.get(reverse("api_approved")).status_code, 403)

    def test_newsletter_create_view_and_read(self):
        self.auth(self.j)
        response = self.api.post(
            reverse("api_newsletters"),
            {
                "title": "Weekly",
                "description": "Selected",
                "articles": [self.independent.pk],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.auth(self.r)
        self.assertEqual(self.api.get(reverse("api_newsletters")).data["count"], 1)
        self.assertEqual(
            self.api.post(reverse("api_newsletters"), {}, format="json").status_code,
            403,
        )

    def test_editor_can_create_and_edit_newsletter(self):
        self.auth(self.e)
        response = self.api.post(
            reverse("api_newsletters"),
            {
                "title": "Desk",
                "description": "Editorial",
                "articles": [self.independent.pk],
                "publisher": self.pub.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            self.api.patch(
                reverse("api_newsletter", args=[response.data["id"]]),
                {"title": "Updated"},
                format="json",
            ).status_code,
            200,
        )

    def test_newsletter_cannot_select_draft(self):
        self.auth(self.j)
        response = self.api.post(
            reverse("api_newsletters"),
            {"title": "Bad", "description": "Draft", "articles": [self.a.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_revoked_article_hidden_from_newsletter(self):
        item = Newsletter.objects.create(
            author=self.j, title="Weekly", description="News"
        )
        item.articles.add(self.independent)
        self.independent.approved = False
        self.independent.save()
        self.auth(self.r)
        response = self.api.get(reverse("api_newsletter", args=[item.pk]))
        self.assertEqual(response.data["articles"], [])

    def test_newsletter_email_deduplicates(self):
        item = Newsletter.objects.create(
            author=self.j, title="Weekly", description="News", publisher=self.pub
        )
        item.articles.add(self.independent)
        self.r.subscribed_publishers.add(self.pub)
        self.r.subscribed_journalists.add(self.j)
        send_newsletter(item, self.j)
        send_newsletter(item, self.j)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(NewsletterEmail.objects.count(), 1)

    def test_other_journalist_cannot_edit_newsletter(self):
        item = Newsletter.objects.create(
            author=self.j, title="Weekly", description="News"
        )
        self.auth(self.j2)
        self.assertEqual(
            self.api.patch(
                reverse("api_newsletter", args=[item.pk]),
                {"title": "Bad"},
                format="json",
            ).status_code,
            403,
        )

    def test_user_serialization_hides_inapplicable_fields(self):
        self.auth(self.r)
        response = self.api.get(reverse("api_me"))
        self.assertIsNone(response.data["independent_articles"])
        self.auth(self.j)
        self.assertIsNone(self.api.get(reverse("api_me")).data["subscriptions"])

    def test_web_pages_and_subscription_save(self):
        self.client.force_login(self.r)
        for name in ("home", "subscriptions", "newsletters"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.client.post(
            reverse("subscriptions"),
            {
                "subscribed_publishers": [self.pub.pk],
                "subscribed_journalists": [self.j.pk],
            },
        )
        self.assertTrue(self.r.subscribed_publishers.filter(pk=self.pub.pk).exists())
        self.client.force_login(self.j)
        for name in ("workspace", "article_create", "newsletter_create"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class RealHTTPApprovalTests(LiveServerTestCase):
    def test_real_self_post_reaches_approved_endpoint(self):
        import requests

        journalist = User.objects.create_user(
            "livewriter", "lw@example.com", "Password!778", role="journalist"
        )
        editor = User.objects.create_user(
            "liveeditor", "le@example.com", "Password!778", role="editor"
        )
        article = Article.objects.create(
            author=journalist, title="Live HTTP", content="Internal integration"
        )
        token = Token.objects.create(user=editor)
        with override_settings(API_BASE_URL=self.live_server_url):
            response = requests.post(
                self.live_server_url + reverse("api_approve", args=[article.pk]),
                headers={"Authorization": "Token " + token.key},
                timeout=20,
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["api_logged"])
        self.assertEqual(ApprovedLog.objects.count(), 1)
        self.assertEqual(ApprovedLog.objects.get().payload["title"], "Live HTTP")
