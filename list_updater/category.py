"""Job category classification and management functions."""

import re
from typing import Any

from list_updater.constants import CATEGORIES
from list_updater.formatter import create_md_table

type Listing = dict[str, Any]

# Short keywords that need word boundary matching to avoid false positives
# (e.g., "ai" should not match "maintenance", "ml" should not match "html")
WORD_BOUNDARY_KEYWORDS = frozenset({"ai", "ml", "rf", "qa", "sre", "swe", "sde", "api"})


def _matches_keyword(title: str, keyword: str) -> bool:
    """Check if a keyword matches in the title.

    Uses word boundary matching for short keywords to avoid false positives.

    Args:
        title: The lowercased job title.
        keyword: The keyword to search for.

    Returns:
        True if the keyword matches in the title.
    """
    if keyword in WORD_BOUNDARY_KEYWORDS:
        return bool(re.search(rf"\b{re.escape(keyword)}\b", title))
    return keyword in title


def classify_job_category(job: Listing) -> str | None:
    """Classify a job into a category based on its title.

    Args:
        job: A job listing dictionary.

    Returns:
        The category name, or None if the job should be filtered out.
    """
    title = job.get("title", "").lower()

    # Filter out IT technical support roles that aren't really tech internships
    if any(
        _matches_keyword(title, term)
        for term in [
            "it technical intern",
            "it technician",
            "it support",
            "technical support intern",
            "help desk",
            "desktop support",
            "it help desk",
            "computer support",
            "security operations",
            "field operations",
            "information technology",
        ]
    ):
        return None

    # Hardware (first priority) - expanded keywords
    if any(
        _matches_keyword(title, term)
        for term in [
            "hardware",
            "embedded",
            "fpga",
            "circuit",
            "chip",
            "silicon",
            "asic",
            "robotics",
            "firmware",
            "manufactur",
            "electrical",
            "mechanical",
            "systems engineer",
            "test engineer",
            "validation",
            "verification",
            "pcb",
            "analog",
            "digital",
            "signal",
            "power",
            "rf",
            "antenna",
        ]
    ):
        return "Hardware Engineering"

    # Quant (second priority) - expanded keywords
    if any(
        _matches_keyword(title, term)
        for term in [
            "quant",
            "quantitative",
            "trading",
            "finance",
            "investment",
            "financial",
            "risk",
            "portfolio",
            "derivatives",
            "algorithmic trading",
            "market",
            "capital",
            "equity",
            "fixed income",
            "credit",
        ]
    ):
        return "Quantitative Finance"

    # Data Science (third priority) - expanded keywords
    if any(
        _matches_keyword(title, term)
        for term in [
            "data science",
            "artificial intelligence",
            "data scientist",
            "ai",
            "machine learning",
            "ml",
            "data analytics",
            "data analyst",
            "research eng",
            "nlp",
            "computer vision",
            "research sci",
            "data eng",
            "analytics",
            "statistician",
            "modeling",
            "algorithms",
            "deep learning",
            "pytorch",
            "tensorflow",
            "pandas",
            "numpy",
            "sql",
            "etl",
            "pipeline",
            "big data",
            "spark",
            "hadoop",
        ]
    ):
        return "Data Science, AI & Machine Learning"

    # Product (fourth priority) - check before Software to catch "Software Product Management" roles
    if any(
        _matches_keyword(title, term)
        for term in [
            "product manag",
            "product analyst",
            "apm",
            "associate product",
            "product owner",
            "product design",
            "product marketing",
            "product strategy",
            "business analyst",
            "program manag",
            "project manag",
        ]
    ) or ("product" in title and any(word in title for word in ["analyst", "manager", "associate", "coordinator"])):
        return "Product Management"

    # Software Engineering (fifth priority) - greatly expanded keywords
    if any(
        _matches_keyword(title, term)
        for term in [
            "software",
            "engineer",
            "developer",
            "dev",
            "programming",
            "coding",
            "fullstack",
            "full-stack",
            "full stack",
            "frontend",
            "front end",
            "front-end",
            "backend",
            "back end",
            "back-end",
            "mobile",
            "web",
            "app",
            "application",
            "platform",
            "infrastructure",
            "cloud",
            "devops",
            "sre",
            "site reliability",
            "systems",
            "network",
            "security",
            "cybersecurity",
            "qa",
            "quality assurance",
            "test",
            "automation",
            "ci/cd",
            "deployment",
            "kubernetes",
            "docker",
            "aws",
            "azure",
            "gcp",
            "api",
            "microservices",
            "database",
            "java",
            "python",
            "javascript",
            "react",
            "node",
            "golang",
            "rust",
            "c++",
            "c#",
            ".net",
            "ios",
            "android",
            "flutter",
            "technical",
            "technology",
            "tech",
            "coding",
            "programming",
            "sde",
            "swe",
        ]
    ):
        return "Software Engineering"

    # Default to Software Engineering for jobs that don't fit any category
    return "Software Engineering"


def ensure_categories(listings: list[Listing], verbose: bool = False) -> list[Listing]:
    """Ensure all listings have a valid category assigned.

    Args:
        listings: List of listing dictionaries.
        verbose: If True, print details about filtered jobs.

    Returns:
        List of categorized listings (some may be filtered out).
    """
    categorized_listings: list[Listing] = []
    filtered_jobs: list[Listing] = []

    # Create mapping from old category names to new category names
    category_mapping = {
        "Software": "Software Engineering",
        "Product": "Product Management",
        "AI/ML/Data": "Data Science, AI & Machine Learning",
        "Quant": "Quantitative Finance",
        "Hardware": "Hardware Engineering",
    }

    for listing in listings:
        # If listing already has a category, normalize it to full category name
        if "category" in listing and listing["category"]:
            existing_category = listing["category"]
            # Normalize old category names to new full names
            if existing_category in category_mapping:
                listing["category"] = category_mapping[existing_category]
                categorized_listings.append(listing)
            # Re-classify jobs with "Other" or invalid categories
            elif existing_category in ["Other", "None", None]:
                category = classify_job_category(listing)
                if category is not None:
                    listing["category"] = category
                    categorized_listings.append(listing)
                else:
                    filtered_jobs.append(listing)
            else:
                # Keep jobs with valid full category names
                categorized_listings.append(listing)
        else:
            # Only auto-classify if no category exists
            category = classify_job_category(listing)
            if category is not None:  # Only keep jobs that fit our categories
                listing["category"] = category
                categorized_listings.append(listing)
            else:
                filtered_jobs.append(listing)

    if filtered_jobs:
        print(f"Filtered out {len(filtered_jobs)} excluded roles (IT support, help desk, etc.)")
        if verbose:
            for job in filtered_jobs[:10]:  # Show first 10
                print(f"  - [{job.get('company_name')}] {job.get('title', 'No title')}")
            if len(filtered_jobs) > 10:
                print(f"  ... and {len(filtered_jobs) - 10} more")

    return categorized_listings


def create_category_table(
    listings: list[Listing],
    category_name: str,
    off_season: bool = False,
    active_only: bool = False,
    inactive_only: bool = False,
) -> str:
    """Create a table section for a specific category.

    Args:
        listings: List of listing dictionaries.
        category_name: The category name to filter by.
        off_season: Whether this is for off-season listings.
        active_only: If True, only include active listings (no inactive section).
        inactive_only: If True, only include inactive listings.

    Returns:
        HTML/markdown string for the category section.
    """
    category_listings = [listing for listing in listings if listing["category"] == category_name]
    if not category_listings:
        return ""

    emoji = next((cat["emoji"] for cat in CATEGORIES.values() if cat["name"] == category_name), "")

    # Different header for inactive-only page
    if inactive_only:
        header = f"\n\n## {emoji} {category_name} Internship Roles (Inactive)\n\n"
        header += "[Back to top](#summer-2027-tech-internships-inactive-listings)\n\n"
    else:
        header = f"\n\n## {emoji} {category_name} Internship Roles\n\n"
        header += "[Back to top](#summer-2027-tech-internships-by-pitt-csc--simplify)\n\n"

    # Optional callout under Data Science section (only for active listings)
    if not inactive_only and category_name == "Data Science, AI & Machine Learning":
        resume_url = "https://docs.google.com/document/d/1azvJt51U2CbpvyO0ZkICqYFDhzdfGxU_lsPQTGhsn94/edit?usp=sharing"
        header += (
            f"> 📄 Here's the [resume template]({resume_url}) "
            "used by Stanford CS and Pitt CSC for internship prep.\n"
            "\n"
            "> 🧠 Want to know what keywords your resume is missing for a job? "
            "Use the blue Simplify application link to instantly compare your resume to any job description.\n\n"
        )

    if not inactive_only and category_name == "Product Management":
        tracker_url = "https://simplify.jobs/top-list/Associate-Product-Manager-Intern?utm_source=GHList&utm_medium=ot"
        header += (
            "> 📅 Curious when Big Tech product internships typically open? Simplify put together an "
            f"[openings tracker]({tracker_url}) based on historical data for those companies.\n"
            "\n"
        )

    # Sort and format
    active = sorted(
        [listing for listing in category_listings if listing["active"]],
        key=lambda x: x["date_posted"],
        reverse=True,
    )
    inactive = sorted(
        [listing for listing in category_listings if not listing["active"]],
        key=lambda x: x["date_posted"],
        reverse=True,
    )

    result = header

    if inactive_only:
        # Only show inactive listings (for separate inactive README)
        if inactive:
            result += create_md_table(inactive, off_season) + "\n\n"
        else:
            return ""  # No inactive listings in this category
    elif active_only:
        # Only show active listings (no collapsed inactive section)
        if active:
            result += create_md_table(active, off_season) + "\n\n"
            # Add link to inactive listings if there are any
            if inactive:
                anchor = category_name.lower().replace(" ", "-").replace(",", "").replace("&", "")
                inactive_url = f"https://github.com/SimplifyJobs/Summer2027-Internships/blob/dev/README-Inactive.md#-{anchor}-internship-roles-inactive"
                result += f"🔒 **[See {len(inactive)} more closed roles →]({inactive_url})**\n\n"
        else:
            return ""  # No active listings in this category
    else:
        # Original behavior: active + collapsed inactive
        if active:
            result += create_md_table(active, off_season) + "\n\n"

        if inactive:
            result += (
                "<details>\n"
                f"<summary>🗃️ Inactive roles ({len(inactive)})</summary>\n\n"
                + create_md_table(inactive, off_season)
                + "\n\n</details>\n\n"
            )

    return result
