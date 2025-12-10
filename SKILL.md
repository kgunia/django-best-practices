---
name: django-best-practices
description: Standardowe praktyki kodowania Django dla Karola. Użyj przy tworzeniu Django views, forms, models, testów, oraz przy optymalizacji queries. Zawiera wzorce AJAX z Choices.js, i18n z gettext_lazy, query optimization, pytest patterns, security audits. Użyj gdy piszesz kod Django lub optymalizujesz wydajność.
---

# Django Best Practices

Standardy kodowania i sprawdzone wzorce dla projektów Django.

**Version:** 2.0 (December 2025)
**Django:** 4.x/5.x
**Python:** 3.11+

## Installation

**Option 1: Upload to Claude Project**
1. Go to Projects in Claude.ai
2. Select your project
3. Click "Add content" → "Upload files"
4. Upload the `django-best-practices.skill` file

**Option 2: Manual setup**
```bash
mkdir -p ~/.claude/skills/django-best-practices
unzip django-best-practices.skill -d ~/.claude/skills/django-best-practices/
```

## Quick Start

Claude automatically applies these practices when:
- Writing Django code (views, models, forms)
- Reviewing/refactoring existing code
- Discussing architecture decisions
- Helping with debugging
- Optimizing queries

**Example prompts:**
- "Write a Django view following best practices"
- "Refactor this code using Django patterns"
- "Add tests for this view"
- "Optimize these database queries"

---

## Code Style

**Type Hints:** Always use for functions and methods
```python
def get_recipients(notice: Notice) -> QuerySet[AdditionalRecipient]:
    return AdditionalRecipient.objects.filter(notice=notice)
```

**Docstrings:** For complex functions
```python
def complex_filtering(user: User, status: str) -> QuerySet:
    """
    Filter notices for user considering all recipient types.
    
    Args:
        user: User instance
        status: Notice status filter
        
    Returns:
        Filtered queryset of Notice objects
    """
```

## String Formatting & Internationalization

**ALWAYS use:**
- `gettext_lazy` as `_()` for static translations
- `format_lazy()` for dynamic translations with parameters
- f-strings ONLY for debugging (not for user-facing text)

**Correct:**
```python
from django.utils.translation import gettext_lazy as _, format_lazy

# Static
label = _("Subject")

# Dynamic with parameters
title = format_lazy(_("Character limit: {limit}."), limit=255)

# Alternative with .format()
title = _("Character limit: {limit}.").format(limit=255)
```

**INCORRECT (don't mix syntax!):**
```python
# ❌ Mixing {variable} with % operator
_("Character limit: {limit}.") % {"limit": 255}

# ❌ f-string for UI (won't be translated)
label = f"Limit: {value}"
```

**Operator % - if you must:**
```python
_("Character limit: %(limit)s.") % {"limit": 255}
```

## Query Optimization

**Basic rules:**
1. **select_related()** for ForeignKey (JOIN)
2. **prefetch_related()** for M2M and reverse FK (separate queries)
3. **only()** when you need only specific fields
4. **Avoid N+1 queries** - always use bulk operations

**Example:**
```python
# ❌ N+1 problem
recipients = AdditionalRecipient.objects.filter(notice=notice)
for r in recipients:
    print(r.notice.title)  # Query on each iteration!

# ✅ Optimization
recipients = (
    AdditionalRecipient.objects
    .filter(notice=notice)
    .select_related('notice')  # Single JOIN
    .only('id', 'first_name', 'last_name', 'email', 'notice__title')
    .order_by('last_name', 'first_name')
)
```

**For complex relationships - check references/query_optimization.md**

## AJAX Forms & Choices.js

**Universal pattern for AJAX search in select fields.**

See `assets/choices_mixin.py` for ready-to-use code and `references/ajax_patterns.md` for detailed examples.

**Basic flow:**
1. Create endpoint returning JSON `[{"value": "id", "label": "text"}]`
2. Use ChoicesMixin with ajax_url
3. JavaScript automatically handles debounce (300ms) and fetch

**Example:**
```python
# views.py
@login_required
def search_recipients(request):
    notice_id = request.GET.get('notice_id')
    search = request.GET.get('search', '')
    
    recipients = (
        AdditionalRecipient.objects
        .filter(notice_id=notice_id)
        .filter(Q(first_name__icontains=search) | Q(email__icontains=search))
        .only('id', 'first_name', 'last_name', 'email')[:20]
    )
    
    return JsonResponse([
        {'value': str(r.id), 'label': f"{r.first_name} {r.last_name} ({r.email})"}
        for r in recipients
    ], safe=False)

# forms.py - use ready mixin from assets/
```

## Testing

**Always use pytest-django + factory-boy.**

**Installation:**
```bash
pipenv install --dev pytest pytest-django pytest-cov factory-boy freezegun
```

**Basic structure:**
```python
import pytest
from django.contrib.auth import get_user_model
from freezegun import freeze_time

User = get_user_model()

@pytest.mark.django_db
class TestNoticeFiltering:
    @pytest.fixture
    def setup_data(self):
        user = User.objects.create_user(username="test", email="test@test.com")
        return {'user': user}
    
    def test_direct_recipient(self, setup_data):
        # Test implementation
        pass
```

**Factory-Boy for test data:**
```python
# tests/factories.py
import factory
from apps.notices.models import Notice
from django.contrib.auth import get_user_model

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")

class NoticeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notice
    
    title = factory.Faker('sentence', nb_words=4)
    content = factory.Faker('paragraph')
    status = Notice.Status.DRAFT
    created_by = factory.SubFactory(UserFactory)

# Usage in tests
@pytest.mark.django_db
def test_notice_creation():
    notice = NoticeFactory(status=Notice.Status.PUBLISHED)
    assert notice.status == Notice.Status.PUBLISHED
    
    # Create batch
    notices = NoticeFactory.create_batch(10)
    assert Notice.objects.count() == 11
```

**Freezegun for time-based tests:**
```python
from freezegun import freeze_time
from datetime import datetime, timedelta

@pytest.mark.django_db
@freeze_time("2025-12-10 10:00:00")
def test_notice_expiration():
    """Test notices expire after 30 days."""
    notice = NoticeFactory(
        start_date=datetime(2025, 11, 1)
    )
    
    # Check if expired
    assert notice.is_expired()  # Should be True (> 30 days)
    
@pytest.mark.django_db
def test_notice_with_time_travel():
    """Test with time manipulation."""
    with freeze_time("2025-01-01"):
        notice = NoticeFactory()
        assert notice.created_at.year == 2025
    
    # Time travel forward
    with freeze_time("2025-06-01"):
        assert (datetime.now() - notice.created_at).days > 150
```

**Test all edge cases** - 4 recipient types, empty querysets, permissions, time-based logic.

See `references/testing_patterns.md` for more examples.

## Security

**pip-audit dla vulnerability scanning:**
```bash
pipenv install --dev pip-audit
pipenv run pip-audit
```

Jeśli znajdzie podatności w indirect dependencies, zaktualizuj parent package:
```bash
pipenv graph  # znajdź kto wymaga podatnej paczki
pipenv update django  # zaktualizuj parent
```

## Git Workflow

**Conventional Commits:**
```bash
fix(notices): add recipient group filtering to queryset
feat(forms): implement universal AJAX search mixin
chore(deps): update Django to 4.2.20
```

**Tagging:**
```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

## Flake8

**Ignorowanie warnings gdy uzasadnione:**
```python
subprocess.call(cmd, shell=True)  # noqa: B605 B607
```

Używaj konkretnych kodów, nie `# noqa` sam w sobie.

## Advanced Patterns

### Custom QuerySet Managers

**Encapsulate complex queries in custom managers:**

```python
from django.db import models

class PublishedNoticeQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Notice.Status.PUBLISHED)
    
    def for_user(self, user):
        entity_ids = user_role_entity_ids(user)
        return self.filter(
            Q(noticerecipient__recipient_id__in=entity_ids) |
            Q(noticeadditionalrecipient__user=user)
        ).distinct()
    
    def with_read_status(self, user):
        return self.annotate(
            was_read=Exists(
                ReadAcknowledgment.objects.filter(
                    notice=OuterRef('pk'),
                    user=user
                )
            )
        )

class NoticeManager(models.Manager):
    def get_queryset(self):
        return PublishedNoticeQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)

# Model
class Notice(models.Model):
    objects = NoticeManager()
    
    # Usage: Notice.objects.published().for_user(request.user)
```

### Service Layer Architecture

**Extract business logic from views into services:**

```python
# apps/notices/services.py
from dataclasses import dataclass
from typing import List

@dataclass
class NoticeCreationData:
    title: str
    content: str
    recipient_ids: List[int]
    created_by: User

class NoticeService:
    @staticmethod
    def create_notice(data: NoticeCreationData) -> Notice:
        """Create notice with recipients atomically."""
        with transaction.atomic():
            notice = Notice.objects.create(
                title=data.title,
                content=data.content,
                created_by=data.created_by
            )
            
            # Bulk create recipients
            recipients = [
                NoticeRecipient(notice=notice, recipient_id=rid)
                for rid in data.recipient_ids
            ]
            NoticeRecipient.objects.bulk_create(recipients)
            
            # Send notifications
            NoticeService._send_notifications(notice)
            
            return notice
    
    @staticmethod
    def _send_notifications(notice: Notice):
        # Notification logic here
        pass

# Usage in view
def create_notice_view(request):
    data = NoticeCreationData(
        title=form.cleaned_data['title'],
        content=form.cleaned_data['content'],
        recipient_ids=form.cleaned_data['recipients'],
        created_by=request.user
    )
    notice = NoticeService.create_notice(data)
```

### Dataclasses for DTOs

**Use dataclasses for data transfer objects:**

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class NoticeDTO:
    id: int
    title: str
    content: str
    status: str
    created_at: datetime
    was_read: bool = False
    recipient_count: int = 0
    
    @classmethod
    def from_model(cls, notice: Notice, user: User) -> 'NoticeDTO':
        return cls(
            id=notice.id,
            title=notice.title,
            content=notice.content,
            status=notice.status,
            created_at=notice.created_at,
            was_read=notice.is_read_by(user),
            recipient_count=notice.recipients.count()
        )
```

### Signal Handlers

**Organize signals properly:**

```python
# apps/notices/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Notice)
def notice_post_save(sender, instance, created, **kwargs):
    """Handle notice creation/update."""
    if created:
        logger.info(f"Notice created: {instance.id} by {instance.created_by}")
        # Send notifications
        from .tasks import send_notice_notifications
        send_notice_notifications.delay(instance.id)

@receiver(pre_delete, sender=Notice)
def notice_pre_delete(sender, instance, **kwargs):
    """Prevent deletion of published notices."""
    if instance.status == Notice.Status.PUBLISHED:
        from django.core.exceptions import ValidationError
        raise ValidationError("Cannot delete published notices")

# apps/notices/apps.py
class NoticesConfig(AppConfig):
    name = 'apps.notices'
    
    def ready(self):
        import apps.notices.signals  # Register signals
```

### Mixins for Reusable Logic

**Create mixins for common patterns:**

```python
# apps/core/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

class UserFilterMixin:
    """Filter queryset for current user."""
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.for_user(self.request.user)

class AuditMixin(models.Model):
    """Add created/modified tracking."""
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='+', on_delete=models.PROTECT)
    
    class Meta:
        abstract = True

class SoftDeleteMixin(models.Model):
    """Soft delete functionality."""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def hard_delete(self):
        super().delete()

# Usage
class Notice(AuditMixin, SoftDeleteMixin):
    title = models.CharField(max_length=255)
    # ...
```

See `references/advanced_patterns.md` for more patterns.

## Code Quality Tools

### Ruff (Modern Linter/Formatter)

**Installation:**
```bash
pipenv install --dev ruff
```

**Configuration: `ruff.toml`**
```toml
target-version = "py311"
line-length = 100

[lint]
select = ["E", "F", "I", "N", "W", "B", "Q"]
ignore = ["E501"]  # Line too long (handled by formatter)

[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports
"tests/*.py" = ["S101"]  # Use of assert

[format]
quote-style = "double"
indent-style = "space"
```

**Usage:**
```bash
ruff check .          # Lint
ruff check --fix .    # Auto-fix
ruff format .         # Format
```

### Mypy (Type Checking)

**Configuration: `mypy.ini`**
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
plugins = mypy_django_plugin.main

[mypy.plugins.django-stubs]
django_settings_module = config.settings

[mypy-tests.*]
disallow_untyped_defs = False
```

**Usage:**
```bash
pipenv install --dev mypy django-stubs
mypy apps/
```

### Pre-commit Hooks

**Configuration: `.pre-commit-config.yaml`**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [django-stubs]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pipenv run pytest
        language: system
        pass_filenames: false
        always_run: true
```

**Setup:**
```bash
pipenv install --dev pre-commit
pre-commit install
```

### Logging Best Practices

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# Usage in code
import logging
logger = logging.getLogger(__name__)

def create_notice(request):
    logger.info(f"Creating notice for user {request.user.id}")
    try:
        # Logic
        logger.debug(f"Notice data: {data}")
    except Exception as e:
        logger.error(f"Failed to create notice: {e}", exc_info=True)
```

See `references/code_quality.md` and example configs in `assets/`.

## Flake8

**Ignore warnings when justified:**
```python
subprocess.call(cmd, shell=True)  # noqa: B605 B607
```

Use specific codes, not `# noqa` alone.

## Resources

**Core References:**
- `references/ajax_patterns.md` - Detailed Choices.js integration examples
- `references/query_optimization.md` - Complex query examples, caching patterns
- `references/testing_patterns.md` - Comprehensive pytest examples with factory-boy
- `references/advanced_patterns.md` - Service Layer, Repository Pattern, Custom Managers
- `references/code_quality.md` - Ruff, Mypy, Pre-commit hooks setup

**Ready-to-use Code:**
- `assets/choices_mixin.py` - Ready-to-use ChoicesMixin
- `assets/ruff.toml` - Example Ruff configuration
- `assets/mypy.ini` - Example Mypy configuration
- `assets/.pre-commit-config.yaml` - Pre-commit hooks setup
- `assets/factories.py` - Example factory-boy factories

## What's Included

**Core Principles:**
- English docstrings + type hints
- `gettext_lazy as _` for translations
- Query optimization patterns
- Testing with pytest + factory-boy

**Advanced Patterns:**
- Custom QuerySet managers
- Service layer architecture
- Dataclasses for DTOs
- Signal handlers
- Mixins for reusable logic

**Code Quality:**
- Ruff configuration
- Mypy type checking
- Pre-commit hooks
- Logging best practices

**Testing:**
- Pytest + factory-boy setup
- Comprehensive test examples
- Freezegun for time-based tests

## Updates

**Version 2.0** (December 2025)
- Added Advanced Patterns section
- Added Code Quality tools (Ruff, Mypy)
- Extended Testing with factory-boy and freezegun
- Added Installation guide and Quick Start
- Merged with AJAX patterns and query optimization

**Based on:**
- Django 4.x/5.x best practices
- Python 3.11+ features
- Modern tooling (Ruff, Mypy, Pytest)
- Real-world production patterns from Karol's projects
