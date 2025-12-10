# Query Optimization Patterns

## N+1 Problem - Identyfikacja i Rozwiązanie

### Problem: N+1 Queries

```python
# ❌ BAD - generuje N+1 queries
notices = Notice.objects.filter(status='published')
for notice in notices:
    print(notice.created_by.username)  # Query za każdym razem!
    print(notice.recipient_count)       # Query za każdym razem!
```

**Jak wykryć:**
```python
from django.db import connection
from django.test.utils import override_settings

@override_settings(DEBUG=True)
def test_view():
    # Call view
    response = client.get('/notices/')
    
    # Check how many queries were executed
    print(len(connection.queries))
    for query in connection.queries:
        print(query['sql'])
```

### Rozwiązanie: select_related()

**Dla ForeignKey (1-to-1 relationships):**

```python
# ✅ GOOD - single JOIN query
notices = Notice.objects.select_related('created_by').filter(status='published')
for notice in notices:
    print(notice.created_by.username)  # Brak dodatkowych queries!
```

**Multiple levels:**

```python
# Entity -> User -> Profile
recipients = (
    AdditionalRecipient.objects
    .select_related('user', 'user__profile', 'notice')
    .filter(notice__status='published')
)
```

### Rozwiązanie: prefetch_related()

**Dla ManyToMany i reverse ForeignKey:**

```python
# ✅ GOOD - 2 queries total (1 base + 1 prefetch)
notices = Notice.objects.prefetch_related('recipients').filter(status='published')
for notice in notices:
    for recipient in notice.recipients.all():  # Brak dodatkowych queries!
        print(recipient.name)
```

**Complex prefetch:**

```python
from django.db.models import Prefetch

# Prefetch z filtrowaniem
active_recipients = AdditionalRecipient.objects.filter(is_active=True)

notices = Notice.objects.prefetch_related(
    Prefetch('additional_recipients', queryset=active_recipients)
).filter(status='published')
```

## only() i defer() - Optymalizacja pól

### only() - Pobierz TYLKO wybrane pola

```python
# ❌ Pobiera wszystkie kolumny (może być duży content_html)
recipients = AdditionalRecipient.objects.all()

# ✅ Pobierz tylko to czego potrzebujesz
recipients = (
    AdditionalRecipient.objects
    .only('id', 'first_name', 'last_name', 'email')
    .order_by('last_name')
)
```

**Z select_related:**

```python
recipients = (
    AdditionalRecipient.objects
    .select_related('notice')
    .only(
        'id', 'first_name', 'last_name', 'email',
        'notice__id', 'notice__title'  # Pola z related model
    )
)
```

### defer() - Exclude heavy fields

```python
# Load everything EXCEPT content_html
notices = Notice.objects.defer('content_html').filter(status='published')
```

## Bulk Operations

### Bulk Create

```python
# ❌ N queries
for i in range(100):
    Recipient.objects.create(name=f"User {i}")

# ✅ 1 query
recipients = [
    Recipient(name=f"User {i}")
    for i in range(100)
]
Recipient.objects.bulk_create(recipients, batch_size=50)
```

### Bulk Update

```python
# ❌ N queries
recipients = Recipient.objects.filter(is_active=True)
for r in recipients:
    r.last_seen = now()
    r.save()

# ✅ 1 query
Recipient.objects.filter(is_active=True).update(last_seen=now())

# ✅ Bulk update z różnymi wartościami (Django 4.2+)
recipients = Recipient.objects.filter(is_active=True)
for r in recipients:
    r.points += 10
Recipient.objects.bulk_update(recipients, ['points'], batch_size=50)
```

## Annotate & Aggregate

### Count related objects

```python
from django.db.models import Count, Q

# Policz recipients dla każdego notice
notices = Notice.objects.annotate(
    recipient_count=Count('recipients')
).filter(recipient_count__gt=0)

# Multiple counts z filtrowaniem
notices = Notice.objects.annotate(
    total_recipients=Count('recipients'),
    active_recipients=Count('recipients', filter=Q(recipients__is_active=True)),
    read_count=Count('read_acknowledgments')
)
```

### Conditional aggregation

```python
from django.db.models import Sum, Case, When, IntegerField

notices = Notice.objects.annotate(
    priority_count=Sum(
        Case(
            When(recipients__priority='high', then=1),
            default=0,
            output_field=IntegerField()
        )
    )
)
```

## Complex Filtering

### Multiple table lookups

```python
# User otrzymuje notice przez:
# 1. Bezpośrednio (NoticeRecipient -> Recipient)
# 2. Przez grupę (NoticeRecipientGroup -> RecipientGroup -> RecipientGroupRecipient)
# 3. Jako dodatkowy odbiorca (NoticeAdditionalRecipient)

from django.db.models import Q

def get_user_notices(user):
    # Pobierz entity_ids użytkownika (funkcja pomocnicza)
    entity_ids = user_role_entity_ids(user)
    
    notices = Notice.objects.filter(
        Q(status=Notice.Status.PUBLISHED) &
        (
            # Przypadek 1: Bezpośredni recipient przez entity
            Q(noticerecipient__recipient_id__in=entity_ids) |
            
            # Przypadek 2: Grupa przez entity
            Q(
                noticerecipientgroup__recipient_group__in=
                RecipientGroup.objects.filter(
                    recipientgrouprecipient__recipient_id__in=entity_ids
                )
            ) |
            
            # Przypadek 3: Grupa przez user
            Q(
                noticerecipientgroup__recipient_group__in=
                RecipientGroup.objects.filter(
                    recipientgroupadditionalrecipient__user=user
                )
            ) |
            
            # Przypadek 4: Dodatkowy odbiorca
            Q(noticeadditionalrecipient__user=user)
        )
    ).distinct()  # Ważne! Usuń duplikaty
    
    return notices
```

### Unikaj duplikatów z distinct()

```python
# ❌ Bez distinct() - może zwrócić duplikaty
notices = Notice.objects.filter(
    Q(recipients__name__icontains='test') |
    Q(groups__name__icontains='test')
)

# ✅ Z distinct()
notices = Notice.objects.filter(
    Q(recipients__name__icontains='test') |
    Q(groups__name__icontains='test')
).distinct()

# ✅ distinct() z order_by - PostgreSQL wymaga
notices = Notice.objects.filter(...).order_by('id').distinct('id')
```

## Caching Patterns

### Query result caching

```python
from django.core.cache import cache

def get_recipients_for_notice(notice_id):
    cache_key = f'recipients_notice_{notice_id}'
    recipients = cache.get(cache_key)
    
    if recipients is None:
        recipients = list(
            AdditionalRecipient.objects
            .filter(notice_id=notice_id)
            .select_related('user')
            .only('id', 'first_name', 'last_name', 'email')
        )
        cache.set(cache_key, recipients, timeout=300)  # 5 minut
    
    return recipients
```

### Template fragment caching

```html
{% load cache %}

{% cache 600 notice_recipients notice.id %}
    <ul>
    {% for recipient in notice.recipients.all %}
        <li>{{ recipient.name }}</li>
    {% endfor %}
    </ul>
{% endcache %}
```

### Invalidate cache on update

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=AdditionalRecipient)
def invalidate_recipient_cache(sender, instance, **kwargs):
    cache_key = f'recipients_notice_{instance.notice_id}'
    cache.delete(cache_key)
```

## Database Indexes

**W models.py:**

```python
class Notice(models.Model):
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20)
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            # Single column
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            
            # Composite index (kolejność ma znaczenie!)
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['status', '-created_at']),  # DESC
        ]
        
        # Unique together
        unique_together = [('notice', 'recipient')]
```

**Migracja:**

```python
# python manage.py makemigrations --name add_notice_indexes
```

## Query Performance Tools

### Django Debug Toolbar

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # ...
]

INTERNAL_IPS = ['127.0.0.1']
```

### django-silk (production profiling)

```python
INSTALLED_APPS = [
    'silk',
]

MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
]

# urls.py
urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
```

### Manual query logging

```python
import logging
from django.db import connection

logger = logging.getLogger(__name__)

def log_queries(func):
    def wrapper(*args, **kwargs):
        initial_queries = len(connection.queries)
        result = func(*args, **kwargs)
        final_queries = len(connection.queries)
        
        query_count = final_queries - initial_queries
        logger.info(f"{func.__name__} executed {query_count} queries")
        
        return result
    return wrapper

@log_queries
def get_notices_for_user(user):
    return Notice.objects.filter(...)
```

## Best Practices Summary

1. **Always use select_related() for ForeignKey**
2. **Always use prefetch_related() for M2M**
3. **Use only() when you don't need all fields**
4. **Use bulk operations for multiple creates/updates**
5. **Add distinct() when joining across M2M**
6. **Cache expensive queries**
7. **Add indexes for frequently filtered/ordered fields**
8. **Profile with django-debug-toolbar in development**
9. **Monitor queries in production with django-silk**
10. **Test query count in pytest**

## Query Count Testing

```python
import pytest
from django.test.utils import override_settings

@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_notice_list_query_count(client, notices):
    from django.db import connection
    
    # Reset queries
    connection.queries_log.clear()
    
    response = client.get('/notices/')
    
    # Assert reasonable query count
    query_count = len(connection.queries)
    assert query_count <= 5, f"Too many queries: {query_count}"
```
