# Contributing to the Internship List
Thank you for your interest in contributing to the Pitt CSC and Simplify internship list!

Below, you'll find the guidelines for our repository. If you have any questions, please create a [miscellaneous issue](https://github.com/SimplifyJobs/Summer2027-Internships/issues/new/choose).

## Finding an Internship to Add
We ask that the internships that you add meet some requirements. Specifically, your internship must
- be in one of the following categories:
    - **Software Engineering** - Software development, computer engineering, full-stack, frontend, backend, mobile development
    - **Product Management** - Product manager, associate product manager (APM), product analyst roles
    - **Data Science, AI & Machine Learning** - Data science, machine learning, AI research, data engineering, analytics
    - **Quantitative Finance** - Quantitative trading, quantitative research, fintech engineering
    - **Hardware Engineering** - Hardware design, embedded systems, firmware, FPGA, circuit design
    - **Other** - Any other tech-related internships that don't fit the above categories
- be located in the United States, Canada, or remote.
- not already exist in the internship list.
- belong to a company using a formal ATS such as Workday, Greenhouse, Ashby, etc.
    - any company using non-ATS platforms such as forms or surveys must be verified/approved on Simplify.

## Adding an Internship
Cool! You're ready to add an internship to the list. Follow these steps:

1) First create a new issue [here](https://github.com/SimplifyJobs/Summer2027-Internships/issues/new/choose).
2) Select the **New Internship** issue template.
3) Fill in the information about your internship into the form, including:
   - **Category**: Choose the appropriate category from the dropdown (Software Engineering, Product Management, etc.)
   - **Advanced Degree Requirements**: Check this box if the internship specifically requires or prefers Master's, MBA, or PhD degrees
   - All other required fields (company, title, location, etc.)
4) Hit submit.
> Please make a new submission for each unique position, **even if they are for the same company**.
5) That's it! Once a member of our team has reviewed your submission, it will be automatically added to the correct `README` with proper categorization and degree indicators

## Editing an Internship
To edit an internship (changing name, setting as inactive, removing, etc.), follow these steps:
1) First copy the url of the internship you would like to edit.
> This can be found by right-clicking on the `APPLY` button and selecting **copy link address**
2) Create a new issue [here](https://github.com/SimplifyJobs/Summer2027-Internships/issues/new/choose).
3) Select the **Edit Internship** issue template.
4) Fill in the url to the **link** input.
> This is how we ensure your edit affects the correct internship
5) Leave every other input blank except for whichever fields you would like to update or change about the internship, including:
   - **Category**: Change the internship category if needed
   - **Advanced Degree Requirements**: Check or uncheck if the degree requirements have changed
   - Any other fields you want to modify
6) If it is not obvious why you are making these edits, please specify why in the reason box at the bottom of the form.
7) Hit submit. A member of our team will review your revision and approve it shortly.

## Automatic README.md Updates
A script will automatically add new contributions as well as new internships found by [Simplify](https://simplify.jobs) to the appropriate README. Internships will be:

- **Categorized** into the appropriate section (Software Engineering, Product Management, Data Science, etc.)
- **Marked with special indicators**:
  - 🔥 for FAANG+ companies (Google, Meta, Apple, Amazon, Microsoft, etc.)
  - 🎓 for roles requiring advanced degrees (Master's/MBA/PhD)
  - 🛂 for roles that don't offer sponsorship
  - 🇺🇸 for roles requiring U.S. citizenship

The row will look something like this:
```md
| Company | Role | Location | Application | Age |
| --- | --- | --- | :---: | :---: |
| 🔥 **[Google](https://google.com)** | Software Engineering Internship 🎓 | San Francisco, CA | <a href="..."><img src="..." alt="Apply"></a> | 2d |
```

When rendered, it will look like:
| Company | Role | Location | Application | Age |
| --- | --- | --- | :---: | :---: |
| 🔥 **[Google](https://google.com)** | Software Engineering Internship 🎓 | San Francisco, CA | <a href="..."><img src="..." alt="Apply"></a> | 2d |

---

## Maintainer Guide

This section is for maintainers who need to understand how the repository operates behind the scenes.

### High Level Overview

Internships are stored in `.github/scripts/listings.json`. This file is edited by:
1. Submitting a `new_internship` or `edit_internship` issue form
2. An external microservice that runs daily to fetch internships from Simplify's database

Once an `approved` label is attached to an issue, a GitHub Action automatically edits `listings.json` with the new information. Every time `listings.json` is updated, another GitHub Action called "Update READMEs" updates the README files with the new internships.

### listings.json Schema

All internships are stored in `.github/scripts/listings.json`. A listing entry looks like:

```json
{
    "company_name": "Capital One",
    "locations": ["McLean, VA", "Plano, TX"],
    "title": "Product Development Intern",
    "date_posted": 1690430400,
    "terms": ["Summer 2024"],
    "active": true,
    "url": "https://example.com/job/123",
    "is_visible": true,
    "source": "Simplify",
    "company_url": "",
    "date_updated": 1690430400,
    "id": "98b2d671-3f03-430e-b18c-e5ddb8ce5035"
}
```

| Property | Type | Description |
|----------|------|-------------|
| `company_name` | `str` | Name of company |
| `company_url` | `str` | Link to Simplify page (empty for contributions) |
| `title` | `str` | Name of internship position |
| `date_posted` | `int` | Unix timestamp when added |
| `date_updated` | `int` | Unix timestamp when last updated |
| `url` | `str` | Link to job posting |
| `terms` | `[str]` | Array of terms (e.g., `["Summer 2024"]`) |
| `locations` | `[str]` | Array of locations |
| `active` | `bool` | `true` if application is open |
| `is_visible` | `bool` | `true` if visible in README |
| `source` | `str` | `Simplify` or GitHub username of contributor |
| `id` | `str` | Unique identifier |

### GitHub Issue Templates

Issue templates are in `.github/ISSUE_TEMPLATE/`:

| Template | File | Purpose | Label |
|----------|------|---------|-------|
| New Internship | `new_internship.yaml` | Add a new internship | `new_internship` |
| Edit Internship | `edit_internship.yaml` | Update existing internship | `edit_internship` |
| Bulk Mark Inactive | `bulk_mark_inactive.yaml` | Mark multiple listings inactive | `bulk_mark_inactive` |
| Miscellaneous | `misc.yaml` | Questions, bugs, etc. | `misc` |
| Feature Suggestion | `feature_suggestion.yaml` | Improvements to repo | `enhancement` |

### Processing Issues

1. Review the submission to ensure fields are correct and the internship fits the repo theme
2. If issues exist, respond explaining what needs to be changed
3. If no issues, add the `approved` label to trigger the GitHub Action
4. If the action fails, it will comment on the issue with the error
5. If successful, the issue is auto-closed and changes are reflected in `listings.json`

### GitHub Actions

**Contribution Approved** (`.github/workflows/contribution_approved.yml`):
- Triggered when `approved` label is added to an issue
- Runs `main.py contribution process` to extract issue data and update `listings.json`
- Commits changes with contributor attribution
- Auto-closes the issue

**Update READMEs** (`.github/workflows/update_readmes.yml`):
- Triggered on changes to `listings.json` or manually
- Runs `main.py readme update` to regenerate README tables
- Commits and pushes changes

**Lint** (`.github/workflows/lint.yml`):
- Triggered on changes to Python code
- Runs ruff and mypy checks

### External Script

A private script runs externally once per day to:
1. Pull new internships from Simplify's database
2. Add them to `listings.json`

---

## Code Contribution

This section is for developers who want to contribute to the codebase itself (the list-updater CLI tool).

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

From the repository root:

```bash
uv sync
```

### CLI Usage

```bash
uv run python main.py <group> <command> [options]
```

The CLI uses grouped subcommands. Use `--help` on any command for details:

```bash
uv run python main.py --help
uv run python main.py listings --help
```

#### README Commands

```bash
# Update README files from listings.json
uv run python main.py readme update
```

#### Contribution Commands

```bash
# Process an approved contribution issue
uv run python main.py contribution process <event_file>
```

#### Listings Commands

```bash
# Bulk mark listings as inactive
uv run python main.py listings mark-inactive <event_file>

# Show listing statistics
uv run python main.py listings stats
uv run python main.py listings stats --json

# Validate listings.json schema and data
uv run python main.py listings validate
uv run python main.py listings validate --fix

# Search and filter listings
uv run python main.py listings search --company "Google"
uv run python main.py listings search --category "Software" --active
uv run python main.py listings search --location "Remote" --limit 50

# Show changes since a date or commit
uv run python main.py listings diff
uv run python main.py listings diff --since "2025-01-01"
uv run python main.py listings diff --commit abc123

# Interactively fix issues in listings.json
uv run python main.py listings fix
uv run python main.py listings fix --dry-run          # Preview without saving
uv run python main.py listings fix --type empty       # Only fix empty fields
uv run python main.py listings fix --type duplicate   # Only fix duplicates
uv run python main.py listings fix --auto             # Auto-accept all recommended fixes
uv run python main.py listings fix --auto --dry-run   # Preview auto-fixes
```

The `fix` command walks through issues one-by-one, prompting for action:
- Empty titles: fix, hide, delete, or skip
- Invalid categories: set to "Other" or custom
- Duplicate URLs/IDs: choose which to keep (prefers Simplify-sourced listings)
- Blocked companies: hide or delete

### Project Structure

```
/
├── main.py                      # CLI entry point (Typer)
├── pyproject.toml               # Project configuration
├── list_updater/                # Core library
│   ├── __init__.py
│   ├── analytics.py             # Stats, validate, search, diff commands
│   ├── category.py              # Job category classification
│   ├── commands.py              # Core CLI commands
│   ├── constants.py             # Configuration constants
│   ├── formatter.py             # Table/markdown formatting
│   ├── github.py                # GitHub Actions utilities
│   ├── listings.py              # Listing data operations
│   └── readme.py                # README generation
└── .github/
    └── scripts/
        └── listings.json        # Internship data
```

### Development

#### Linting

```bash
uv run ruff check .
uv run ruff format .
```

#### Type Checking

```bash
uv run mypy .
```

### GitHub Actions Integration

The CLI is used in GitHub Actions workflows:

```yaml
- name: Process contribution
  run: uv run main.py contribution process $GITHUB_EVENT_PATH

- name: Update READMEs
  run: uv run main.py readme update
```

Outputs are set via `GITHUB_OUTPUT`:
- `commit_message`: Suggested commit message
- `commit_email`: Contributor email (for attribution)
- `commit_username`: Contributor username
- `summary_comment`: Summary for bulk operations
- `error_message`: Error details (on failure)