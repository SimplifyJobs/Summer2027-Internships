"""README generation and embedding functions."""

import re
from typing import Any

from list_updater.category import create_category_table, ensure_categories
from list_updater.constants import CATEGORIES, GITHUB_FILE_SIZE_LIMIT, SIZE_BUFFER
from list_updater.listings import filter_active, mark_stale_listings

type Listing = dict[str, Any]


def check_and_insert_warning(content: str, repo_name: str = "Summer2027-Internships") -> str:
    """Insert warning notice before GitHub cutoff point while preserving full content.

    Args:
        content: The README content.
        repo_name: The repository name for links.

    Returns:
        Content with warning inserted if necessary.
    """
    content_size = len(content.encode("utf-8"))

    if content_size <= (GITHUB_FILE_SIZE_LIMIT - SIZE_BUFFER):
        return content

    # Find insertion point right at the GitHub cutoff (with minimal buffer for the warning itself)
    # Use a smaller buffer so the warning appears right at the cutoff, not before it
    target_size = GITHUB_FILE_SIZE_LIMIT - SIZE_BUFFER

    # Convert to bytes for accurate measurement
    content_bytes = content.encode("utf-8")

    # Find the last complete table row before the limit
    insertion_bytes = content_bytes[:target_size]
    insertion_content = insertion_bytes.decode("utf-8", errors="ignore")
    limit_chars = len(insertion_content)

    # Split only where the FOLLOWING row starts a new company group. A "↳" row means "same
    # company as the row above", so reopening the table just before one would render a row
    # with no company name at all.
    rows = [m for m in re.finditer(r"<tr>\n(.*?)</tr>\n", content, re.S) if "<td>" in m.group(1)]

    def _is_continuation(match: re.Match[str]) -> bool:
        cells = re.findall(r"<td>(.*?)</td>", match.group(1), re.S)
        return bool(cells) and cells[0].strip() == "↳"

    insertion_point = None
    for index, match in enumerate(rows):
        if match.end() > limit_chars:
            break
        if index + 1 < len(rows) and _is_continuation(rows[index + 1]):
            continue
        insertion_point = match.end()

    if insertion_point is None:
        # No safe row boundary found; leave the content untouched rather than corrupt a table.
        return content

    # Create the warning notice with anchor link
    full_list_url = f"https://github.com/SimplifyJobs/{repo_name}/blob/dev/README.md#-see-full-list"
    simplify_jobs_url = (
        "https://simplify.jobs/jobs?category=Software%20Engineering%3BHardware%20Engineering"
        "%3BQuantitative%20Finance%3BProduct%20Management%3BData%20%26%20Analytics%3BIT%20%26%20Security"
        "&jobId=2ac81173-86b5-4dbd-a7a9-260847c259cc&jobType=Internship?utm_source=GHList"
    )
    warning_notice = f"""
</tbody>
</table>

---

<div align="center" id="github-cutoff-warning">
  <h2>🔗 See Full List</h2>
  <p><strong>⚠️ GitHub preview cuts off around here due to file size limits.</strong></p>
  <p>📋 <strong><a href="{full_list_url}">Click here to view the complete list with all internship opportunities!</a></strong> 📋</p>
  <p><em>To find even more internships in tech, check out <a href="{simplify_jobs_url}">Simplify's website</a>.</em></p>
</div>

---

<table>
<thead>
<tr>
<th>Company</th>
<th>Role</th>
<th>Location</th>
<th>Application</th>
<th>Age</th>
</tr>
</thead>
<tbody>
"""  # noqa: E501

    # Split content at insertion point and insert warning
    before_insertion = content[:insertion_point]
    after_insertion = content[insertion_point:]

    return before_insertion + warning_notice + after_insertion


def embed_table(
    listings: list[Listing],
    filepath: str,
    off_season: bool = False,
    active_only: bool = False,
    inactive_only: bool = False,
) -> None:
    """Embed the listings table into a README file.

    Args:
        listings: List of listing dictionaries.
        filepath: Path to the README file to modify.
        off_season: Whether this is for off-season listings.
        active_only: If True, only include active listings (no inactive sections).
        inactive_only: If True, only include inactive listings.
    """
    # Ensure all listings have a category
    listings = ensure_categories(listings)
    listings = mark_stale_listings(listings)

    # Filter listings based on active/inactive mode
    if inactive_only:
        filtered_listings = [listing for listing in listings if not listing.get("active", False)]
        total_count = len(filtered_listings)
    else:
        # For active_only or default, count active listings
        active_listings = filter_active(listings)
        total_count = len(active_listings)

    # Count listings by category
    category_counts: dict[str, int] = {}
    for category_info in CATEGORIES.values():
        cat_name = category_info["name"]
        if inactive_only:
            count = len(
                [
                    listing
                    for listing in listings
                    if listing["category"] == cat_name and not listing.get("active", False)
                ]
            )
        else:
            count = len(
                [listing for listing in listings if listing["category"] == cat_name and listing.get("active", False)]
            )
        category_counts[cat_name] = count

    # Build the category summary for the Browse section
    category_order = ["Software", "Product", "AI/ML/Data", "Quant", "Hardware"]
    category_links = []

    # Use the appropriate README file based on whether this is off-season or not
    if inactive_only:
        readme_filename = "README-Inactive.md"
    elif off_season:
        readme_filename = "README-Off-Season.md"
    else:
        readme_filename = "README.md"
    github_readme_base = f"https://github.com/SimplifyJobs/Summer2027-Internships/blob/dev/{readme_filename}"

    for category_key in category_order:
        if category_key in CATEGORIES:
            category_info = CATEGORIES[category_key]
            name = category_info["name"]
            emoji = category_info["emoji"]
            count = category_counts[name]
            anchor = name.lower().replace(" ", "-").replace(",", "").replace("&", "")
            if inactive_only:
                link = f"{github_readme_base}#-{anchor}-internship-roles-inactive"
            else:
                link = f"{github_readme_base}#-{anchor}-internship-roles"
            category_links.append(f"{emoji} **[{name}]({link})** ({count})")

    category_counts_str = "\n\n".join(category_links)

    new_text = ""
    in_browse_section = False
    browse_section_replaced = False
    in_table_section = False

    with open(filepath) as f:
        for line in f.readlines():
            if not browse_section_replaced and line.startswith("### Browse"):
                in_browse_section = True
                if inactive_only:
                    header = f"### Browse {total_count} Inactive Internship Roles by Category"
                else:
                    header = f"### Browse {total_count} Internship Roles by Category"
                new_text += f"{header}\n\n{category_counts_str}\n\n---\n"
                browse_section_replaced = True
                continue

            if in_browse_section:
                if line.startswith("---"):
                    in_browse_section = False
                continue

            if not in_table_section and "TABLE_START" in line:
                in_table_section = True
                new_text += line
                new_text += "\n---\n\n"

                # Add tables for each category in order
                for category_key in category_order:
                    if category_key in CATEGORIES:
                        category_info = CATEGORIES[category_key]
                        table = create_category_table(
                            listings,
                            category_info["name"],
                            off_season,
                            active_only=active_only,
                            inactive_only=inactive_only,
                        )
                        if table:
                            new_text += table
                continue

            if in_table_section:
                if "TABLE_END" in line:
                    in_table_section = False
                    new_text += line
                continue

            if not in_browse_section and not in_table_section:
                new_text += line

    # Check content size and insert warning if necessary (only for main README, not inactive)
    if not inactive_only:
        final_content = check_and_insert_warning(new_text)
    else:
        final_content = new_text

    with open(filepath, "w") as f:
        f.write(final_content)
