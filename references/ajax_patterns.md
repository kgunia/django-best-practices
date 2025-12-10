# AJAX Patterns with Choices.js

## Complete ChoicesMixin Implementation

```python
import json
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django import forms


class LazyEncoder(DjangoJSONEncoder):
    """Encoder for Django lazy objects"""
    pass


class ChoicesMixin:
    """Universal mixin for Choices.js integration with AJAX support"""
    
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
        field_config = settings.CHOICES_CONFIG.copy()
        if choices_config is not None:
            field_config.update(choices_config)
        return json.dumps(field_config, cls=LazyEncoder)


class ChoicesSelect(ChoicesMixin, forms.Select):
    """Select widget with Choices.js and optional AJAX"""
    
    def __init__(self, *args, disabled_choices=None, ajax_url=None, ajax_params=None, **kwargs):
        self.disabled_choices = disabled_choices or []
        super().__init__(*args, ajax_url=ajax_url, ajax_params=ajax_params, **kwargs)

    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value in self.disabled_choices:
            option["attrs"]["disabled"] = True
        return option
```

## JavaScript Implementation

**File: `static/js/choices_init.js`**

```javascript
var default_choices_config = JSON.parse(
    document.getElementById("default_choices_config").textContent
);

document.addEventListener("htmx:afterRequest", initChoicesJS, false);
document.addEventListener("htmx:load", markInvalidBootstrapInputs, false);
document.addEventListener("DOMContentLoaded", initChoicesJS, false);

function initChoicesJS() {
    document.querySelectorAll("[choices-config]").forEach(function (element) {
        if (element.getAttribute("data-choice") !== "active") {
            const field_choices_config = JSON.parse(
                element.getAttribute("choices-config")
            );
            const ajaxUrl = element.getAttribute("data-ajax-url");
            
            let config = field_choices_config || default_choices_config;
            
            if (ajaxUrl) {
                // Collect all data-ajax-* params
                const ajaxParams = {};
                Array.from(element.attributes).forEach(attr => {
                    if (attr.name.startsWith('data-ajax-') && 
                        attr.name !== 'data-ajax-url') {
                        const paramName = attr.name.replace('data-ajax-', '');
                        ajaxParams[paramName] = attr.value;
                    }
                });
                
                // AJAX-specific config
                config = {
                    ...config,
                    searchEnabled: true,
                    searchChoices: false,
                    shouldSort: false,
                    placeholder: true,
                    placeholderValue: 'Wpisz aby wyszukać...',
                    noResultsText: 'Brak wyników',
                };
                
                const choices = new Choices(element, config);
                
                // Search with debounce
                let searchTimeout;
                element.addEventListener('search', function(event) {
                    const searchTerm = event.detail.value;
                    
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        if (searchTerm.length >= 2) {
                            fetchResults(choices, ajaxUrl, ajaxParams, searchTerm);
                        }
                    }, 300);  // 300ms debounce
                });
                
                // Load initial results (optional)
                fetchResults(choices, ajaxUrl, ajaxParams, '');
            } else {
                // Regular Choices without AJAX
                new Choices(element, config);
            }
        }
    });
}

function fetchResults(choicesInstance, url, params, searchTerm) {
    const urlParams = new URLSearchParams({
        ...params,
        search: searchTerm
    });
    
    fetch(`${url}?${urlParams.toString()}`)
        .then(response => response.json())
        .then(data => {
            choicesInstance.clearChoices();
            choicesInstance.setChoices(data, 'value', 'label', true);
        })
        .catch(error => {
            console.error('Error fetching choices:', error);
        });
}

function markInvalidBootstrapInputs(content) {
    htmx.findAll(content.target, ".choices .choices__inner .is-invalid")
        .forEach((e) => {
            htmx.addClass(htmx.closest(e, ".choices"), "is-invalid");
        });
}
```

## Django Endpoint Pattern

```python
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q

@login_required
def search_recipients(request):
    """
    AJAX endpoint for recipient search.
    Returns: [{"value": "id", "label": "display_text"}]
    """
    notice_id = request.GET.get('notice_id')
    search = request.GET.get('search', '')
    
    if not notice_id:
        return JsonResponse({'results': []})
    
    recipients = (
        AdditionalRecipient.objects
        .filter(notice_id=notice_id)
        .filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
        .only('id', 'first_name', 'last_name', 'email')
        .order_by('last_name', 'first_name')[:20]
    )
    
    results = [
        {
            'value': str(r.id),
            'label': f"{r.first_name} {r.last_name} ({r.email})"
        }
        for r in recipients
    ]
    
    return JsonResponse(results, safe=False)
```

## Form Usage Example

### Basic Form

```python
from django.utils.translation import gettext_lazy as _

class NoticeRecipientForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        label=_("Recipient"),
        queryset=AdditionalRecipient.objects.none(),
        widget=ChoicesSelect(
            choices_config={"searchEnabled": True},
            ajax_url=reverse_lazy('search_recipients'),
            ajax_params={}
        ),
        required=False,
    )
    
    def __init__(self, *args, notice=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if notice:
            # Update AJAX params dynamically
            self.fields['recipient'].widget.ajax_params['notice_id'] = notice.id
            self.fields['recipient'].widget.attrs['data-ajax-notice-id'] = notice.id
```

### Custom Field (Cleaner)

```python
class AjaxModelChoiceField(forms.ModelChoiceField):
    """ModelChoiceField with built-in AJAX support"""
    
    def __init__(self, ajax_url=None, ajax_params=None, *args, **kwargs):
        self.ajax_url = ajax_url
        self.ajax_params = ajax_params or {}
        
        if 'widget' not in kwargs:
            kwargs['widget'] = ChoicesSelect(
                choices_config={"searchEnabled": True},
                ajax_url=ajax_url,
                ajax_params=ajax_params
            )
        
        super().__init__(*args, **kwargs)
    
    def update_ajax_params(self, **params):
        """Update AJAX params after initialization"""
        self.ajax_params.update(params)
        for key, value in params.items():
            self.widget.attrs[f'data-ajax-{key}'] = value

# Usage
class SimpleForm(forms.Form):
    recipient = AjaxModelChoiceField(
        queryset=AdditionalRecipient.objects.none(),
        ajax_url='/api/search-recipients/',
        required=True,
    )
    
    def __init__(self, *args, notice=None, **kwargs):
        super().__init__(*args, **kwargs)
        if notice:
            self.fields['recipient'].update_ajax_params(notice_id=notice.id)
```

## Settings Configuration

**File: `settings.py`**

```python
CHOICES_CONFIG = {
    "searchEnabled": True,
    "searchPlaceholderValue": "Szukaj...",
    "noResultsText": "Brak wyników",
    "noChoicesText": "Brak opcji do wyboru",
    "itemSelectText": "Naciśnij aby wybrać",
    "removeItemButton": True,
}
```

**Template setup:**

```html
<script id="default_choices_config" type="application/json">
    {{ CHOICES_CONFIG|safe }}
</script>
```

## Troubleshooting

**Problem: Form validation fails with AJAX field**

Rozwiązanie: Upewnij się że queryset jest pusty na starcie i wypełniany dynamicznie w `__init__`:

```python
recipient = forms.ModelChoiceField(
    queryset=AdditionalRecipient.objects.none(),  # Pusty!
    # ...
)
```

**Problem: Wartość nie jest wysyłana w POST**

Check in console if Choices.js is setting the value:

```javascript
document.addEventListener('submit', function(e) {
    const form = e.target;
    const choicesSelects = form.querySelectorAll('[data-ajax-url]');
    
    choicesSelects.forEach(select => {
        console.log('Select value:', select.value);
        console.log('Select required:', select.required);
    });
});
```
