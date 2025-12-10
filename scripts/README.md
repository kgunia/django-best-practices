# Scripts

Utility scripts for this repository.

## build_skill.py

Builds a Claude AI Skill file from the repository contents.

**Usage:**
```bash
python scripts/build_skill.py
```

**Output:**
- `django-best-practices.skill` - Packaged skill file

**What it does:**
1. Packages SKILL.md, references/, and assets/ into a .skill file
2. The .skill file is just a zip archive with a specific structure
3. Can be uploaded to Claude AI for automated assistance

**Note:** You can also download pre-built .skill files from the [Releases](https://github.com/yourusername/django-best-practices/releases) page.

## Future Scripts

Ideas for additional scripts:
- `validate.py` - Validate skill structure locally
- `update_version.py` - Bump version numbers
- `generate_toc.py` - Generate table of contents
- `export_pdf.py` - Export documentation as PDF

Contributions welcome!
