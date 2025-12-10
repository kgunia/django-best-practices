"""
Universal Choices.js mixin for Django forms with AJAX support.

Usage:
    1. Copy this file to your project (e.g., apps/core/widgets.py)
    2. Import and use in your forms
    3. See ajax_patterns.md in references/ for complete examples

Requirements:
    - Choices.js library loaded in template
    - settings.CHOICES_CONFIG defined
    - JavaScript initialization (see ajax_patterns.md)
"""

import json
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django import forms


class LazyEncoder(DjangoJSONEncoder):
    """Encoder for Django lazy objects (gettext_lazy, etc.)"""
    pass


class ChoicesMixin:
    """
    Universal mixin for Choices.js integration with optional AJAX support.
    
    Args:
        choices_config (dict, optional): Override default Choices.js config
        ajax_url (str, optional): URL for AJAX search endpoint
        ajax_params (dict, optional): Additional parameters for AJAX requests
    
    Example:
        widget = ChoicesSelect(
            choices_config={"searchEnabled": True},
            ajax_url="/api/search-recipients/",
            ajax_params={"notice_id": 123}
        )
    """
    
    def __init__(self, *args, choices_config=None, ajax_url=None, ajax_params=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ajax_url = ajax_url
        self.ajax_params = ajax_params or {}
        self.attrs["choices-config"] = self.get_choices_config(choices_config)
        
        # Add AJAX attributes if defined
        if self.ajax_url:
            self.attrs["data-ajax-url"] = self.ajax_url
            for key, value in self.ajax_params.items():
                self.attrs[f"data-ajax-{key}"] = value

    @staticmethod
    def get_choices_config(choices_config):
        """Merge field-specific config with default settings"""
        field_config = settings.CHOICES_CONFIG.copy()
        if choices_config is not None:
            field_config.update(choices_config)
        return json.dumps(field_config, cls=LazyEncoder)


class ChoicesSelect(ChoicesMixin, forms.Select):
    """
    Select widget with Choices.js and optional disabled choices.
    
    Args:
        disabled_choices (list, optional): List of choice values to disable
        ajax_url (str, optional): URL for AJAX search endpoint
        ajax_params (dict, optional): Additional parameters for AJAX requests
    
    Example:
        widget = ChoicesSelect(
            disabled_choices=['inactive_option'],
            ajax_url="/api/search/",
        )
    """
    
    def __init__(self, *args, disabled_choices=None, ajax_url=None, ajax_params=None, **kwargs):
        self.disabled_choices = disabled_choices or []
        super().__init__(*args, ajax_url=ajax_url, ajax_params=ajax_params, **kwargs)

    def create_option(self, name, value, label, selected, index, **kwargs):
        """Override to support disabled choices"""
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value in self.disabled_choices:
            option["attrs"]["disabled"] = True
        return option


class ChoicesSelectMultiple(ChoicesMixin, forms.SelectMultiple):
    """
    Multiple select widget with Choices.js.
    
    Args:
        ajax_url (str, optional): URL for AJAX search endpoint
        ajax_params (dict, optional): Additional parameters for AJAX requests
    
    Example:
        widget = ChoicesSelectMultiple(
            choices_config={"removeItemButton": True},
            ajax_url="/api/search-tags/",
        )
    """
    pass


class AjaxModelChoiceField(forms.ModelChoiceField):
    """
    ModelChoiceField with built-in AJAX support.
    
    Automatically handles queryset management and widget configuration.
    
    Args:
        ajax_url (str): URL for AJAX search endpoint
        ajax_params (dict, optional): Additional parameters for AJAX requests
        
    Example:
        class MyForm(forms.Form):
            recipient = AjaxModelChoiceField(
                queryset=Recipient.objects.none(),
                ajax_url='/api/search-recipients/',
                required=True,
            )
            
            def __init__(self, *args, notice=None, **kwargs):
                super().__init__(*args, **kwargs)
                if notice:
                    self.fields['recipient'].update_ajax_params(notice_id=notice.id)
    """
    
    def __init__(self, ajax_url=None, ajax_params=None, *args, **kwargs):
        self.ajax_url = ajax_url
        self.ajax_params = ajax_params or {}
        
        # Auto-configure widget if not provided
        if 'widget' not in kwargs:
            kwargs['widget'] = ChoicesSelect(
                choices_config={"searchEnabled": True},
                ajax_url=ajax_url,
                ajax_params=ajax_params
            )
        
        super().__init__(*args, **kwargs)
    
    def update_ajax_params(self, **params):
        """
        Update AJAX parameters after initialization.
        
        Useful for dynamic parameters like notice_id in __init__.
        
        Args:
            **params: Key-value pairs to add/update in ajax_params
            
        Example:
            self.fields['recipient'].update_ajax_params(notice_id=notice.id)
        """
        self.ajax_params.update(params)
        for key, value in params.items:
            self.widget.attrs[f'data-ajax-{key}'] = value


# Settings template for settings.py
"""
Add to your settings.py:

CHOICES_CONFIG = {
    "searchEnabled": True,
    "searchPlaceholderValue": "Szukaj...",
    "noResultsText": "Brak wyników",
    "noChoicesText": "Brak opcji do wyboru",
    "itemSelectText": "Naciśnij aby wybrać",
    "removeItemButton": True,
}

And in your base template:

<script id="default_choices_config" type="application/json">
    {{ CHOICES_CONFIG|safe }}
</script>
"""
