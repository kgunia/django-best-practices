# Django Testing with Pytest

## Setup

**Install:**
```bash
pipenv install --dev pytest pytest-django pytest-cov
```

**Configure: `pytest.ini`**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = 
    --ds=config.settings.test
    --reuse-db
    --nomigrations
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
```

**Test settings: `config/settings/test.py`**
```python
from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Szybsze hashe dla testów
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Wyłącz debug
DEBUG = False
```

## Basic Test Structure

```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestNoticeModel:
    """Test Notice model functionality"""
    
    @pytest.fixture
    def user(self):
        """Create test user"""
        return User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def notice(self, user):
        """Create test notice"""
        return Notice.objects.create(
            title='Test Notice',
            content='Test content',
            status=Notice.Status.DRAFT,
            created_by=user
        )
    
    def test_notice_creation(self, notice):
        """Test notice is created correctly"""
        assert notice.title == 'Test Notice'
        assert notice.status == Notice.Status.DRAFT
        assert notice.created_by is not None
    
    def test_notice_str(self, notice):
        """Test notice string representation"""
        assert str(notice) == 'Test Notice'
```

## Comprehensive Fixtures

### Fixture Scope

```python
# Function scope (default) - new for each test
@pytest.fixture
def user():
    return User.objects.create_user(username='test')

# Class scope - shared within test class
@pytest.fixture(scope='class')
def shared_user():
    return User.objects.create_user(username='shared')

# Module scope - shared within file
@pytest.fixture(scope='module')
def module_user():
    return User.objects.create_user(username='module')

# Session scope - shared across all tests
@pytest.fixture(scope='session')
def session_user():
    return User.objects.create_user(username='session')
```

### Complex Fixtures

```python
@pytest.fixture
def setup_notice_recipients(db):
    """Create complete notice with all recipient types"""
    # Users
    user1 = User.objects.create_user(username='user1', email='user1@test.com')
    user2 = User.objects.create_user(username='user2', email='user2@test.com')
    creator = User.objects.create_user(username='creator', email='creator@test.com')
    
    # Entities
    entity1 = Entity.objects.create(name='Entity 1')
    entity2 = Entity.objects.create(name='Entity 2')
    
    # Recipient Group
    recipient_group = RecipientGroup.objects.create(
        name='Test Group',
        created_by=creator
    )
    RecipientGroupRecipient.objects.create(
        recipient_group=recipient_group,
        recipient=entity1
    )
    
    # Notice
    notice = Notice.objects.create(
        title='Test Notice',
        content='Content',
        status=Notice.Status.PUBLISHED,
        created_by=creator
    )
    
    # Direct recipient
    NoticeRecipient.objects.create(
        notice=notice,
        recipient=entity2
    )
    
    # Group recipient
    NoticeRecipientGroup.objects.create(
        notice=notice,
        recipient_group=recipient_group
    )
    
    # Additional recipient
    NoticeAdditionalRecipient.objects.create(
        notice=notice,
        user=user2
    )
    
    return {
        'notice': notice,
        'user1': user1,
        'user2': user2,
        'creator': creator,
        'entity1': entity1,
        'entity2': entity2,
        'recipient_group': recipient_group,
    }
```

### Parametrized Fixtures

```python
@pytest.fixture(params=[
    Notice.Status.DRAFT,
    Notice.Status.PUBLISHED,
    Notice.Status.ARCHIVED,
])
def notice_with_status(request, user):
    """Create notice with different statuses"""
    return Notice.objects.create(
        title='Test Notice',
        status=request.param,
        created_by=user
    )

def test_notice_display(notice_with_status):
    """Test runs 3 times with different statuses"""
    assert notice_with_status.status in Notice.Status.values
```

## Testing Views

### Function-Based Views

```python
@pytest.mark.django_db
class TestNoticeListView:
    def test_list_view_success(self, client, notice):
        """Test notice list view returns 200"""
        response = client.get(reverse('notices:list'))
        assert response.status_code == 200
        assert notice.title in str(response.content)
    
    def test_list_view_requires_login(self, client):
        """Test login required"""
        response = client.get(reverse('notices:list'))
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_list_view_with_auth(self, client, user, notice):
        """Test with authenticated user"""
        client.force_login(user)
        response = client.get(reverse('notices:list'))
        assert response.status_code == 200
        assert 'notices' in response.context
```

### Class-Based Views

```python
@pytest.mark.django_db
class TestNoticeDetailView:
    @pytest.fixture
    def detail_url(self, notice):
        return reverse('notices:detail', kwargs={'pk': notice.pk})
    
    def test_detail_view(self, client, user, notice, detail_url):
        client.force_login(user)
        response = client.get(detail_url)
        
        assert response.status_code == 200
        assert response.context['notice'] == notice
    
    def test_404_for_nonexistent(self, client, user):
        client.force_login(user)
        response = client.get(reverse('notices:detail', kwargs={'pk': 9999}))
        assert response.status_code == 404
```

## Testing Forms

```python
@pytest.mark.django_db
class TestNoticeForm:
    def test_form_valid_data(self, user):
        """Test form with valid data"""
        form_data = {
            'title': 'New Notice',
            'content': 'Content here',
            'status': Notice.Status.DRAFT,
        }
        form = NoticeForm(data=form_data)
        assert form.is_valid()
    
    def test_form_missing_required_field(self):
        """Test form validation with missing field"""
        form_data = {
            'content': 'Content here',
            # Missing title
        }
        form = NoticeForm(data=form_data)
        assert not form.is_valid()
        assert 'title' in form.errors
    
    def test_form_with_instance(self, notice):
        """Test form with existing instance"""
        form = NoticeForm(instance=notice)
        assert form.initial['title'] == notice.title
    
    def test_form_save(self, user):
        """Test form save creates object"""
        form_data = {
            'title': 'New Notice',
            'content': 'Content here',
            'status': Notice.Status.DRAFT,
        }
        form = NoticeForm(data=form_data)
        assert form.is_valid()
        
        notice = form.save(commit=False)
        notice.created_by = user
        notice.save()
        
        assert Notice.objects.filter(title='New Notice').exists()
```

## Testing QuerySets

```python
@pytest.mark.django_db
class TestNoticeQueryset:
    def test_published_notices(self, user):
        """Test published notices queryset"""
        # Create notices with different statuses
        Notice.objects.create(title='Draft', status=Notice.Status.DRAFT, created_by=user)
        published = Notice.objects.create(
            title='Published', 
            status=Notice.Status.PUBLISHED, 
            created_by=user
        )
        Notice.objects.create(title='Archived', status=Notice.Status.ARCHIVED, created_by=user)
        
        # Test queryset
        published_notices = Notice.objects.filter(status=Notice.Status.PUBLISHED)
        assert published_notices.count() == 1
        assert published_notices.first() == published
    
    def test_user_notices_all_recipient_types(self, setup_notice_recipients):
        """Test complex filtering - all 4 recipient types"""
        data = setup_notice_recipients
        
        # Mock function (replace with actual)
        def user_role_entity_ids(user):
            return [data['entity1'].id, data['entity2'].id]
        
        # Get notices for user1 (through entity1 in group)
        notices = get_user_notices(data['user1'])
        assert data['notice'] in notices
        
        # Get notices for user2 (as additional recipient)
        notices = get_user_notices(data['user2'])
        assert data['notice'] in notices
```

## Testing Signals

```python
@pytest.mark.django_db
class TestNoticeSignals:
    def test_post_save_signal_creates_audit_log(self, user):
        """Test signal creates audit log on save"""
        notice = Notice.objects.create(
            title='Test',
            created_by=user
        )
        
        # Check audit log was created
        assert AuditLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Notice),
            object_id=notice.id
        ).exists()
    
    def test_pre_delete_signal_prevents_deletion(self, notice):
        """Test signal prevents deletion of published notices"""
        notice.status = Notice.Status.PUBLISHED
        notice.save()
        
        with pytest.raises(ValidationError):
            notice.delete()
```

## Testing Permissions

```python
@pytest.mark.django_db
class TestNoticePermissions:
    @pytest.fixture
    def admin_user(self):
        user = User.objects.create_user(username='admin', password='pass')
        user.is_staff = True
        user.save()
        return user
    
    def test_admin_can_delete_notice(self, client, admin_user, notice):
        """Test admin has delete permission"""
        client.force_login(admin_user)
        response = client.post(
            reverse('notices:delete', kwargs={'pk': notice.pk})
        )
        assert response.status_code == 302
        assert not Notice.objects.filter(pk=notice.pk).exists()
    
    def test_regular_user_cannot_delete_notice(self, client, user, notice):
        """Test regular user lacks delete permission"""
        client.force_login(user)
        response = client.post(
            reverse('notices:delete', kwargs={'pk': notice.pk})
        )
        assert response.status_code == 403
        assert Notice.objects.filter(pk=notice.pk).exists()
```

## Mocking

```python
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestExternalAPICalls:
    @patch('apps.notices.services.send_email')
    def test_notice_creation_sends_email(self, mock_send_email, user):
        """Test email is sent on notice creation"""
        notice = Notice.objects.create(
            title='Test',
            created_by=user
        )
        
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert 'Test' in call_args[0][0]  # Title in subject
    
    @patch('requests.post')
    def test_external_api_call(self, mock_post, notice):
        """Test external API integration"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response
        
        result = send_to_external_api(notice)
        
        assert result['success'] is True
        mock_post.assert_called_once()
```

## Performance Testing

```python
from django.test.utils import override_settings

@pytest.mark.django_db
@override_settings(DEBUG=True)
class TestQueryPerformance:
    def test_notice_list_query_count(self, client, user):
        """Test notice list doesn't have N+1 queries"""
        from django.db import connection
        
        # Create test data
        for i in range(10):
            Notice.objects.create(
                title=f'Notice {i}',
                created_by=user
            )
        
        # Clear queries
        connection.queries_log.clear()
        
        client.force_login(user)
        response = client.get(reverse('notices:list'))
        
        # Assert reasonable query count
        query_count = len(connection.queries)
        assert query_count <= 5, f"Too many queries: {query_count}"
```

## Parametrize Tests

```python
@pytest.mark.django_db
class TestNoticeValidation:
    @pytest.mark.parametrize("title,expected_valid", [
        ("Valid Title", True),
        ("a" * 255, True),
        ("a" * 256, False),
        ("", False),
    ])
    def test_title_validation(self, title, expected_valid, user):
        """Test title field validation"""
        notice = Notice(title=title, created_by=user)
        
        if expected_valid:
            notice.full_clean()  # Should not raise
        else:
            with pytest.raises(ValidationError):
                notice.full_clean()
```

## Coverage

**Run tests with coverage:**
```bash
pytest --cov=apps --cov-report=html --cov-report=term-missing
```

**View HTML report:**
```bash
open htmlcov/index.html
```

**Target 80%+ coverage dla critical code.**

## CI/CD Integration

**GitHub Actions: `.github/workflows/tests.yml`**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install pipenv
        pipenv install --dev
    
    - name: Run tests
      run: pipenv run pytest --cov --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Best Practices

1. **Use fixtures for reusable test data**
2. **Test edge cases, not just happy path**
3. **Use parametrize for similar tests with different data**
4. **Mock external services**
5. **Test query count for performance**
6. **Aim for 80%+ code coverage**
7. **Keep tests fast** - use --reuse-db and --nomigrations
8. **Test permissions explicitly**
9. **Use descriptive test names**
10. **Group related tests in classes**
