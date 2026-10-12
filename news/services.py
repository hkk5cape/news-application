from smtplib import SMTPException
import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.db import transaction
from rest_framework.authtoken.models import Token
from .models import ApprovalEvent, Article, ArticleEmail, NewsletterEmail
from .policies import can_edit, is_editor, subscribers


@transaction.atomic
def approve_article(article_id, editor):
    """Commit approval and a durable event before any network calls."""
    article = (
        Article.objects.select_for_update()
        .select_related("publisher", "author")
        .get(pk=article_id)
    )
    if not is_editor(editor) or not can_edit(editor, article):
        raise PermissionDenied("Only an assigned editor can approve this article.")
    if article.author_id == editor.pk:
        raise PermissionDenied("Authors cannot approve their own articles.")
    article.approved = True
    article.approved_by = editor
    article.save(update_fields=["approved", "approved_by"])
    snapshot = {
        "article_id": article.pk,
        "revision": article.revision,
        "title": article.title,
        "content": article.content,
        "author": article.author.username,
        "publisher": article.publisher.name if article.publisher else None,
    }
    event, created = ApprovalEvent.objects.get_or_create(
        article_id_snapshot=article.pk,
        revision=article.revision,
        defaults={"article": article, "approved_by": editor, "snapshot": snapshot},
    )
    if created:
        ArticleEmail.objects.bulk_create(
            [
                ArticleEmail(event=event, reader=reader, email=reader.email)
                for reader in subscribers(article.author_id, article.publisher_id)
            ]
        )
    return event


def dispatch_approval(event):
    """Called by the approval view after commit; retries only unfinished work."""
    for delivery in event.deliveries.filter(sent=False):
        try:
            body = (
                event.snapshot["content"]
                + "\n\n"
                + settings.SITE_URL
                + f"/articles/{event.article_id_snapshot}/"
            )
            if (
                send_mail(
                    event.snapshot["title"],
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [delivery.email],
                )
                != 1
            ):
                raise OSError("Email not accepted")
            delivery.sent, delivery.error = True, ""
        except (SMTPException, OSError):
            delivery.error = "Email delivery failed; retry is available."
        delivery.save(update_fields=["sent", "error"])
    if not event.api_logged:
        token, _ = Token.objects.get_or_create(user=event.approved_by)
        try:
            response = requests.post(
                settings.API_BASE_URL + "/api/approved/",
                json={"event_id": event.pk},
                headers={"Authorization": "Token " + token.key},
                timeout=(3, 8),
                allow_redirects=False,
            )
            response.raise_for_status()
            if (
                response.status_code not in (200, 201)
                or response.json().get("event_id") != event.pk
            ):
                raise ValueError("Unexpected log response")
            event.api_logged, event.api_error = True, ""
        except (requests.RequestException, ValueError, AttributeError):
            event.api_error = "Approval API delivery failed; retry is available."
        event.save(update_fields=["api_logged", "api_error"])
    return event


def send_newsletter(newsletter, user):
    if not can_edit(user, newsletter):
        raise PermissionDenied
    articles = list(newsletter.articles.filter(approved=True))
    if not articles:
        raise ValidationError("Select at least one approved article before sending.")
    body = (
        newsletter.description
        + "\n\n"
        + "\n\n".join(a.title + "\n" + a.content for a in articles)
    )
    for reader in subscribers(newsletter.author_id, newsletter.publisher_id):
        delivery, _ = NewsletterEmail.objects.get_or_create(
            newsletter=newsletter,
            revision=newsletter.revision,
            reader=reader,
            defaults={"email": reader.email},
        )
        if delivery.sent:
            continue
        try:
            if (
                send_mail(
                    newsletter.title,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [delivery.email],
                )
                != 1
            ):
                raise OSError("Email not accepted")
            delivery.sent, delivery.error = True, ""
        except (SMTPException, OSError):
            delivery.error = "Newsletter email failed; retry send."
        delivery.save(update_fields=["sent", "error"])
