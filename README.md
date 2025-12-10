# Django Best Practices

Production-ready Django patterns, code quality tools, and performance optimizations. A comprehensive guide for building maintainable Django applications.

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/yourusername/django-best-practices/releases)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-4.x%20%7C%205.x-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 💡 **Bonus:** This repository includes a [Claude AI Skill](#-bonus-claude-ai-skill) for automated code assistance!

## 🎯 What Is This?

A curated collection of Django best practices covering:
- **Architecture patterns** (Service Layer, Repository, Custom Managers)
- **Performance optimization** (N+1 fixes, caching, query optimization)  
- **Code quality** (Ruff, Mypy, Pre-commit hooks)
- **Testing strategies** (pytest, factory-boy, freezegun)
- **Production patterns** used in real-world applications

**Use it as:**
- 📖 Reference documentation for your team
- 🎓 Learning resource for Django developers
- ✅ Code review checklist
- 🤖 AI assistant knowledge base (Claude Skill included!)

## 📚 What's Included

### Core Principles
- **Type hints** + English docstrings
- **i18n** with `gettext_lazy`
- **Query optimization** patterns
- **Testing** with pytest + factory-boy + freezegun

### Advanced Patterns
- Custom QuerySet managers
- Service layer architecture
- Repository pattern
- Dataclasses for DTOs
- Signal handlers
- Reusable mixins

### Code Quality Tools
- **Ruff** (linting + formatting)
- **Mypy** (type checking)
- **Pre-commit hooks**
- **Logging** best practices

### AJAX & Forms
- Universal Choices.js patterns
- AJAX search endpoints
- Ready-to-use widgets

### Performance
- Query optimization (N+1, select_related, prefetch_related)
- Caching strategies
- Database indexes
- Bulk operations

## 🚀 How to Use

### Option 1: Browse Online (Quickest)

Read directly on GitHub:
- [Core Practices](SKILL.md) - Main guidelines
- [Advanced Patterns](references/advanced_patterns.md) - Service Layer, Repository, Managers
- [Query Optimization](references/query_optimization.md) - Performance patterns
- [Testing Guide](references/testing_patterns.md) - Pytest examples
- [Code Quality](references/code_quality.md) - Ruff, Mypy setup
- [Quick Reference](QUICK_REFERENCE.md) - One-page cheat sheet

### Option 2: Clone Repository (Recommended)

Keep it local as a reference:

```bash
git clone https://github.com/yourusername/django-best-practices.git
cd django-best-practices

# Browse with your favorite editor
code .  # VS Code
pycharm .  # PyCharm
```

**Update when new patterns are added:**
```bash
git pull origin main
```

### Option 3: Use Ready-to-Use Configs

Copy configuration files to your project:

```bash
# Code quality tools
cp assets/ruff.toml your-project/
cp assets/mypy.ini your-project/
cp assets/.pre-commit-config.yaml your-project/

# Testing factories
cp assets/factories.py your-project/tests/

# AJAX widgets
cp assets/choices_mixin.py your-project/apps/core/
```

### Option 4: 🤖 Bonus - Claude AI Skill

**Use with Claude AI for automated assistance:**

1. **Download the skill:**
   ```bash
   wget https://github.com/yourusername/django-best-practices/releases/latest/download/django-best-practices.skill
   ```

2. **Upload to Claude:**
   - Go to [claude.ai](https://claude.ai)
   - Open your Project
   - Click "Add content" → "Upload files"
   - Upload the `.skill` file

3. **Use it:**
   ```
   "Write a Django view following best practices"
   "Refactor this code using service layer pattern"
   "Add pytest tests with factory-boy"
   "Optimize these database queries"
   ```

Claude will automatically apply all patterns from this repository!

**Building the skill yourself:**
```bash
# Repository includes skill build tools
python scripts/build_skill.py  # Generates .skill file
```

## 📖 Documentation

### Main Guide
- [SKILL.md](SKILL.md) - Core best practices

### References
- [AJAX Patterns](references/ajax_patterns.md) - Choices.js integration with AJAX
- [Query Optimization](references/query_optimization.md) - N+1 fixes, caching, indexes
- [Testing Patterns](references/testing_patterns.md) - Pytest, factory-boy, fixtures
- [Advanced Patterns](references/advanced_patterns.md) - Service Layer, Repository, Custom Managers
- [Code Quality](references/code_quality.md) - Ruff, Mypy, Pre-commit setup

### Ready-to-Use Code
- [choices_mixin.py](assets/choices_mixin.py) - Universal AJAX form widgets
- [ruff.toml](assets/ruff.toml) - Ruff configuration
- [mypy.ini](assets/mypy.ini) - Mypy configuration
- [.pre-commit-config.yaml](assets/.pre-commit-config.yaml) - Pre-commit hooks
- [factories.py](assets/factories.py) - Factory-boy examples

### Quick References
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - One-page cheat sheet for common patterns

## 💡 Why This Repository?

**For Individual Developers:**
- Learn production-ready patterns
- Copy working code examples
- Avoid common pitfalls
- Speed up development

**For Teams:**
- Establish coding standards
- Onboard new developers faster
- Consistent code review criteria
- Share knowledge effectively

**For Companies:**
- Reduce technical debt
- Improve code quality
- Standardize Django practices
- Train junior developers

**Bonus - For AI-Assisted Development:**
- Use as Claude AI Skill for automated assistance
- Get AI suggestions following your standards
- Consistent code generation

## 🛠️ Quick Start Examples

### Query Optimization
```python
# ❌ N+1 problem
recipients = AdditionalRecipient.objects.filter(notice=notice)
for r in recipients:
    print(r.notice.title)  # Query on each iteration!

# ✅ Optimized
recipients = (
    AdditionalRecipient.objects
    .filter(notice=notice)
    .select_related('notice')
    .only('id', 'first_name', 'last_name', 'email', 'notice__title')
    .order_by('last_name', 'first_name')
)
```

### Service Layer
```python
from dataclasses import dataclass

@dataclass
class NoticeCreationData:
    title: str
    content: str
    recipient_ids: List[int]
    created_by: User

class NoticeService:
    @staticmethod
    @transaction.atomic
    def create_notice(data: NoticeCreationData) -> Notice:
        notice = Notice.objects.create(...)
        NoticeService._add_recipients(notice, data)
        return notice
```

### Testing with Factory-Boy
```python
import factory

class NoticeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notice
    
    title = factory.Faker('sentence')
    created_by = factory.SubFactory(UserFactory)

# Usage
@pytest.mark.django_db
def test_notice_creation():
    notice = NoticeFactory(status='published')
    assert notice.status == 'published'
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-pattern`)
3. Add your pattern to appropriate file in `references/`
4. Update `SKILL.md` if needed
5. Commit your changes (`git commit -m 'Add new pattern for X'`)
6. Push to the branch (`git push origin feature/new-pattern`)
7. Open a Pull Request

### Ideas for Contributions

- New Django patterns you use in production
- Additional code quality tools
- More testing examples
- Performance optimization techniques
- Security best practices
- Deployment patterns

## 📝 Version History

### v2.0 (December 2025)
- ✨ Added Advanced Patterns section
- ✨ Added Code Quality tools (Ruff, Mypy)
- ✨ Extended Testing with factory-boy and freezegun
- ✨ Added Installation guide and Quick Start
- ✨ Merged AJAX patterns and query optimization

### v1.0 (Initial Release)
- ✅ Basic Django best practices
- ✅ Query optimization
- ✅ Testing patterns

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on real-world production patterns
- Inspired by Django community best practices
- Built for use with [Claude AI](https://claude.ai)

## 💬 Support & Community

- 🐛 [Report bugs](https://github.com/yourusername/django-best-practices/issues)
- 💡 [Request features](https://github.com/yourusername/django-best-practices/issues)
- 📖 [Read documentation](https://github.com/yourusername/django-best-practices/wiki)
- 💬 [Discussions](https://github.com/yourusername/django-best-practices/discussions)

## 🤖 Bonus: Claude AI Skill

This repository can be packaged as a Claude AI Skill for automated assistance.

**What is a Claude Skill?**
- AI knowledge base that Claude uses automatically
- Provides context-aware suggestions
- Enforces your coding standards
- Available in all Claude conversations within a project

**How to use:**
1. Download `.skill` file from [Releases](https://github.com/yourusername/django-best-practices/releases)
2. Upload to your Claude Project
3. Get AI assistance following these exact patterns!

**Build skill yourself:**
```bash
# All source files are in this repo
# .skill file is just a packaged version
python scripts/build_skill.py
```

## ⭐ Show Your Support

If this repository helps you, please:
- ⭐ Star it on GitHub
- 🔀 Fork it for your team
- 📣 Share it with other Django developers
- 🤝 Contribute your own patterns

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on real-world production patterns
- Inspired by Django community best practices
- Contributions from developers worldwide
- Enhanced for AI-assisted development with Claude

---

**Made with ❤️ for the Django community**

*This is a living document. Patterns evolve with Django versions and community feedback.*
