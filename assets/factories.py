"""
Factory-boy factories for Django models.

Usage in tests:
    from tests.factories import UserFactory, NoticeFactory
    
    user = UserFactory()
    notice = NoticeFactory(created_by=user)
    notices = NoticeFactory.create_batch(10)

Documentation: https://factoryboy.readthedocs.io/
"""

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


# ========================================
# User & Auth Factories
# ========================================

class UserFactory(DjangoModelFactory):
    """Factory for User model."""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after creation."""
        if not create:
            return
        
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('testpass123')
        obj.save()


class StaffUserFactory(UserFactory):
    """Factory for staff user."""
    is_staff = True


class SuperUserFactory(UserFactory):
    """Factory for superuser."""
    is_staff = True
    is_superuser = True


# ========================================
# Entity Factories (if you have Entity model)
# ========================================

class EntityFactory(DjangoModelFactory):
    """Factory for Entity model."""
    
    class Meta:
        model = 'entities.Entity'
    
    name = factory.Sequence(lambda n: f'Entity {n}')
    code = factory.Sequence(lambda n: f'ENT{n:04d}')
    is_active = True


# ========================================
# Notice Factories
# ========================================

class NoticeFactory(DjangoModelFactory):
    """Factory for Notice model."""
    
    class Meta:
        model = 'notices.Notice'
    
    title = factory.Faker('sentence', nb_words=6)
    content = factory.Faker('paragraph', nb_sentences=5)
    
    # Use fuzzy.FuzzyChoice for enum/choice fields
    status = fuzzy.FuzzyChoice(['draft', 'published', 'archived'])
    
    # Dates
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + timedelta(days=30) if obj.start_date else None
    )
    
    # Foreign keys
    created_by = factory.SubFactory(UserFactory)
    
    # Timestamps (auto_now_add=True)
    created_at = factory.LazyFunction(timezone.now)


class PublishedNoticeFactory(NoticeFactory):
    """Factory for published notices."""
    status = 'published'


class DraftNoticeFactory(NoticeFactory):
    """Factory for draft notices."""
    status = 'draft'


# ========================================
# Recipient Factories
# ========================================

class RecipientGroupFactory(DjangoModelFactory):
    """Factory for RecipientGroup model."""
    
    class Meta:
        model = 'notices.RecipientGroup'
    
    name = factory.Sequence(lambda n: f'Group {n}')
    description = factory.Faker('text', max_nb_chars=200)
    created_by = factory.SubFactory(UserFactory)


class NoticeRecipientFactory(DjangoModelFactory):
    """Factory for NoticeRecipient (direct recipients)."""
    
    class Meta:
        model = 'notices.NoticeRecipient'
    
    notice = factory.SubFactory(NoticeFactory)
    recipient = factory.SubFactory(EntityFactory)


class NoticeAdditionalRecipientFactory(DjangoModelFactory):
    """Factory for NoticeAdditionalRecipient."""
    
    class Meta:
        model = 'notices.NoticeAdditionalRecipient'
    
    notice = factory.SubFactory(NoticeFactory)
    user = factory.SubFactory(UserFactory)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')


class ReadAcknowledgmentFactory(DjangoModelFactory):
    """Factory for ReadAcknowledgment."""
    
    class Meta:
        model = 'notices.ReadAcknowledgment'
    
    notice = factory.SubFactory(NoticeFactory)
    user = factory.SubFactory(UserFactory)
    read_at = factory.LazyFunction(timezone.now)


# ========================================
# Complex Factory with Many-to-Many
# ========================================

class NoticeWithRecipientsFactory(NoticeFactory):
    """
    Factory for Notice with recipients.
    
    Usage:
        notice = NoticeWithRecipientsFactory(
            recipient_count=5,
            additional_recipient_count=3
        )
    """
    
    @factory.post_generation
    def recipient_count(obj, create, extracted, **kwargs):
        """Add direct recipients after creation."""
        if not create:
            return
        
        count = extracted or 3
        for _ in range(count):
            NoticeRecipientFactory(notice=obj)
    
    @factory.post_generation
    def additional_recipient_count(obj, create, extracted, **kwargs):
        """Add additional recipients after creation."""
        if not create:
            return
        
        count = extracted or 2
        for _ in range(count):
            NoticeAdditionalRecipientFactory(notice=obj)


# ========================================
# Factory Traits (alternative patterns)
# ========================================

class NoticeWithTraitsFactory(NoticeFactory):
    """
    Factory with traits for different scenarios.
    
    Usage:
        # With read acknowledgment
        notice = NoticeWithTraitsFactory(read=True, user=some_user)
        
        # Expired notice
        notice = NoticeWithTraitsFactory(expired=True)
    """
    
    class Params:
        # Trait: notice is read by a user
        read = factory.Trait(
            read_acknowledgment=factory.RelatedFactory(
                ReadAcknowledgmentFactory,
                factory_related_name='notice',
            )
        )
        
        # Trait: notice is expired
        expired = factory.Trait(
            start_date=factory.LazyFunction(
                lambda: timezone.now().date() - timedelta(days=60)
            ),
            end_date=factory.LazyFunction(
                lambda: timezone.now().date() - timedelta(days=30)
            ),
        )


# ========================================
# Usage Examples in Tests
# ========================================

"""
Example test file:

import pytest
from tests.factories import (
    UserFactory, 
    NoticeFactory, 
    PublishedNoticeFactory,
    NoticeWithRecipientsFactory
)

@pytest.mark.django_db
class TestNoticeModel:
    def test_create_notice(self):
        notice = NoticeFactory()
        assert notice.title
        assert notice.created_by
    
    def test_published_notice(self):
        notice = PublishedNoticeFactory()
        assert notice.status == 'published'
    
    def test_notice_with_recipients(self):
        notice = NoticeWithRecipientsFactory(
            recipient_count=5,
            additional_recipient_count=3
        )
        assert notice.noticerecipient_set.count() == 5
        assert notice.noticeadditionalrecipient_set.count() == 3
    
    def test_batch_creation(self):
        notices = NoticeFactory.create_batch(10)
        assert len(notices) == 10
    
    def test_build_without_saving(self):
        # Build without saving to database
        notice = NoticeFactory.build()
        assert notice.id is None
"""
