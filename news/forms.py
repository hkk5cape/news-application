"""Validated forms for registration, publishing, and company membership."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Article, Newsletter, Publisher, User
from .policies import is_editor


class RegistrationForm(UserCreationForm):
    """Register an account with a selected role and a unique email address."""
    role = forms.ChoiceField(
        choices=User.Role.choices,
        help_text="Editors create and manage publishing companies. Journalists write articles. Readers follow news.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email", "role"]

    def clean_email(self):
        """Normalise the email address and reject case-insensitive duplicates."""
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


class ArticleForm(forms.ModelForm):
    """Limit publisher choices to companies associated with the current user."""
    class Meta:
        model = Article
        fields = ["title", "content", "publisher"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["publisher"].queryset = (
            Publisher.objects.filter(editors=user)
            if is_editor(user)
            else Publisher.objects.filter(journalists=user)
        )


class NewsletterForm(forms.ModelForm):
    """Offer approved articles and publishers available to the current user."""
    class Meta:
        model = Newsletter
        fields = ["title", "description", "publisher", "articles"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["publisher"].queryset = (
            Publisher.objects.filter(editors=user)
            if is_editor(user)
            else Publisher.objects.filter(journalists=user)
        )
        self.fields["articles"].queryset = Article.objects.filter(approved=True)


class SubscriptionForm(forms.ModelForm):
    """Let a reader select publishers and active journalist accounts."""
    class Meta:
        model = User
        fields = ["subscribed_publishers", "subscribed_journalists"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subscribed_journalists"].queryset = User.objects.filter(
            role="journalist", is_active=True
        )


class PublisherForm(forms.ModelForm):
    """Validate the editable name and description of a publishing company."""
    class Meta:
        model = Publisher
        fields = ["name", "description"]


class EmployeeForm(forms.Form):
    """Resolve an existing active editor or journalist by exact username."""
    username = forms.CharField(
        max_length=150,
        help_text="Enter the exact username of an existing editor or journalist account.",
    )

    def clean_username(self):
        """Resolve the employee or raise a field validation error."""
        username = self.cleaned_data["username"].strip()
        try:
            self.employee = User.objects.get(
                username=username, is_active=True, role__in=["editor", "journalist"]
            )
        except User.DoesNotExist:
            raise forms.ValidationError(
                "No active editor or journalist with this username. Ask the employee to register first."
            )
        return username
