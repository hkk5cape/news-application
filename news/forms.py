from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Article, Newsletter, Publisher, User
from .policies import is_editor


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=User.Role.choices,
        help_text="Editors create and manage publishing companies. Journalists write articles. Readers follow news.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email", "role"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


class ArticleForm(forms.ModelForm):
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
    class Meta:
        model = User
        fields = ["subscribed_publishers", "subscribed_journalists"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subscribed_journalists"].queryset = User.objects.filter(
            role="journalist", is_active=True
        )


class PublisherForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ["name", "description"]


class EmployeeForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        help_text="Enter the exact username of an existing editor or journalist account.",
    )

    def clean_username(self):
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
