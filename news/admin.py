from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    ApprovedLog,
    ApprovalEvent,
    Article,
    ArticleEmail,
    Newsletter,
    NewsletterEmail,
    Publisher,
    User,
)


@admin.register(User)
class NewsUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "News roles and subscriptions",
            {"fields": ("role", "subscribed_publishers", "subscribed_journalists")},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (("News", {"fields": ("email", "role")}),)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    filter_horizontal = ("editors", "journalists")


# Content changes must use the application workflow so approval cannot be bypassed.
class AuditOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


for model in (
    Article,
    Newsletter,
    ApprovalEvent,
    ApprovedLog,
    ArticleEmail,
    NewsletterEmail,
):
    admin.site.register(model, AuditOnlyAdmin)
