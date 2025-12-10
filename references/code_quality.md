# Code Quality Tools

## Ruff - Modern Python Linter & Formatter

Ruff is an extremely fast Python linter and formatter, written in Rust. It replaces multiple tools: Black, isort, flake8, and more.

### Installation

```bash
pipenv install --dev ruff
```

### Configuration

**File: `ruff.toml` (in project root)**

```toml
# Target Python version
target-version = "py311"

# Line length
line-length = 100

# Exclude directories
extend-exclude = [
    "migrations",
    "*/migrations/*",
    ".venv",
    "venv",
]

[lint]
# Enable specific rule sets
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "W",    # pycodestyle warnings
    "B",    # flake8-bugbear
    "Q",    # flake8-quotes
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "DJ",   # flake8-django
]

# Ignore specific rules
ignore = [
    "E501",   # Line too long (handled by formatter)
    "DJ001",  # Django model without __str__
]

# Per-file ignores
[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports
"tests/*.py" = ["S101"]   # Use of assert
"*/migrations/*.py" = ["E501", "N806"]
"settings/*.py" = ["F405"]  # Star imports

# Django settings
[lint.flake8-django]
settings-module = "config.settings"

[format]
# Formatting options
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

### Usage

**Check for issues:**
```bash
ruff check .
```

**Auto-fix issues:**
```bash
ruff check --fix .
```

**Format code:**
```bash
ruff format .
```

**Check specific directory:**
```bash
ruff check apps/notices/
```

**Show rule explanations:**
```bash
ruff rule E501
```

### VS Code Integration

**File: `.vscode/settings.json`**
```json
{
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": true,
            "source.organizeImports": true
        },
        "editor.defaultFormatter": "charliermarsh.ruff"
    }
}
```

### Common Rules to Know

- **E501**: Line too long (let formatter handle it)
- **F401**: Unused import
- **F841**: Unused variable
- **B008**: Do not use function calls in default arguments
- **DJ001**: Model without __str__
- **UP**: Python upgrade suggestions

## Mypy - Static Type Checker

Mypy performs static type checking for Python, catching type errors before runtime.

### Installation

```bash
pipenv install --dev mypy django-stubs types-requests
```

### Configuration

**File: `mypy.ini` (in project root)**

```ini
[mypy]
# Python version
python_version = 3.11

# Strict mode options
warn_return_any = True
warn_unused_configs = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_optional = True

# Gradually enforce types
disallow_untyped_defs = True
disallow_any_unimported = False
disallow_any_generics = False
disallow_subclassing_any = False

# Django plugin
plugins = mypy_django_plugin.main

# Disable for tests initially
[mypy-tests.*]
disallow_untyped_defs = False

# Django stubs config
[mypy.plugins.django-stubs]
django_settings_module = config.settings

# Third-party libraries without stubs
[mypy-celery.*]
ignore_missing_imports = True

[mypy-factory.*]
ignore_missing_imports = True

[mypy-debug_toolbar.*]
ignore_missing_imports = True
```

**File: `setup.cfg` (alternative location)**

```ini
[mypy]
python_version = 3.11
plugins = mypy_django_plugin.main

[mypy.plugins.django-stubs]
django_settings_module = config.settings
```

### Usage

**Check entire project:**
```bash
mypy .
```

**Check specific app:**
```bash
mypy apps/notices/
```

**Check with detailed output:**
```bash
mypy --show-error-codes --pretty .
```

**Generate HTML report:**
```bash
mypy --html-report ./mypy-report .
```

### Type Hints Examples

**Views:**
```python
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from typing import Optional

def notice_list(request: HttpRequest) -> HttpResponse:
    notices = Notice.objects.published()
    return render(request, 'notices/list.html', {'notices': notices})

def notice_detail(request: HttpRequest, notice_id: int) -> HttpResponse:
    notice: Optional[Notice] = Notice.objects.filter(id=notice_id).first()
    if notice is None:
        raise Http404()
    return render(request, 'notices/detail.html', {'notice': notice})
```

**Services:**
```python
from typing import List, Optional
from django.db.models import QuerySet

class NoticeService:
    @staticmethod
    def get_published_notices(user: User) -> QuerySet[Notice]:
        return Notice.objects.published().for_user(user)
    
    @staticmethod
    def create_notice(data: NoticeCreationData) -> Notice:
        # Implementation
        pass
```

**Models:**
```python
from django.db import models
from typing import Optional

class Notice(models.Model):
    title: str = models.CharField(max_length=255)
    content: str = models.TextField()
    
    def get_recipients(self) -> QuerySet['Recipient']:
        return self.recipients.all()
    
    def mark_as_read(self, user: User) -> Optional['ReadAcknowledgment']:
        ack, created = ReadAcknowledgment.objects.get_or_create(
            notice=self,
            user=user
        )
        return ack if created else None
```

### VS Code Integration

**File: `.vscode/settings.json`**
```json
{
    "python.linting.mypyEnabled": true,
    "python.linting.mypyArgs": [
        "--config-file=mypy.ini"
    ]
}
```

## Pre-commit Hooks

Pre-commit hooks run checks automatically before each commit, ensuring code quality.

### Installation

```bash
pipenv install --dev pre-commit
pre-commit install
```

### Configuration

**File: `.pre-commit-config.yaml` (in project root)**

```yaml
repos:
  # Ruff - linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      # Linter
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      # Formatter
      - id: ruff-format

  # Mypy - type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies:
          - django-stubs
          - types-requests
        args: [--config-file=mypy.ini]
        files: ^apps/

  # Django - check for issues
  - repo: local
    hooks:
      - id: django-check
        name: Django Check
        entry: python manage.py check
        language: system
        pass_filenames: false
        always_run: true

      - id: django-migrations
        name: Django Migrations Check
        entry: python manage.py makemigrations --check --dry-run
        language: system
        pass_filenames: false
        always_run: true

  # Tests - run on commit
  - repo: local
    hooks:
      - id: pytest
        name: Pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: [--maxfail=1, -x]

  # General hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: check-merge-conflict
      - id: debug-statements
```

### Usage

**Run on all files:**
```bash
pre-commit run --all-files
```

**Run specific hook:**
```bash
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

**Skip hooks for a commit:**
```bash
git commit --no-verify -m "WIP: work in progress"
```

**Update hooks to latest versions:**
```bash
pre-commit autoupdate
```

### Lightweight Configuration (Fast Commits)

If full pre-commit is too slow, use a lighter version:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
```

## Logging Best Practices

Proper logging helps with debugging and monitoring production issues.

### Configuration

**File: `settings.py`**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django_error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Create logs directory
(BASE_DIR / 'logs').mkdir(exist_ok=True)
```

### Usage in Code

```python
import logging

# Get logger
logger = logging.getLogger(__name__)

# In views
def create_notice(request):
    logger.info(f"User {request.user.id} creating notice")
    
    try:
        notice = NoticeService.create_notice(data)
        logger.info(f"Notice {notice.id} created successfully")
        return redirect('notices:detail', pk=notice.pk)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        messages.error(request, str(e))
    except Exception as e:
        logger.error(f"Failed to create notice: {e}", exc_info=True)
        messages.error(request, _("An error occurred"))

# In services
class NoticeService:
    @staticmethod
    def create_notice(data: NoticeCreationData) -> Notice:
        logger.debug(f"Creating notice with data: {data}")
        
        with transaction.atomic():
            notice = Notice.objects.create(...)
            logger.info(f"Notice {notice.id} created")
            
            NoticeService._add_recipients(notice, data)
            logger.debug(f"Added recipients to notice {notice.id}")
            
            return notice
```

### Log Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General informational messages
- **WARNING**: Warning messages (something unexpected)
- **ERROR**: Error messages (something failed)
- **CRITICAL**: Critical messages (system may be unstable)

### Best Practices

1. **Use appropriate log levels** - don't log everything as ERROR
2. **Include context** - user IDs, object IDs, etc.
3. **Don't log sensitive data** - passwords, tokens, PII
4. **Use structured logging** - JSON format for production
5. **Rotate log files** - prevent disk space issues
6. **Monitor logs** - set up alerts for errors
7. **Use exc_info=True** - include stack traces for errors

## CI/CD Integration

**File: `.github/workflows/ci.yml`**

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install pipenv
        pipenv install --dev
    
    - name: Ruff check
      run: pipenv run ruff check .
    
    - name: Ruff format check
      run: pipenv run ruff format --check .
    
    - name: Mypy
      run: pipenv run mypy .
    
    - name: Django checks
      run: |
        pipenv run python manage.py check
        pipenv run python manage.py makemigrations --check --dry-run
    
    - name: Pytest
      run: pipenv run pytest --cov --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Summary

**Tools used:**
- **Ruff**: Fast linting and formatting (replaces Black, isort, flake8)
- **Mypy**: Static type checking
- **Pre-commit**: Automated checks before commit
- **Logging**: Structured logging for debugging and monitoring

**Benefits:**
- Catch bugs before runtime
- Consistent code style
- Better IDE support with type hints
- Easier debugging with proper logging
- Automated quality checks in CI/CD
