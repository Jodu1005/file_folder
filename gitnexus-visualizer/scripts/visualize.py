#!/usr/bin/env python3
"""
GitNexus Visualizer - End-to-End Code Visualization
Automatically indexes projects with GitNexus and generates Mermaid diagrams.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_step(step_num, total_steps, message):
    """Print a formatted step message"""
    print(f"\n[{step_num}/{total_steps}] {message}")


def check_dependencies():
    """Check if required tools are installed"""
    issues = []

    # Check Node.js/npx
    if not shutil.which('npx'):
        issues.append("npx (Node.js) - Install from https://nodejs.org")

    # Check Python kuzu
    try:
        import kuzu
    except ImportError:
        issues.append("kuzu Python package - Run: pip install kuzu")

    return issues


def find_git_root(start_path):
    """Find the git repository root directory"""
    current = Path(start_path).resolve()

    # If current path is a file, start from its directory
    if current.is_file():
        current = current.parent

    # Walk up parents looking for .git
    for parent in [current] + list(current.parents):
        if (parent / '.git').exists():
            return parent

    return None


def run_gitnexus_analyze(project_path, force=False):
    """Run GitNexus analyze on the project"""
    cmd = ['npx', 'gitnexus', 'analyze']
    if force:
        cmd.append('--force')

    print(f"  Running: {' '.join(cmd)}")
    print(f"  This may take 2-3 minutes...")

    result = subprocess.run(
        cmd,
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        return False

    print(f"  {result.stdout}")
    return True


def check_gitnexus_status(project_path):
    """Check if GitNexus index exists and is up to date"""
    gitnexus_dir = os.path.join(project_path, '.gitnexus')

    if not os.path.exists(gitnexus_dir):
        return None  # No index

    # Check status
    result = subprocess.run(
        ['npx', 'gitnexus', 'status'],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return None

    output = result.stdout
    if 'up-to-date' in output.lower() or '✅' in output:
        return True  # Index is fresh
    elif 'stale' in output.lower() or '❌' in output:
        return False  # Index needs update

    return True  # Assume good if unclear


def run_converter(project_path):
    """Run the Kuzu to Mermaid converter"""
    gitnexus_dir = os.path.join(project_path, '.gitnexus')
    script_path = os.path.join(os.path.dirname(__file__), 'kuzu_to_mermaid.py')

    if not os.path.exists(script_path):
        print(f"  Error: Converter script not found at {script_path}")
        return False

    # Copy script to .gitnexus directory
    target_script = os.path.join(gitnexus_dir, 'kuzu_to_mermaid.py')
    shutil.copy(script_path, target_script)

    # Run the converter
    print(f"  Running converter...")
    result = subprocess.run(
        [sys.executable, target_script, gitnexus_dir],
        cwd=gitnexus_dir,
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(f"  stderr: {result.stderr}")

    return result.returncode == 0


def main():
    """Main workflow"""
    print("="*70)
    print("GitNexus Visualizer - End-to-End Code Visualization")
    print("="*70)

    # Parse arguments
    project_path = None
    force_reindex = False

    args = sys.argv[1:]
    while args:
        arg = args.pop(0)
        if arg == '--force' or arg == '-f':
            force_reindex = True
        elif arg == '--help' or arg == '-h':
            print(__doc__)
            print("""
Usage: python visualize.py [project_path] [--force]

Arguments:
  project_path    Path to the project (default: current directory)
  --force, -f     Force re-indexing with GitNexus

Examples:
  python visualize.py                          # Visualize current directory
  python visualize.py ~/code/my-project       # Visualize specific project
  python visualize.py --force                 # Re-index and visualize
            """)
            return
        else:
            project_path = arg

    # Use current directory if no path specified
    if project_path is None:
        project_path = os.getcwd()

    # Step 1: Validate project path
    print_step(1, 5, f"Validating project: {project_path}")

    project_path = os.path.abspath(project_path)
    if not os.path.exists(project_path):
        print(f"  Error: Path does not exist: {project_path}")
        return 1

    git_root = find_git_root(project_path)
    if not git_root:
        print(f"  Error: Not a git repository: {project_path}")
        print(f"  GitNexus only works with git repositories")
        return 1

    print(f"  Git repository found: {git_root}")
    project_path = str(git_root)

    # Step 2: Check dependencies
    print_step(2, 5, "Checking dependencies")

    missing = check_dependencies()
    if missing:
        print("  Missing required tools:")
        for item in missing:
            print(f"    - {item}")
        print("\n  Please install missing dependencies and try again")
        return 1

    print("  All dependencies OK")

    # Step 3: Check GitNexus index
    print_step(3, 5, "Checking GitNexus index")

    index_status = check_gitnexus_status(project_path)

    if index_status is None:
        print("  No GitNexus index found")
        print("  Will create new index...")
        if not run_gitnexus_analyze(project_path):
            return 1
    elif index_status is False or force_reindex:
        print("  GitNexus index is stale" if not force_reindex else "  Forced re-index")
        print("  Will update index...")
        if not run_gitnexus_analyze(project_path, force=True):
            return 1
    else:
        print("  GitNexus index is up-to-date")

    # Step 4: Generate Mermaid diagrams
    print_step(4, 5, "Generating Mermaid diagrams")

    if not run_converter(project_path):
        return 1

    # Step 5: Show results
    output_dir = os.path.join(project_path, '.gitnexus', 'mermaid图')
    print_step(5, 5, "Complete!")

    print("\n" + "="*70)
    print("SUCCESS!")
    print("="*70)
    print(f"\nOutput directory: {output_dir}")
    print("\nGenerated files:")
    print("  - 00_OVERVIEW_summary.mmd      (Statistics overview)")
    print("  - 01_CALLS_functions.mmd       (Function calls)")
    print("  - 02_EXTENDS_classes.mmd       (Class inheritance)")
    print("  - 03_DEFINES_files.mmd        (File definitions)")
    print("  - 04_MEMBER_OF_classes.mmd    (Class members)")
    print("  - 05_IMPORTS_files.mmd        (Import dependencies)")
    print("  - 06_CONTAINS.mmd             (Containment)")
    print("  - 07_STEP_IN_PROCESS.mmd      (Execution flows)")
    print("  - 08_COMMUNITY_modules.mmd    (Functional modules)")
    print("  - 99_COMPLETE_all_relations.mmd (All-in-one)")
    print("  - README.md                    (Index and guide)")
    print("\nHow to view:")
    print("  1. Visit https://mermaid.live")
    print("  2. Copy content of any .mmd file")
    print("  3. Paste into the editor")
    print("="*70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
