"""Database models for publishing, subscriptions, and retryable deliveries."""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """An account with a publishing role and reader-only subscriptions."""
    class Role(models.TextChoices):
        """Available account roles selected during registration."""
        READER = "reader", "Reader"
        EDITOR = "editor", "Editor"
        JOURNALIST = "journalist", "Journalist"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.READER)
    email = models.EmailField(unique=True)
    subscribed_publishers = models.ManyToManyField(
        "Publisher", blank=True, related_name="subscribers"
    )
    subscribed_journalists = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="journalist_subscribers",
        limit_choices_to={"role": "journalist"},
    )

    @property
    def reader_subscriptions(self):
        """Return publisher and journalist querysets for readers, otherwise None."""
        if self.role != self.Role.READER:
            return None
        return {
            "publishers": self.subscribed_publishers.all(),
            "journalists": self.subscribed_journalists.all(),
        }

    @property
    def independent_articles(self):
        """Return a journalist's articles without a publisher, or None."""
        return (
            self.authored_articles.filter(publisher=None)
            if self.role == self.Role.JOURNALIST
            else None
        )

    @property
    def independent_newsletters(self):
        """Return a journalist's independent newsletters, or None."""
        return (
            self.authored_newsletters.filter(publisher=None)
            if self.role == self.Role.JOURNALIST
            else None
        )


class Publisher(models.Model):
    """A publishing company with assigned editors and journalists."""
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="edited_publishers",
        blank=True,
        limit_choices_to={"role": "editor"},
    )
    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="publisher_memberships",
        blank=True,
        limit_choices_to={"role": "journalist"},
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    """A revision-controlled story that remains private until approved."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_articles",
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="articles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_articles",
    )
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at", "-pk"]
        permissions = [("approve_article", "Can approve article")]

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    """An authored collection of approved articles for subscribers."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_newsletters",
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="newsletters",
    )
    articles = models.ManyToManyField(Article, related_name="newsletters")
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title


class ApprovalEvent(models.Model):
    """Store one approval snapshot per article revision for delivery retries."""
    article = models.ForeignKey(Article, null=True, on_delete=models.SET_NULL)
    article_id_snapshot = models.PositiveBigIntegerField()
    revision = models.PositiveIntegerField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    api_logged = models.BooleanField(default=False)
    api_error = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["article_id_snapshot", "revision"],
                name="one_event_per_revision",
            )
        ]


class ArticleEmail(models.Model):
    """Track whether one reader received an article approval email."""
    event = models.ForeignKey(
        ApprovalEvent, on_delete=models.CASCADE, related_name="deliveries"
    )
    reader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    email = models.EmailField()
    sent = models.BooleanField(default=False)
    error = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "reader"], name="one_email_per_reader_event"
            )
        ]


class ApprovedLog(models.Model):
    """Record an authenticated approval event received by the API."""
    event = models.OneToOneField(ApprovalEvent, on_delete=models.PROTECT)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)


class NewsletterEmail(models.Model):
    """Track delivery of a newsletter revision to an individual reader."""
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    reader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    email = models.EmailField()
    sent = models.BooleanField(default=False)
    error = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["newsletter", "revision", "reader"], name="one_newsletter_email"
            )
        ]
