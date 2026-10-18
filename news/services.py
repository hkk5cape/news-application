"""Coordinate article approval, subscriber email, and authenticated API delivery."""

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
    """Approve a story and create a durable delivery event in one transaction.

    Args:
        article_id (int): Primary key of the article to review.
        editor (news.models.User): Editor requesting approval.

    Returns:
        news.models.ApprovalEvent: The existing or newly created revision event.

    Raises:
        django.core.exceptions.PermissionDenied: The editor cannot review this story
            or attempts to approve their own work.
        news.models.Article.DoesNotExist: The article identifier does not exist.

    Network calls occur separately through dispatch_approval after commit.
    """
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
    """Attempt unfinished email and API deliveries for an approval event.

    Args:
        event (news.models.ApprovalEvent): Committed approval snapshot to deliver.

    Returns:
        news.models.ApprovalEvent: Event with updated delivery status.

    Recorded successful deliveries are skipped. Failed attempts retain a generic
    error and can be retried. This does not guarantee exactly-once delivery if a
    remote service accepts a request but the acknowledgement is lost.
    """
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
    """Email approved newsletter content to the current subscribers.

    Args:
        newsletter (news.models.Newsletter): Newsletter revision to distribute.
        user (news.models.User): Account requesting the send.

    Raises:
        django.core.exceptions.PermissionDenied: The user cannot edit the newsletter.
        django.core.exceptions.ValidationError: No approved articles are selected.

    Previously successful deliveries for the same revision are skipped.
    """
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
