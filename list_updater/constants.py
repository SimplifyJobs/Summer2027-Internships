"""Constants and configuration for the internships scripts."""

import os
import time

if hasattr(time, "tzset"):
    time.tzset()

# Button image URLs
SIMPLIFY_BUTTON = "https://i.imgur.com/MXdpmi0.png"
SHORT_APPLY_BUTTON = "https://i.imgur.com/fbjwDvo.png"
SQUARE_SIMPLIFY_BUTTON = "https://i.imgur.com/aVnQdox.png"
LONG_APPLY_BUTTON = "https://i.imgur.com/6cFAMUo.png"

# Inactivity thresholds (in months)
NON_SIMPLIFY_INACTIVE_THRESHOLD_MONTHS = 2
SIMPLIFY_INACTIVE_THRESHOLD_MONTHS = 2

# GitHub README file size limit (500 KiB = 512,000 bytes)
GITHUB_FILE_SIZE_LIMIT = 512000
# Smaller buffer to show warning closer to actual cutoff (2.5 KiB buffer)
SIZE_BUFFER = 2560

# Set of Simplify company URLs to block from appearing in the README
BLOCKED_COMPANIES: set[str] = {
    "https://simplify.jobs/c/Jerry",
}

# FAANG+ companies - will be marked with fire emoji
FAANG_PLUS: set[str] = {
    "airbnb",
    "adobe",
    "amazon",
    "amd",
    "anthropic",
    "apple",
    "asana",
    "atlassian",
    "bytedance",
    "cloudflare",
    "coinbase",
    "crowdstrike",
    "databricks",
    "datadog",
    "doordash",
    "dropbox",
    "duolingo",
    "figma",
    "google",
    "ibm",
    "instacart",
    "intel",
    "linkedin",
    "lyft",
    "meta",
    "microsoft",
    "netflix",
    "notion",
    "nvidia",
    "openai",
    "oracle",
    "palantir",
    "paypal",
    "perplexity",
    "pinterest",
    "ramp",
    "reddit",
    "rippling",
    "robinhood",
    "roblox",
    "salesforce",
    "samsara",
    "servicenow",
    "shopify",
    "slack",
    "snap",
    "snapchat",
    "spacex",
    "splunk",
    "snowflake",
    "stripe",
    "square",
    "tesla",
    "tinder",
    "tiktok",
    "uber",
    "visa",
    "waymo",
    "x",
}

# Job categories with display names and emojis
CATEGORIES: dict[str, dict[str, str]] = {
    "Software": {"name": "Software Engineering", "emoji": "💻"},
    "Product": {"name": "Product Management", "emoji": "📱"},
    "AI/ML/Data": {"name": "Data Science, AI & Machine Learning", "emoji": "🤖"},
    "Quant": {"name": "Quantitative Finance", "emoji": "📈"},
    "Hardware": {"name": "Hardware Engineering", "emoji": "🔧"},
}

# Category name mapping from short to full names
CATEGORY_MAPPING: dict[str, str] = {
    "software engineering": "Software Engineering",
    "product management": "Product Management",
    "data science, ai & machine learning": "Data Science, AI & Machine Learning",
    "data science": "Data Science, AI & Machine Learning",
    "ai": "Data Science, AI & Machine Learning",
    "machine learning": "Data Science, AI & Machine Learning",
    "quantitative finance": "Quantitative Finance",
    "hardware engineering": "Hardware Engineering",
}

# Required schema properties for listings
LISTING_SCHEMA_PROPS: list[str] = [
    "source",
    "company_name",
    "id",
    "title",
    "active",
    "date_updated",
    "is_visible",
    "date_posted",
    "url",
    "locations",
    "company_url",
    "terms",
    "sponsorship",
]
