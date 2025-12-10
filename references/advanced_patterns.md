# Advanced Django Patterns

## Custom QuerySet Managers

Custom managers encapsulate complex queries and make them reusable across your codebase.

### Basic Pattern

```python
from django.db import models
from django.db.models import Q, Exists, OuterRef

class NoticeQuerySet(models.QuerySet):
    """Custom QuerySet for Notice model."""
    
    def published(self):
        """Return only published notices."""
        return self.filter(status=Notice.Status.PUBLISHED)
    
    def draft(self):
        """Return only draft notices."""
        return self.filter(status=Notice.Status.DRAFT)
    
    def for_user(self, user):
        """
        Return notices visible to user.
        Handles all 4 recipient types.
        """
        entity_ids = user_role_entity_ids(user)
        
        return self.filter(
            Q(noticerecipient__recipient_id__in=entity_ids) |
            Q(noticerecipientgroup__recipient_group__in=
                RecipientGroup.objects.filter(
                    recipientgrouprecipient__recipient_id__in=entity_ids
                )
            ) |
            Q(noticerecipientgroup__recipient_group__in=
                RecipientGroup.objects.filter(
                    recipientgroupadditionalrecipient__user=user
                )
            ) |
            Q(noticeadditionalrecipient__user=user)
        ).distinct()
    
    def with_read_status(self, user):
        """Annotate with read status for user."""
        return self.annotate(
            was_read=Exists(
                ReadAcknowledgment.objects.filter(
                    notice=OuterRef('pk'),
                    user=user
                )
            )
        )
    
    def with_recipient_count(self):
        """Annotate with recipient count."""
        return self.annotate(
            recipient_count=Count('recipients')
        )
    
    def active_in_date_range(self, start_date=None, end_date=None):
        """Filter by date range."""
        qs = self
        if start_date:
            qs = qs.filter(start_date__gte=start_date)
        if end_date:
            qs = qs.filter(end_date__lte=end_date)
        return qs


class NoticeManager(models.Manager):
    """Custom Manager for Notice model."""
    
    def get_queryset(self):
        """Return custom QuerySet."""
        return NoticeQuerySet(self.model, using=self._db)
    
    # Proxy methods for convenience
    def published(self):
        return self.get_queryset().published()
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)
    
    def with_read_status(self, user):
        return self.get_queryset().with_read_status(user)


# In model
class Notice(models.Model):
    # Fields...
    
    objects = NoticeManager()
    
    class Meta:
        db_table = 'notices'
```

**Usage:**
```python
# Chain methods
notices = (
    Notice.objects
    .published()
    .for_user(request.user)
    .with_read_status(request.user)
    .with_recipient_count()
    .select_related('created_by')
    .order_by('-created_at')
)

# In views
def notice_list(request):
    notices = Notice.objects.published().for_user(request.user)
    return render(request, 'notices/list.html', {'notices': notices})
```

## Service Layer Architecture

Service layer separates business logic from views, making code more testable and reusable.

### Basic Service

```python
# apps/notices/services.py
from dataclasses import dataclass
from typing import List, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


@dataclass
class NoticeCreationData:
    """DTO for notice creation."""
    title: str
    content: str
    status: str
    start_date: date
    end_date: Optional[date]
    recipient_ids: List[int]
    recipient_group_ids: List[int]
    additional_recipient_ids: List[int]
    created_by: User


class NoticeService:
    """Service for Notice operations."""
    
    @staticmethod
    @transaction.atomic
    def create_notice(data: NoticeCreationData) -> Notice:
        """
        Create notice with all recipients.
        
        This is atomic - if any step fails, everything rolls back.
        """
        # Validate
        NoticeService._validate_creation_data(data)
        
        # Create notice
        notice = Notice.objects.create(
            title=data.title,
            content=data.content,
            status=data.status,
            start_date=data.start_date,
            end_date=data.end_date,
            created_by=data.created_by
        )
        
        logger.info(f"Notice {notice.id} created by {data.created_by.id}")
        
        # Add recipients
        NoticeService._add_recipients(notice, data)
        
        # Send notifications if published
        if data.status == Notice.Status.PUBLISHED:
            NoticeService._send_notifications(notice)
        
        return notice
    
    @staticmethod
    def _validate_creation_data(data: NoticeCreationData):
        """Validate notice creation data."""
        if data.end_date and data.end_date < data.start_date:
            raise ValidationError("End date must be after start date")
        
        if not any([
            data.recipient_ids,
            data.recipient_group_ids,
            data.additional_recipient_ids
        ]):
            raise ValidationError("At least one recipient is required")
    
    @staticmethod
    def _add_recipients(notice: Notice, data: NoticeCreationData):
        """Add all recipients to notice."""
        # Direct recipients
        if data.recipient_ids:
            recipients = [
                NoticeRecipient(notice=notice, recipient_id=rid)
                for rid in data.recipient_ids
            ]
            NoticeRecipient.objects.bulk_create(recipients)
        
        # Recipient groups
        if data.recipient_group_ids:
            groups = [
                NoticeRecipientGroup(notice=notice, recipient_group_id=gid)
                for gid in data.recipient_group_ids
            ]
            NoticeRecipientGroup.objects.bulk_create(groups)
        
        # Additional recipients
        if data.additional_recipient_ids:
            additional = [
                NoticeAdditionalRecipient(notice=notice, user_id=uid)
                for uid in data.additional_recipient_ids
            ]
            NoticeAdditionalRecipient.objects.bulk_create(additional)
    
    @staticmethod
    def _send_notifications(notice: Notice):
        """Send notifications to recipients."""
        from .tasks import send_notice_notifications
        send_notice_notifications.delay(notice.id)
    
    @staticmethod
    @transaction.atomic
    def mark_as_read(notice: Notice, user: User) -> ReadAcknowledgment:
        """Mark notice as read by user."""
        ack, created = ReadAcknowledgment.objects.get_or_create(
            notice=notice,
            user=user,
            defaults={'read_at': timezone.now()}
        )
        
        if created:
            logger.debug(f"User {user.id} read notice {notice.id}")
        
        return ack
    
    @staticmethod
    def get_unread_count(user: User) -> int:
        """Get unread notice count for user."""
        return (
            Notice.objects
            .published()
            .for_user(user)
            .exclude(
                readacknowledgment__user=user
            )
            .count()
        )
```

**Usage in views:**
```python
from apps.notices.services import NoticeService, NoticeCreationData

def create_notice_view(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            data = NoticeCreationData(
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                status=form.cleaned_data['status'],
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data.get('end_date'),
                recipient_ids=form.cleaned_data['recipients'],
                recipient_group_ids=form.cleaned_data['groups'],
                additional_recipient_ids=form.cleaned_data['additional'],
                created_by=request.user
            )
            
            try:
                notice = NoticeService.create_notice(data)
                messages.success(request, _("Notice created successfully"))
                return redirect('notices:detail', pk=notice.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = NoticeForm()
    
    return render(request, 'notices/create.html', {'form': form})
```

## Repository Pattern

Repository pattern provides an abstraction layer between data access and business logic.

```python
# apps/notices/repositories.py
from typing import List, Optional
from django.db.models import QuerySet


class NoticeRepository:
    """Repository for Notice data access."""
    
    @staticmethod
    def get_by_id(notice_id: int) -> Optional[Notice]:
        """Get notice by ID."""
        try:
            return Notice.objects.select_related('created_by').get(id=notice_id)
        except Notice.DoesNotExist:
            return None
    
    @staticmethod
    def get_published_for_user(user: User) -> QuerySet[Notice]:
        """Get published notices for user."""
        return (
            Notice.objects
            .published()
            .for_user(user)
            .with_read_status(user)
            .select_related('created_by')
            .prefetch_related('recipients')
            .order_by('-created_at')
        )
    
    @staticmethod
    def get_unread_for_user(user: User) -> QuerySet[Notice]:
        """Get unread notices for user."""
        return (
            NoticeRepository.get_published_for_user(user)
            .filter(was_read=False)
        )
    
    @staticmethod
    def search(query: str, user: User) -> QuerySet[Notice]:
        """Search notices by title/content."""
        return (
            Notice.objects
            .published()
            .for_user(user)
            .filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )
            .distinct()
        )
    
    @staticmethod
    def bulk_create(notices: List[Notice]) -> List[Notice]:
        """Bulk create notices."""
        return Notice.objects.bulk_create(notices, batch_size=100)


# Usage in service
class NoticeService:
    @staticmethod
    def get_user_dashboard(user: User) -> dict:
        """Get dashboard data for user."""
        return {
            'unread_notices': NoticeRepository.get_unread_for_user(user)[:5],
            'recent_notices': NoticeRepository.get_published_for_user(user)[:10],
            'unread_count': NoticeRepository.get_unread_for_user(user).count(),
        }
```

## Dataclasses for DTOs

Use dataclasses for type-safe data transfer between layers.

```python
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime, date


@dataclass
class RecipientDTO:
    """DTO for recipient data."""
    id: int
    name: str
    email: str
    type: str  # 'direct', 'group', 'additional'


@dataclass
class NoticeDTO:
    """DTO for notice display."""
    id: int
    title: str
    content: str
    status: str
    start_date: date
    end_date: Optional[date]
    created_at: datetime
    created_by_name: str
    was_read: bool = False
    is_favourite: bool = False
    recipient_count: int = 0
    recipients: List[RecipientDTO] = field(default_factory=list)
    
    @classmethod
    def from_model(cls, notice: Notice, user: User) -> 'NoticeDTO':
        """Create DTO from model instance."""
        return cls(
            id=notice.id,
            title=notice.title,
            content=notice.content,
            status=notice.status,
            start_date=notice.start_date,
            end_date=notice.end_date,
            created_at=notice.created_at,
            created_by_name=notice.created_by.get_full_name(),
            was_read=getattr(notice, 'was_read', False),
            is_favourite=getattr(notice, 'is_favourite', False),
            recipient_count=notice.recipients.count(),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)


# Usage
def notice_detail_api(request, notice_id):
    notice = Notice.objects.published().with_read_status(request.user).get(id=notice_id)
    dto = NoticeDTO.from_model(notice, request.user)
    return JsonResponse(dto.to_dict())
```

## Signal Handlers

Organize signals in dedicated files and register them properly.

```python
# apps/notices/signals.py
from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notice)
def notice_post_save(sender, instance, created, **kwargs):
    """Handle notice creation/update."""
    if created:
        logger.info(f"Notice {instance.id} created by {instance.created_by.id}")
        
        # Send notifications asynchronously
        if instance.status == Notice.Status.PUBLISHED:
            from .tasks import send_notice_notifications
            send_notice_notifications.delay(instance.id)
    else:
        logger.debug(f"Notice {instance.id} updated")
        
        # Invalidate cache
        cache.delete(f'notice_{instance.id}')


@receiver(pre_save, sender=Notice)
def notice_pre_save(sender, instance, **kwargs):
    """Validate before save."""
    if instance.end_date and instance.end_date < instance.start_date:
        from django.core.exceptions import ValidationError
        raise ValidationError("End date must be after start date")


@receiver(pre_delete, sender=Notice)
def notice_pre_delete(sender, instance, **kwargs):
    """Prevent deletion of published notices."""
    if instance.status == Notice.Status.PUBLISHED:
        from django.core.exceptions import ValidationError
        raise ValidationError("Cannot delete published notices")
    
    logger.warning(f"Notice {instance.id} is being deleted")


@receiver(post_delete, sender=Notice)
def notice_post_delete(sender, instance, **kwargs):
    """Cleanup after deletion."""
    cache.delete(f'notice_{instance.id}')
    logger.info(f"Notice {instance.id} deleted")


# apps/notices/apps.py
from django.apps import AppConfig


class NoticesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notices'
    
    def ready(self):
        """Register signals when app is ready."""
        import apps.notices.signals  # noqa: F401
```

## Mixins for Reusable Logic

Create abstract base classes with common functionality.

```python
# apps/core/mixins.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class TimestampMixin(models.Model):
    """Add created/modified timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class UserTrackingMixin(models.Model):
    """Track who created/modified."""
    created_by = models.ForeignKey(
        User,
        related_name='%(class)s_created',
        on_delete=models.PROTECT,
        verbose_name=_("Created by")
    )
    modified_by = models.ForeignKey(
        User,
        related_name='%(class)s_modified',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Modified by")
    )
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Soft delete functionality."""
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        related_name='%(class)s_deleted',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        abstract = True
    
    def delete(self, user=None, *args, **kwargs):
        """Soft delete."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()
    
    def hard_delete(self):
        """Permanently delete."""
        super().delete()
    
    def restore(self):
        """Restore soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()


class PublishableMixin(models.Model):
    """Add publish/unpublish functionality."""
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def publish(self):
        """Publish the object."""
        if not self.is_published:
            self.is_published = True
            self.published_at = timezone.now()
            self.save()
    
    def unpublish(self):
        """Unpublish the object."""
        self.is_published = False
        self.save()


# Usage
class Notice(
    TimestampMixin,
    UserTrackingMixin,
    SoftDeleteMixin,
    PublishableMixin
):
    """Notice model with all mixins."""
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    def save(self, *args, **kwargs):
        # Custom save logic
        super().save(*args, **kwargs)

# In views
def delete_notice(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    notice.delete(user=request.user)  # Soft delete with user tracking
    return redirect('notices:list')
```

## Best Practices

1. **Keep services focused** - one service per domain model
2. **Use dataclasses for DTOs** - type safety and clarity
3. **Repositories for data access** - easier to test and mock
4. **Signals for side effects** - keep main logic clean
5. **Mixins for cross-cutting concerns** - timestamps, soft delete, etc.
6. **Always use transactions** - especially in services
7. **Log important operations** - helps with debugging
8. **Validate early** - fail fast with clear errors
