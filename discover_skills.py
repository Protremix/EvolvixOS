#!/usr/bin/env python3
"""
EvolvixOS — GitHub Skill Discovery CLI
Search, install, and learn from ALL open-source AI skills on GitHub.

Usage:
  python discover_skills.py discover          # Search GitHub for all AI skills
  python discover_skills.py install owner/repo # Install a specific skill
  python discover_skills.py install_all        # Auto-install top skills (100+ stars)
  python discover_skills.py learn owner/repo   # Learn how to use a skill
  python discover_skills.py learn_all          # Learn all installed skills
  python discover_skills.py catalog           # Show skill catalog
  python discover_skills.py update             # Update all installed skills
  python discover_skills.py auto              # Full auto: discover → install → learn
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from skills.github_discovery.skill import GitHubSkillDiscovery
from rich.console import Console

console = Console()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    discovery = GitHubSkillDiscovery(config={
        "skills_dir": "./skills",
        "cache_dir": "./data/github_cache",
    })

    if action == "discover":
        console.print("[bold cyan]🔍 Searching GitHub for ALL open-source AI skills...[/bold cyan]")
        results = discovery.discover_all(min_stars=50)
        console.print(f"\n[green]✅ Found {len(results)} new skills[/green]")
        discovery.get_skill_catalog()

    elif action == "install":
        if len(sys.argv) < 3:
            console.print("[red]Usage: python discover_skills.py install owner/repo[/red]")
            sys.exit(1)
        result = discovery.install_skill(sys.argv[2])
        console.print(result)

    elif action == "install_all":
        console.print("[bold cyan]📦 Installing all top skills from GitHub...[/bold cyan]")
        result = discovery.install_all_discovered(min_stars=100, max_install=50)
        console.print(f"\n[green]✅ Installed: {result['installed']}, Failed: {result['failed']}[/green]")

    elif action == "learn":
        if len(sys.argv) < 3:
            console.print("[red]Usage: python discover_skills.py learn owner/repo[/red]")
            sys.exit(1)
        result = discovery.learn_skill(sys.argv[2])
        console.print(result)

    elif action == "learn_all":
        console.print("[bold cyan]🧠 Learning all installed skills...[/bold cyan]")
        result = discovery.learn_all_installed()
        console.print(f"\n[green]✅ Learned {result['learned']} skills[/green]")

    elif action == "catalog":
        discovery.get_skill_catalog()

    elif action == "update":
        discovery.update_all()

    elif action == "auto":
        # Full autonomous cycle: discover → install → learn
        console.print("[bold cyan]🧬 Full auto-discovery cycle[/bold cyan]")
        console.print("=" * 50)

        console.print("\n[bold]Step 1: Discovering skills on GitHub...[/bold]")
        discovery.discover_all(min_stars=50)

        console.print("\n[bold]Step 2: Installing top skills...[/bold]")
        discovery.install_all_discovered(min_stars=100, max_install=20)

        console.print("\n[bold]Step 3: Learning how to use each skill...[/bold]")
        discovery.learn_all_installed()

        console.print("\n[bold]Step 4: Skill catalog:[/bold]")
        discovery.get_skill_catalog()

        console.print("\n[green]✅ EvolvixOS is now smarter![/green]")
        console.print(f"   Discovered: {len(discovery.registry['discovered'])}")
        console.print(f"   Installed: {len(discovery.registry['installed'])}")
        console.print(f"   Learned: {len(discovery.registry['learned'])}")

    else:
        print(f"Unknown action: {action}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
