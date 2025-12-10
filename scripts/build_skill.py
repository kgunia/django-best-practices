#!/usr/bin/env python3
"""
Build Claude AI Skill from this repository.

This script packages the repository contents into a .skill file
that can be uploaded to Claude AI for automated assistance.

Usage:
    python scripts/build_skill.py
    
The .skill file will be created in the project root.
"""

import zipfile
from pathlib import Path


def build_skill():
    """Build .skill file from repository contents."""
    
    # Define paths
    repo_root = Path(__file__).parent.parent
    skill_name = "django-best-practices"
    output_file = repo_root / f"{skill_name}.skill"
    
    # Files to include in skill
    include_patterns = [
        "SKILL.md",
        "references/*.md",
        "assets/*.py",
        "assets/*.toml",
        "assets/*.ini",
        "assets/*.yaml",
    ]
    
    print(f"Building {skill_name}.skill...")
    print(f"Repository: {repo_root}")
    
    # Create skill (it's just a zip file)
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as skill_zip:
        # Add SKILL.md (required)
        skill_md = repo_root / "SKILL.md"
        if skill_md.exists():
            skill_zip.write(skill_md, f"{skill_name}/SKILL.md")
            print(f"  ✓ Added SKILL.md")
        else:
            print(f"  ✗ ERROR: SKILL.md not found!")
            return False
        
        # Add references
        references_dir = repo_root / "references"
        if references_dir.exists():
            for ref_file in references_dir.glob("*.md"):
                skill_zip.write(
                    ref_file,
                    f"{skill_name}/references/{ref_file.name}"
                )
                print(f"  ✓ Added references/{ref_file.name}")
        
        # Add assets
        assets_dir = repo_root / "assets"
        if assets_dir.exists():
            for asset_file in assets_dir.iterdir():
                if asset_file.is_file():
                    skill_zip.write(
                        asset_file,
                        f"{skill_name}/assets/{asset_file.name}"
                    )
                    print(f"  ✓ Added assets/{asset_file.name}")
    
    print(f"\n✅ Skill built successfully: {output_file}")
    print(f"   Size: {output_file.stat().st_size / 1024:.1f} KB")
    print(f"\nTo use:")
    print(f"1. Go to https://claude.ai")
    print(f"2. Open your Project")
    print(f"3. Upload {output_file.name}")
    
    return True


if __name__ == "__main__":
    build_skill()
