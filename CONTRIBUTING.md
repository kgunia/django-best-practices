# Contributing to Django Best Practices

Thank you for considering contributing to this project! 🎉

This repository aims to be the most comprehensive collection of Django best practices for production applications. Your contributions help developers worldwide build better Django apps.

## How to Contribute

### Reporting Issues

Found a bug or have a suggestion? Please:

1. Check if the issue already exists
2. Create a new issue with:
   - Clear title and description
   - Code examples (if applicable)
   - Expected vs actual behavior
   - Python/Django versions

### Adding New Patterns

Have a Django pattern you use in production? Share it!

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/django-best-practices.git
   cd django-best-practices
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/new-pattern-name
   ```

3. **Add your pattern**
   
   Choose the appropriate file:
   - `SKILL.md` - For core, frequently-used patterns
   - `references/advanced_patterns.md` - For service layer, repositories, etc.
   - `references/query_optimization.md` - For database/performance patterns
   - `references/testing_patterns.md` - For testing examples
   - `references/code_quality.md` - For linting/typing/tools
   - `references/ajax_patterns.md` - For frontend integration patterns

4. **Follow the format**
   
   ```markdown
   ### Pattern Name
   
   **Brief description of what it does and when to use it.**
   
   ```python
   # ❌ Bad way
   bad_example()
   
   # ✅ Good way
   good_example()
   ```
   
   **Explanation:**
   - Why the good way is better
   - What problems it solves
   - When to use it
   ```

5. **Add working code examples**
   
   - Test your code examples work
   - Include imports
   - Use realistic variable names
   - Add comments where helpful

6. **Update SKILL.md if needed**
   
   If your pattern is core enough, add a brief mention in `SKILL.md` with a reference to the detailed docs.

7. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add pattern for [description]"
   ```
   
   Use conventional commits:
   - `feat:` for new patterns
   - `fix:` for corrections
   - `docs:` for documentation updates
   - `refactor:` for restructuring

8. **Push and create PR**
   ```bash
   git push origin feature/new-pattern-name
   ```
   
   Then open a Pull Request on GitHub with:
   - Description of the pattern
   - Why it's useful
   - Any related issues

## Code Style

### Python Code Examples

- Use Python 3.11+ features
- Include type hints
- Follow PEP 8
- Use English for docstrings and comments
- Test examples actually work

### Markdown

- Use `###` for pattern headings
- Include ❌ for bad examples, ✅ for good examples
- Keep lines under 100 characters
- Use code blocks with syntax highlighting

### Assets

Adding new ready-to-use code files:

1. Place in `assets/` directory
2. Include comprehensive docstrings
3. Add usage examples at the top
4. Update README.md to reference it

## What We're Looking For

### High Priority

- **Production patterns** - Things you actually use in real projects
- **Performance optimizations** - Query improvements, caching strategies
- **Testing patterns** - Pytest fixtures, mocking examples
- **Security practices** - Common vulnerabilities and fixes
- **Code quality tools** - Linter configs, CI/CD setups

### Medium Priority

- **Django 5.x features** - New patterns for latest Django
- **Third-party integrations** - Celery, Redis, etc.
- **Deployment patterns** - Docker, CI/CD, monitoring
- **API patterns** - DRF best practices

### Lower Priority

- Beginner tutorials (this is for best practices, not learning Django)
- Framework comparisons
- Opinion pieces without code

## Review Process

1. **Automated checks** - GitHub Actions will validate the skill structure
2. **Code review** - Maintainers will review for quality and clarity
3. **Discussion** - We may ask questions or request changes
4. **Merge** - Once approved, we'll merge and release

## Release Process

Releases follow semantic versioning:

- **Major** (3.0) - Breaking changes
- **Minor** (2.1) - New features
- **Patch** (2.0.1) - Bug fixes

## Questions?

- Open an issue for questions
- Tag with `question` label
- We'll respond as soon as possible

## Code of Conduct

Be respectful, constructive, and professional. We're all here to improve Django development!

## Recognition

Contributors will be:
- Listed in release notes
- Credited in commits
- Mentioned in README (for significant contributions)

Thank you for helping make Django development better! 🚀
