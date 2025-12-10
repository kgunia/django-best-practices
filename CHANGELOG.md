# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-10

### Added
- **Advanced Patterns** section with:
  - Custom QuerySet Managers
  - Service Layer Architecture
  - Repository Pattern
  - Dataclasses for DTOs
  - Signal Handlers
  - Reusable Mixins (Timestamp, UserTracking, SoftDelete, Publishable)
- **Code Quality Tools** section with:
  - Ruff configuration (replaces Black, isort, flake8)
  - Mypy type checking setup
  - Pre-commit hooks configuration
  - Logging best practices
- **Extended Testing** with:
  - Factory-boy setup and examples
  - Freezegun for time-based tests
  - Comprehensive pytest patterns
- **Installation Guide** and **Quick Start** section
- Ready-to-use configuration files in `assets/`:
  - `ruff.toml`
  - `mypy.ini`
  - `.pre-commit-config.yaml`
  - `factories.py`
- Detailed reference documentation:
  - `references/advanced_patterns.md`
  - `references/code_quality.md`

### Changed
- Updated all dates to 2025
- Converted all mixed Polish/English text to consistent English
- Improved code examples with more realistic scenarios
- Enhanced query optimization examples with 4 recipient types pattern

### Fixed
- Language consistency issues (removed Polish fragments)
- Code example syntax errors
- Broken internal links

## [1.0.0] - 2024-12-05

### Added
- Initial release with core Django best practices
- Query Optimization patterns:
  - N+1 problem detection and fixes
  - select_related() and prefetch_related()
  - Bulk operations
  - Caching strategies
- AJAX Forms & Choices.js:
  - Universal ChoicesMixin
  - AJAX search patterns
  - JavaScript integration
- Testing Patterns:
  - Pytest setup and configuration
  - Fixture examples
  - Mocking patterns
- String Formatting & i18n:
  - gettext_lazy patterns
  - format_lazy usage
- Security:
  - pip-audit for vulnerability scanning
- Git Workflow:
  - Conventional commits
  - Tagging strategy

### Documentation
- `SKILL.md` - Main skill file
- `references/ajax_patterns.md` - Detailed AJAX guide
- `references/query_optimization.md` - Performance patterns
- `references/testing_patterns.md` - Testing examples
- `assets/choices_mixin.py` - Ready-to-use code

## [Unreleased]

### Planned
- Django 5.x specific patterns
- Celery integration patterns
- Redis caching examples
- Docker deployment guide
- API best practices (DRF)
- GraphQL patterns
- WebSocket patterns
- Monitoring and logging improvements

---

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
