from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_migrate, post_save
from django.dispatch import receiver
from .models import User


ROLE_PERMISSIONS = {
    "Reader": ["view_article", "view_newsletter", "view_publisher"],
    "Editor": [
        "view_article",
        "change_article",
        "delete_article",
        "approve_article",
        "view_newsletter",
        "add_newsletter",
        "change_newsletter",
        "delete_newsletter",
        "view_publisher",
    ],
    "Journalist": [
        "add_article",
        "view_article",
        "change_article",
        "delete_article",
        "add_newsletter",
        "view_newsletter",
        "change_newsletter",
        "delete_newsletter",
        "view_publisher",
    ],
}


@receiver(post_migrate)
def configure_groups(sender, **kwargs):
    if sender.name != "news":
        return
    for name, codes in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=name)
        group.permissions.set(
            Permission.objects.filter(
                content_type__app_label="news", codename__in=codes
            )
        )


@receiver(post_save, sender=User)
def assign_role_group(sender, instance, raw=False, **kwargs):
    if raw:
        return
    group, _ = Group.objects.get_or_create(name=instance.get_role_display())
    instance.groups.remove(
        *Group.objects.filter(name__in=ROLE_PERMISSIONS).exclude(pk=group.pk)
    )
    instance.groups.add(group)
    if instance.role != User.Role.READER:
        instance.subscribed_publishers.clear()
        instance.subscribed_journalists.clear()


@receiver(m2m_changed, sender=User.subscribed_publishers.through)
@receiver(m2m_changed, sender=User.subscribed_journalists.through)
def validate_subscriptions(sender, instance, action, reverse, pk_set, **kwargs):
    if action != "pre_add":
        return
    if not reverse and instance.role != User.Role.READER:
        raise ValidationError("Only readers can hold subscriptions.")
    if reverse and User.objects.filter(pk__in=pk_set).exclude(role="reader").exists():
        raise ValidationError("Only readers can subscribe.")
    if sender == User.subscribed_journalists.through:
        if reverse and instance.role != User.Role.JOURNALIST:
            raise ValidationError("Subscriptions must target journalists.")
        if (
            not reverse
            and User.objects.filter(pk__in=pk_set).exclude(role="journalist").exists()
        ):
            raise ValidationError("Subscriptions must target journalists.")
