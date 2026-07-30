"""CLI command implementations for the list updater."""

import json
import re
import uuid
from datetime import datetime
from typing import Any

from list_updater.category import classify_job_category
from list_updater.constants import CATEGORY_MAPPING
from list_updater.github import fail, set_output
from list_updater.listings import (
    check_schema,
    filter_off_season,
    filter_summer,
    get_listings_from_json,
    sort_listings,
)
from list_updater.readme_generator import embed_table

# Constants for contribution processing
NO_ANSWER: set[str] = {"", "no response", "_no response_", "none", "n/a", "na", "-"}
YES_VALUES: set[str] = {"yes", "y", "true", "open"}
NO_VALUES: set[str] = {"no", "n", "false", "closed"}

type ResultDict = dict[str, dict[str, str]]


# =============================================================================
# README Commands
# =============================================================================


def cmd_readme_update() -> None:
    """Update README files from listings.json."""
    listings = get_listings_from_json()

    check_schema(listings)
    sort_listings(listings)

    # earliest_date is 2026-05-01 00:00 PT
    summer_2027_listings = filter_summer(listings, "2027", earliest_date=1777618800)

    # Generate main README with active listings only
    embed_table(summer_2027_listings, "README.md", active_only=True)

    # Generate separate README for inactive listings (same header/ads structure)
    embed_table(summer_2027_listings, "README-Inactive.md", inactive_only=True)

    # Off-season roles get a much earlier cutoff (2025-12-01 PT) than the summer list, since Fall
    # roles for the coming autumn start appearing the previous December. Anything already in the
    # summer list is excluded so it is not listed twice.
    offseason_listings = filter_off_season(
        listings,
        min_year=2026,
        earliest_date=1764576000,
        exclude_ids={listing["id"] for listing in summer_2027_listings},
    )
    embed_table(offseason_listings, "README-Off-Season.md", off_season=True)

    set_output("commit_message", "Updating READMEs at " + datetime.now().strftime("%B %d, %Y %H:%M:%S"))


# =============================================================================
# Contribution Commands
# =============================================================================


def _clean(s: str) -> str:
    """Clean a string by removing markdown formatting and extra whitespace."""
    return re.sub(r"[\s*_`]+", " ", s or "").strip()


def _is_no_answer(s: str) -> bool:
    """Check if a string represents a non-answer."""
    return _clean(s).lower() in NO_ANSWER


def _norm_category(raw: str) -> str | None:
    """Normalize a category string to its canonical form."""
    if _is_no_answer(raw):
        return None
    key = _clean(raw).lower()
    return CATEGORY_MAPPING.get(key)


def _parse_bool(raw: str) -> bool | None:
    """Parse a string as a boolean value."""
    if _is_no_answer(raw):
        return None
    val = _clean(raw).lower()
    if val in YES_VALUES:
        return True
    if val in NO_VALUES:
        return False
    return None


def _add_https_to_url(url: str) -> str:
    """Ensure a URL has an https:// prefix."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def _get_contribution_data(body: str, is_edit: bool, username: str) -> dict[str, Any]:
    """Extract listing data from an issue body."""
    lines = [text.strip("# ").strip() for text in re.split(r"[\n\r]+", body)]
    data: dict[str, Any] = {"date_updated": int(datetime.now().timestamp())}

    # Defaults for NEW only
    if not is_edit:
        data.update(
            {
                "sponsorship": "Offers Sponsorship",
                "active": True,
                "degrees": ["Bachelor's"],
            }
        )

    def next_line_value(idx: int) -> str:
        if idx + 1 >= len(lines):
            return ""
        next_line = lines[idx + 1].strip()
        if next_line and (next_line.endswith("?") or next_line.endswith(":")):
            return ""
        header_patterns = [
            "Company Name",
            "Internship Title",
            "Location",
            "What term",
            "Does this",
            "Is this",
            "Permanently remove",
            "What category",
            "Advanced Degree",
            "Email associated",
            "Extra Notes",
            "Reason for",
        ]
        if any(pattern in next_line for pattern in header_patterns):
            return ""
        return next_line

    provided_fields: set[str] = set()

    for i, line in enumerate(lines):
        if "Link to Internship Posting" in line:
            v = next_line_value(i)
            if not _is_no_answer(v):
                data["url"] = _add_https_to_url(v)
                provided_fields.add("url")

        elif "Company Name" in line:
            v = next_line_value(i)
            if not _is_no_answer(v):
                data["company_name"] = _clean(v)
                provided_fields.add("company_name")

        elif "Internship Title" in line:
            v = next_line_value(i)
            if not _is_no_answer(v):
                data["title"] = _clean(v)
                provided_fields.add("title")

        elif "Location" in line and "Email" not in line:
            v = next_line_value(i)
            if not _is_no_answer(v):
                data["locations"] = [_clean(loc) for loc in v.split("|") if _clean(loc)]
                provided_fields.add("locations")

        elif "What term(s) is this internship offered for?" in line:
            v = next_line_value(i)
            if not _is_no_answer(v):
                data["terms"] = [_clean(term) for term in v.split(",") if _clean(term)]
                provided_fields.add("terms")

        elif "Does this internship offer sponsorship?" in line:
            v = next_line_value(i)
            if not _is_no_answer(v):
                data["sponsorship"] = "Other"
                for option in ["Offers Sponsorship", "Does Not Offer Sponsorship", "U.S. Citizenship is Required"]:
                    if option.lower() in v.lower():
                        data["sponsorship"] = option
                        break
                provided_fields.add("sponsorship")

        elif ("Is this internship still accepting applications?" in line) or (
            "Is this internship currently accepting applications?" in line
        ):
            v = next_line_value(i)
            ans = _parse_bool(v)
            if ans is not None:
                data["active"] = ans
                provided_fields.add("active")
            elif not is_edit and "active" not in data:
                data["active"] = True
                provided_fields.add("active")

        elif "What category does this internship belong to?" in line:
            v = next_line_value(i)
            cat = _norm_category(v)
            if cat is not None:
                data["category"] = cat
                provided_fields.add("category")

        elif "Advanced Degree Requirements" in line:
            checked = False
            provided = False
            if i + 1 < len(lines):
                val = lines[i + 1].strip().lower()
                if "[x]" in val or "[ ]" in val:
                    provided = True
                    checked = "[x]" in val
                elif not _is_no_answer(val) and not val.startswith("###"):
                    if any(
                        term in val for term in ["advanced", "degree", "bachelor", "master", "required", "checkbox"]
                    ):
                        provided = True
            if provided:
                data["degrees"] = ["Master's"] if checked else ["Bachelor's"]
                provided_fields.add("degrees")

        elif "Email associated with your GitHub account" in line:
            v = next_line_value(i)
            email = v if v else "_no response_"
            if not _is_no_answer(email):
                set_output("commit_email", email)
                set_output("commit_username", username)
            else:
                set_output("commit_email", "action@github.com")
                set_output("commit_username", "GitHub Action")

    if is_edit:
        for i, line in enumerate(lines):
            if "Permanently remove this internship from the list?" in line:
                if i + 1 < len(lines):
                    data["is_visible"] = "[x]" not in lines[i + 1].lower()
                    provided_fields.add("is_visible")
                break

    if not is_edit and "category" not in data:
        if "title" in data:
            try:
                data["category"] = classify_job_category(data) or "Other"
            except Exception:
                data["category"] = "Other"
        else:
            data["category"] = "Other"
        provided_fields.add("category")

    data["_provided_fields"] = provided_fields
    return data


def cmd_contribution_process(event_file: str) -> None:
    """Process an approved contribution issue."""
    try:
        with open(event_file) as f:
            event_data = json.load(f)
    except Exception as e:
        fail(f"Failed to read event file: {e!s}")
        return

    try:
        labels = [label["name"] for label in event_data["issue"]["labels"]]
        print(f"DEBUG: Issue labels found: {labels}")

        new_internship = "new_internship" in labels
        edit_internship = "edit_internship" in labels
        bulk_mark_inactive = "bulk_mark_inactive" in labels

        # If it's a bulk_mark_inactive issue, call that handler directly
        if bulk_mark_inactive:
            print("DEBUG: Detected bulk_mark_inactive issue, delegating to bulk-inactive handler")
            cmd_listings_mark_inactive(event_file)
            return

        if not new_internship and not edit_internship:
            fail(
                f"Only new_internship, edit_internship, and bulk_mark_inactive issues can be approved. "
                f"Found labels: {labels}"
            )
            return

        issue_body = event_data["issue"]["body"]
        issue_user = event_data["issue"]["user"]["login"]

        data = _get_contribution_data(issue_body, is_edit=edit_internship, username=issue_user)
    except Exception as e:
        fail(f"Error processing issue data: {e!s}")
        return

    if new_internship:
        data["source"] = issue_user
        data["id"] = str(uuid.uuid4())
        data["date_posted"] = int(datetime.now().timestamp())
        data["company_url"] = ""
        data["is_visible"] = True

    if "url" in data:
        utm = data["url"].find("?utm_source")
        if utm == -1:
            utm = data["url"].find("&utm_source")
        if utm != -1:
            data["url"] = data["url"][:utm]

    provided_fields = data.pop("_provided_fields", set())

    def get_commit_text(listing: dict[str, Any]) -> str:
        closed_text = "" if listing["active"] else "(Closed)"
        sponsorship_text = "" if listing["sponsorship"] == "Other" else ("(" + listing["sponsorship"] + ")")
        parts = [listing["title"].strip(), "at", listing["company_name"].strip()]
        if closed_text:
            parts.append(closed_text)
        if sponsorship_text:
            parts.append(sponsorship_text)
        return " ".join(parts)

    try:
        with open(".github/scripts/listings.json") as f:
            listings = json.load(f)

        if listing_to_update := next((item for item in listings if item["url"] == data["url"]), None):
            if new_internship:
                fail("This internship is already in our list. See CONTRIBUTING.md for how to edit a listing")
                return

            for key, value in data.items():
                if key in provided_fields or key in ["date_updated"]:
                    listing_to_update[key] = value

            set_output("commit_message", "updated listing: " + get_commit_text(listing_to_update))
        else:
            if edit_internship:
                fail("We could not find this internship in our list. Please double check you inserted the right url")
                return
            listings.append(data)
            set_output("commit_message", "added listing: " + get_commit_text(data))

        with open(".github/scripts/listings.json", "w") as f:
            f.write(json.dumps(listings, indent=4))
    except Exception as e:
        fail(f"Error updating listings: {e!s}")
        return


# =============================================================================
# Listings Commands
# =============================================================================


def _extract_urls_from_issue_body(body: str) -> list[str]:
    """Extract URLs from the issue body."""
    urls: list[str] = []
    lines = body.split("\n")
    in_urls_section = False

    for line in lines:
        line = line.strip()

        if "Job Posting URLs" in line:
            in_urls_section = True
            continue

        if in_urls_section and line.startswith("###"):
            break

        if in_urls_section and line and line.startswith("http"):
            clean_url = line.strip()
            tracking_params = ["?utm_source", "&utm_source", "?ref=", "&ref="]
            earliest_pos = len(clean_url)

            for param in tracking_params:
                pos = clean_url.find(param)
                if pos != -1 and pos < earliest_pos:
                    earliest_pos = pos

            if earliest_pos < len(clean_url):
                clean_url = clean_url[:earliest_pos]

            urls.append(clean_url)

    return urls


def _extract_reason_from_issue_body(body: str) -> str:
    """Extract the reason from the issue body."""
    lines = body.split("\n")
    in_reason_section = False
    reason_lines: list[str] = []

    for line in lines:
        line_stripped = line.strip()

        if "Reason for marking as inactive" in line:
            in_reason_section = True
            continue

        if in_reason_section and line_stripped.startswith("###"):
            break

        if in_reason_section and line_stripped:
            reason_lines.append(line_stripped)

    return " ".join(reason_lines) if reason_lines else "Bulk marking as inactive"


def _extract_email_from_issue_body(body: str) -> str | None:
    """Extract email from the issue body if provided."""
    lines = body.split("\n")
    in_email_section = False

    for line in lines:
        line_stripped = line.strip()

        if "Email associated with your GitHub account" in line:
            in_email_section = True
            continue

        if in_email_section and line_stripped.startswith("###"):
            break

        if in_email_section and line_stripped and "@" in line_stripped:
            return line_stripped

    return None


def _mark_urls_as_inactive(urls: list[str]) -> ResultDict:
    """Mark the given URLs as inactive in listings.json."""
    results: ResultDict = {}

    try:
        with open(".github/scripts/listings.json") as f:
            listings: list[dict[str, Any]] = json.load(f)
    except Exception as e:
        fail(f"Failed to load listings.json: {e!s}")
        return results

    for url in urls:
        try:
            listing_found = False
            for listing in listings:
                if listing.get("url") == url:
                    listing_found = True

                    if not listing.get("active", True):
                        results[url] = {
                            "status": "warning",
                            "message": f"Already inactive: {listing['company_name']} - {listing['title']}",
                        }
                    else:
                        listing["active"] = False
                        listing["date_updated"] = int(datetime.now().timestamp())
                        results[url] = {
                            "status": "success",
                            "message": f"Marked inactive: {listing['company_name']} - {listing['title']}",
                        }
                    break

            if not listing_found:
                results[url] = {
                    "status": "error",
                    "message": f"URL not found in database: {url}",
                }

        except Exception as e:
            results[url] = {
                "status": "error",
                "message": f"Error processing URL: {e!s}",
            }

    try:
        with open(".github/scripts/listings.json", "w") as f:
            json.dump(listings, f, indent=4)
    except Exception as e:
        fail(f"Failed to save listings.json: {e!s}")
        return results

    return results


def _generate_commit_message(results: ResultDict, reason: str) -> str:
    """Generate a commit message based on the results."""
    successful_count = len([r for r in results.values() if r["status"] == "success"])
    total_count = len(results)

    if successful_count == 0:
        return f"Bulk inactive attempt: 0/{total_count} roles updated"
    elif successful_count == total_count:
        return f"Bulk marked inactive: {successful_count} roles - {reason}"
    else:
        return f"Bulk marked inactive: {successful_count}/{total_count} roles - {reason}"


def _generate_summary_comment(results: ResultDict, reason: str) -> str:
    """Generate a summary comment for the GitHub issue."""
    successful = [url for url, result in results.items() if result["status"] == "success"]
    warnings = [url for url, result in results.items() if result["status"] == "warning"]
    errors = [url for url, result in results.items() if result["status"] == "error"]

    comment = "## Bulk Mark Inactive Results\n\n"
    comment += f"**Reason:** {reason}\n\n"
    comment += f"**Summary:** {len(successful)} successful, {len(warnings)} warnings, {len(errors)} errors\n\n"

    if successful:
        comment += f"### ✅ Successfully Marked Inactive ({len(successful)})\n"
        for url in successful:
            comment += f"- {results[url]['message']}\n"
        comment += "\n"

    if warnings:
        comment += f"### ⚠️ Warnings ({len(warnings)})\n"
        for url in warnings:
            comment += f"- {results[url]['message']}\n"
        comment += "\n"

    if errors:
        comment += f"### ❌ Errors ({len(errors)})\n"
        for url in errors:
            comment += f"- {results[url]['message']}\n"
        comment += "\n"

    if successful:
        comment += "✅ **The README has been updated and changes have been committed!**\n"

    return comment


def cmd_listings_mark_inactive(event_file: str) -> None:
    """Process a bulk mark inactive issue."""
    try:
        with open(event_file) as f:
            event_data = json.load(f)
    except Exception as e:
        fail(f"Failed to read event file: {e!s}")
        return

    try:
        labels = [label["name"] for label in event_data["issue"]["labels"]]
        if "bulk_mark_inactive" not in labels:
            fail("This command only processes bulk_mark_inactive issues")
            return

        issue_body = event_data["issue"]["body"]
        issue_user = event_data["issue"]["user"]["login"]

        print("DEBUG: Issue body content:")
        print("=" * 80)
        print(issue_body)
        print("=" * 80)

        urls = _extract_urls_from_issue_body(issue_body)
        reason = _extract_reason_from_issue_body(issue_body)
        email = _extract_email_from_issue_body(issue_body)

        print(f"DEBUG: Extracted {len(urls)} URLs from issue body")
        print(f"DEBUG: URLs: {urls}")
        print(f"DEBUG: Reason: {reason}")
        print(f"DEBUG: Email: {email}")

        if not urls:
            fail("No valid URLs found in the issue body")
            return

        print(f"Processing {len(urls)} URLs...")

        results = _mark_urls_as_inactive(urls)

        commit_message = _generate_commit_message(results, reason)
        summary_comment = _generate_summary_comment(results, reason)

        set_output("commit_message", commit_message)
        set_output("summary_comment", summary_comment)

        if email:
            set_output("commit_email", email)
            set_output("commit_username", issue_user)
        else:
            set_output("commit_email", "action@github.com")
            set_output("commit_username", "Github Action")

        print("Results:")
        for url, result in results.items():
            print(f"  {result['status'].upper()}: {result['message']}")

        successful_count = len([r for r in results.values() if r["status"] == "success"])
        if successful_count == 0:
            fail("No URLs were successfully marked as inactive")
            return

    except Exception as e:
        fail(f"Error processing bulk mark inactive: {e!s}")
        return


def cmd_listings_remove(
    url: str | None = None,
    listing_id: str | None = None,
    hide: bool = False,
    permanent: bool = False,
    confirm: bool = False,
) -> None:
    """Remove a listing by URL or ID.

    Default: mark inactive. --hide: set is_visible=false. --permanent: delete from JSON.
    """
    if not url and not listing_id:
        fail("Must provide --url or --id")
        return
    if url and listing_id:
        fail("Provide only one of --url or --id, not both")
        return

    if permanent and not confirm:
        fail("--permanent requires --confirm flag (this permanently deletes the listing from listings.json)")
        return

    try:
        with open(".github/scripts/listings.json") as f:
            listings: list[dict[str, Any]] = json.load(f)
    except Exception as e:
        fail(f"Failed to load listings.json: {e!s}")
        return

    match_key = "url" if url else "id"
    match_value = url or listing_id

    matching = [lst for lst in listings if lst.get(match_key) == match_value]
    if not matching:
        fail(f"No listing found with {match_key}={match_value}")
        return

    listing = matching[0]
    label = f"{listing['company_name']} - {listing['title']}"

    if permanent:
        listings.remove(listing)
        print(f"Permanently deleted: {label}")
    elif hide:
        listing["is_visible"] = False
        listing["date_updated"] = int(datetime.now().timestamp())
        print(f"Hidden from READMEs: {label}")
    else:
        if not listing.get("active", True):
            print(f"Already inactive: {label}")
            return
        listing["active"] = False
        listing["date_updated"] = int(datetime.now().timestamp())
        print(f"Marked inactive: {label}")

    try:
        with open(".github/scripts/listings.json", "w") as f:
            json.dump(listings, f, indent=4)
        print("listings.json updated successfully.")
    except Exception as e:
        fail(f"Failed to save listings.json: {e!s}")
