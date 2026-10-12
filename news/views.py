from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import (
    ArticleForm,
    NewsletterForm,
    RegistrationForm,
    SubscriptionForm,
    PublisherForm,
    EmployeeForm,
)
from .models import Article, Newsletter, Publisher, User
from django.db import transaction
from .policies import can_edit, is_editor, subscribed_articles
from .services import approve_article, dispatch_approval, send_newsletter


def home(request):
    articles = Article.objects.filter(approved=True).select_related(
        "author", "publisher"
    )
    if request.GET.get("feed") == "subscribed":
        articles = (
            subscribed_articles(request.user)
            if request.user.is_authenticated
            else Article.objects.none()
        )
    return render(request, "news/home.html", {"articles": articles})


def register(request):
    form = RegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect(
            "publishers"
            if user.role == "editor"
            else "workspace"
            if user.role == "journalist"
            else "home"
        )
    return render(
        request, "news/form.html", {"form": form, "title": "Create your account"}
    )


@login_required
def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if not article.approved and not can_edit(request.user, article):
        raise PermissionDenied
    return render(
        request,
        "news/article.html",
        {
            "article": article,
            "editable": can_edit(request.user, article),
            "editor": is_editor(request.user) and can_edit(request.user, article),
        },
    )


@login_required
def workspace(request):
    if is_editor(request.user):
        articles = Article.objects.filter(
            Q(publisher=None) | Q(publisher__editors=request.user)
        ).distinct()
    elif request.user.role == "journalist":
        articles = (
            Article.objects.filter(author=request.user)
            .filter(Q(publisher=None) | Q(publisher__journalists=request.user))
            .distinct()
        )
    else:
        raise PermissionDenied
    return render(
        request,
        "news/workspace.html",
        {"articles": articles, "journalist": request.user.role == "journalist"},
    )


@login_required
def article_edit(request, pk=None):
    article = get_object_or_404(Article, pk=pk) if pk else None
    if article:
        if not can_edit(request.user, article) or not request.user.has_perm(
            "news.change_article"
        ):
            raise PermissionDenied
    elif request.user.role != "journalist" or not request.user.has_perm(
        "news.add_article"
    ):
        raise PermissionDenied
    form = ArticleForm(
        request.POST if request.method == "POST" else None,
        instance=article,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        if not article:
            item.author = request.user
        else:
            item.revision += 1
        item.approved, item.approved_by = False, None
        item.save()
        return redirect("workspace")
    return render(
        request,
        "news/form.html",
        {"form": form, "title": "Edit article" if article else "Write article"},
    )


@login_required
def article_delete(request, pk):
    item = get_object_or_404(Article, pk=pk)
    if not can_edit(request.user, item) or not request.user.has_perm(
        "news.delete_article"
    ):
        raise PermissionDenied
    if request.method == "POST":
        item.delete()
        return redirect("workspace")
    return render(request, "news/delete.html", {"item": item})


@login_required
@require_POST
def article_approve(request, pk):
    get_object_or_404(Article, pk=pk)
    if not request.user.has_perm("news.approve_article"):
        raise PermissionDenied
    event = approve_article(pk, request.user)
    dispatch_approval(event)
    messages.success(
        request,
        f"Approved. API logged: {event.api_logged}. Pending emails: {event.deliveries.filter(sent=False).count()}. Approve/retry repeats only unfinished deliveries.",
    )
    return redirect("article", pk=pk)


@login_required
def subscriptions(request):
    if request.user.role != "reader":
        raise PermissionDenied
    form = SubscriptionForm(
        request.POST if request.method == "POST" else None, instance=request.user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Subscriptions updated.")
        return redirect("home")
    return render(
        request,
        "news/form.html",
        {"form": form, "title": "Follow publishers and journalists"},
    )


@login_required
def newsletters(request):
    return render(
        request,
        "news/newsletters.html",
        {
            "newsletters": Newsletter.objects.all(),
            "creator": request.user.has_perm("news.add_newsletter"),
        },
    )


@login_required
def newsletter_detail(request, pk):
    item = get_object_or_404(Newsletter, pk=pk)
    return render(
        request,
        "news/newsletter.html",
        {
            "item": item,
            "articles": item.articles.filter(approved=True),
            "editable": can_edit(request.user, item),
        },
    )


@login_required
def newsletter_edit(request, pk=None):
    item = get_object_or_404(Newsletter, pk=pk) if pk else None
    permission = "news.change_newsletter" if item else "news.add_newsletter"
    if not request.user.has_perm(permission) or (
        item and not can_edit(request.user, item)
    ):
        raise PermissionDenied
    form = NewsletterForm(
        request.POST if request.method == "POST" else None,
        instance=item,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        newsletter = form.save(commit=False)
        if not item:
            newsletter.author = request.user
        else:
            newsletter.revision += 1
        newsletter.save()
        form.save_m2m()
        return redirect("newsletter", pk=newsletter.pk)
    return render(
        request, "news/form.html", {"form": form, "title": "Curate a newsletter"}
    )


@login_required
def newsletter_delete(request, pk):
    item = get_object_or_404(Newsletter, pk=pk)
    if not can_edit(request.user, item) or not request.user.has_perm(
        "news.delete_newsletter"
    ):
        raise PermissionDenied
    if request.method == "POST":
        item.delete()
        return redirect("newsletters")
    return render(request, "news/delete.html", {"item": item})


@login_required
@require_POST
def newsletter_send(request, pk):
    item = get_object_or_404(Newsletter, pk=pk)
    try:
        send_newsletter(item, request.user)
        messages.success(
            request,
            "Newsletter delivery attempted. Previously sent recipients were skipped.",
        )
    except ValidationError as error:
        messages.error(request, str(error))
    return redirect("newsletter", pk=pk)


@login_required
def publishers(request):
    if request.user.role == "editor":
        companies = Publisher.objects.filter(editors=request.user)
    elif request.user.role == "journalist":
        companies = Publisher.objects.filter(journalists=request.user)
    else:
        raise PermissionDenied
    return render(request, "news/publishers.html", {"publishers": companies})


@login_required
def publisher_edit(request, pk=None):
    if request.user.role != "editor":
        raise PermissionDenied
    company = get_object_or_404(Publisher, pk=pk) if pk else None
    if company and not company.editors.filter(pk=request.user.pk).exists():
        raise PermissionDenied
    form = PublisherForm(
        request.POST if request.method == "POST" else None, instance=company
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            company = form.save()
            company.editors.add(request.user)
        messages.success(
            request, "Publisher profile saved. Manage your employees below."
        )
        return redirect("publisher", pk=company.pk)
    return render(
        request,
        "news/form.html",
        {
            "form": form,
            "title": "Edit publisher" if company else "Create your publisher",
        },
    )


@login_required
def publisher_detail(request, pk):
    company = get_object_or_404(Publisher, pk=pk)
    manager = (
        request.user.role == "editor"
        and company.editors.filter(pk=request.user.pk).exists()
    )
    member = (
        request.user.role == "journalist"
        and company.journalists.filter(pk=request.user.pk).exists()
    )
    if not (manager or member):
        raise PermissionDenied
    form = EmployeeForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if not manager:
            raise PermissionDenied
        if form.is_valid():
            employee = form.employee
            membership = (
                company.editors if employee.role == "editor" else company.journalists
            )
            membership.add(employee)
            messages.success(request, "Employee added to this publisher.")
            return redirect("publisher", pk=company.pk)
    return render(
        request,
        "news/publisher.html",
        {"company": company, "manager": manager, "form": form},
    )


@login_required
@require_POST
def employee_remove(request, pk, user_pk):
    with transaction.atomic():
        company = get_object_or_404(Publisher.objects.select_for_update(), pk=pk)
        if (
            request.user.role != "editor"
            or not company.editors.filter(pk=request.user.pk).exists()
        ):
            raise PermissionDenied
        employee = get_object_or_404(User, pk=user_pk)
        if company.editors.filter(pk=employee.pk).exists():
            if (
                company.editors.filter(role="editor", is_active=True)
                .exclude(pk=employee.pk)
                .count()
                == 0
            ):
                messages.error(
                    request,
                    "Keep at least one active editor. Add another editor before removing this one.",
                )
                return redirect("publisher", pk=pk)
            company.editors.remove(employee)
        elif company.journalists.filter(pk=employee.pk).exists():
            company.journalists.remove(employee)
        else:
            from django.http import Http404

            raise Http404("Employee is not part of this publisher.")
    messages.success(
        request,
        "Employee removed from this publisher. Their account and published content are retained.",
    )
    return (
        redirect("publisher", pk=pk)
        if employee.pk != request.user.pk
        else redirect("publishers")
    )
