# Django Best Practices - Quick Reference

One-page cheat sheet for common patterns.

## 🚀 Query Optimization

```python
# ❌ N+1 Problem
for notice in Notice.objects.all():
    print(notice.created_by.username)  # Query each time!

# ✅ Fix with select_related (ForeignKey)
notices = Notice.objects.select_related('created_by').all()

# ✅ Fix with prefetch_related (M2M)
notices = Notice.objects.prefetch_related('recipients').all()

# ✅ Limit fields with only()
notices = Notice.objects.only('id', 'title', 'created_at')

# ✅ Bulk create
Notice.objects.bulk_create([Notice(...) for _ in range(100)])

# ✅ Bulk update
Notice.objects.filter(status='draft').update(status='published')
```

## 🧩 Custom Managers

```python
class NoticeQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status='published')
    
    def for_user(self, user):
        return self.filter(recipients__user=user).distinct()

class NoticeManager(models.Manager):
    def get_queryset(self):
        return NoticeQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()

class Notice(models.Model):
    objects = NoticeManager()
```

## 🏗️ Service Layer

```python
from dataclasses import dataclass
from django.db import transaction

@dataclass
class NoticeData:
    title: str
    content: str
    created_by: User

class NoticeService:
    @staticmethod
    @transaction.atomic
    def create_notice(data: NoticeData) -> Notice:
        notice = Notice.objects.create(
            title=data.title,
            content=data.content,
            created_by=data.created_by
        )
        # Add recipients, send notifications, etc.
        return notice
```

## 🧪 Testing

```python
import pytest
import factory

# Factory
class NoticeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notice
    
    title = factory.Faker('sentence')
    created_by = factory.SubFactory(UserFactory)

# Test
@pytest.mark.django_db
def test_notice_creation():
    notice = NoticeFactory(status='published')
    assert notice.status == 'published'

# Time-based test
from freezegun import freeze_time

@freeze_time("2025-01-01")
def test_with_frozen_time():
    notice = NoticeFactory()
    assert notice.created_at.year == 2025
```

## 🌐 i18n

```python
from django.utils.translation import gettext_lazy as _, format_lazy

# Static
label = _("Subject")

# Dynamic
title = format_lazy(_("Limit: {limit}"), limit=255)

# Don't mix!
# ❌ _("Limit: {limit}") % {"limit": 255}
```

## 📋 Mixins

```python
class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
    
    def delete(self):
        self.is_deleted = True
        self.save()

# Usage
class Notice(TimestampMixin, SoftDeleteMixin):
    title = models.CharField(max_length=255)
```

## 🎯 Type Hints

```python
from typing import Optional, List
from django.db.models import QuerySet

def get_notices(user: User) -> QuerySet[Notice]:
    return Notice.objects.filter(recipients__user=user)

def create_notice(data: dict) -> Optional[Notice]:
    try:
        return Notice.objects.create(**data)
    except Exception:
        return None
```

## 🔧 Code Quality

```bash
# Install tools
pipenv install --dev ruff mypy pytest

# Lint and format
ruff check --fix .
ruff format .

# Type check
mypy apps/

# Test
pytest --cov
```

## 🎨 Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

```bash
pre-commit install
```

## 📊 Logging

```python
import logging

logger = logging.getLogger(__name__)

def create_notice(request):
    logger.info(f"Creating notice for user {request.user.id}")
    try:
        notice = Notice.objects.create(...)
        logger.debug(f"Notice {notice.id} created")
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
```

## 🔐 Security

```bash
# Check for vulnerabilities
pipenv install --dev pip-audit
pipenv run pip-audit

# Update dependencies
pipenv update

# Check what requires a package
pipenv graph
```

## 🎭 AJAX Forms

```python
# Endpoint
@login_required
def search_recipients(request):
    search = request.GET.get('search', '')
    results = Recipient.objects.filter(
        name__icontains=search
    ).values('id', 'name')[:20]
    
    return JsonResponse(list(results), safe=False)

# Widget (see assets/choices_mixin.py)
widget = ChoicesSelect(
    ajax_url='/api/search-recipients/',
    ajax_params={'notice_id': notice.id}
)
```

## 📝 Git Commits

```bash
# Conventional commits
git commit -m "feat: add notice filtering"
git commit -m "fix: resolve N+1 query in list view"
git commit -m "docs: update README with new patterns"
git commit -m "refactor: extract business logic to service"

# Tagging
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

---

**For detailed documentation, see:**
- [SKILL.md](SKILL.md) - Core best practices
- [references/](references/) - Detailed pattern guides
- [assets/](assets/) - Ready-to-use code
