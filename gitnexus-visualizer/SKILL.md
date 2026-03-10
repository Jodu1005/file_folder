---
name: gitnexus-visualizer
description: Automatically visualize any codebase using GitNexus + Mermaid. Use this skill when the user wants to visualize code architecture, generate code relationship diagrams, create visual documentation of a project, see function calls and class inheritance, or transform code analysis into viewable charts. Works on any project - it will automatically index if needed, then generate Mermaid diagrams.
---

# GitNexus Visualizer

Automatically visualize any codebase as Mermaid diagrams.

## Quick Start

Simply tell the skill what project to visualize:

```
"Visualize the code architecture of /path/to/project"
"Generate Mermaid diagrams for this codebase"
"Show me the code relationships in my project"
```

The skill handles everything automatically.

## What This Skill Does

### End-to-End Workflow

```
1. Accept project path (or use current workspace)
   ↓
2. Check if GitNexus index exists
   ↓
3. If no index: Run `npx gitnexus analyze` automatically
   ↓
4. Convert Kuzu database to Mermaid diagrams
   ↓
5. Generate 10+ diagram files
   ↓
6. Provide viewing instructions
```

### Generated Diagrams

All output to `.gitnexus/mermaid图/`:

| File | Content |
|------|---------|
| `00_OVERVIEW_summary.mmd` | Database statistics overview |
| `01_CALLS_functions.mmd` | Function call relationships |
| `02_EXTENDS_classes.mmd` | Class inheritance hierarchy |
| `03_DEFINES_files.mmd` | File definitions |
| `04_MEMBER_OF_classes.mmd` | Class members |
| `05_IMPORTS_files.mmd` | Import dependencies |
| `06_CONTAINS.mmd` | Containment relationships |
| `07_STEP_IN_PROCESS.mmd` | Execution flows |
| `08_COMMUNITY_modules.mmd` | Auto-detected modules |
| `99_COMPLETE_all_relations.mmd` | **All relationships in one chart** |
| `README.md` | Index and viewing guide |

## Usage

### From Current Workspace

```
"Visualize this codebase"
"Generate code diagrams for the current project"
```

### From Specific Path

```
"Visualize /path/to/project"
"Generate diagrams for ~/code/my-project"
```

### With Options

```
"Visualize the project and force re-index"
"Generate diagrams with full analysis"
```

## Requirements

- Node.js (for `npx gitnexus analyze`)
- Python 3.x with `kuzu` package (`pip install kuzu`)

The skill will check these and guide if missing.

## Viewing Results

After generation, visit https://mermaid.live and paste any `.mmd file content.

## How It Works

1. **Project Detection**: Identifies git repository from input or current directory
2. **Index Check**: Runs `npx gitnexus status` to check if index exists
3. **Auto-Index**: If needed, runs `npx gitnexus analyze` to build knowledge graph
4. **Conversion**: Uses bundled Python script to query Kuzu database
5. **Generation**: Creates Mermaid files for each relationship type
6. **Index**: Auto-generates README.md with file descriptions

## Key Features

- **Zero-config**: Works on any git repository automatically
- **Auto-indexing**: Runs GitNexus if index doesn't exist
- **Smart detection**: Finds `.gitnexus` directory automatically
- **Complete visualization**: All relationship types, not just calls
- **Color-coded**: Different node types have distinct colors
- **Organized output**: Separate files + all-in-one overview

## Workflow Examples

### Example 1: Current Workspace

```
User: "Show me the code architecture"

Skill detects: /current/workspace
Checks: .gitnexus exists? YES
Generates: Mermaid diagrams in .gitnexus/mermaid图/
Shows: Path and viewing instructions
```

### Example 2: New Project

```
User: "Visualize ~/code/python-project"

Skill detects: ~/code/python-project
Checks: .gitnexus exists? NO
Runs: npx gitnexus analyze (2-3 minutes)
Generates: Mermaid diagrams
Shows: Complete results
```

### Example 3: Force Re-index

```
User: "Re-analyze and visualize the project"

Skill runs: npx gitnexus analyze --force
Generates: Fresh diagrams from updated index
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "npx not found" | Install Node.js from nodejs.org |
| "kuzu module not found" | Run `pip install kuzu` |
| "Not a git repository" | Ensure project path is a git repo |
| "Index stale" | Skill auto-reindexes, or use `--force` flag |

## Architecture

```
Input: Project Path
   ↓
GitNexus (npx gitnexus analyze)
   ↓
Kuzu Database (.gitnexus/kuzu)
   ↓
Python Converter (scripts/kuzu_to_mermaid.py)
   ↓
Mermaid Files (.mmd)
   ↓
https://mermaid.live (visualization)
```
