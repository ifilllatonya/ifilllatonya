"""Turn an issue-form body into PITCH_* env lines. Issue text is untrusted."""
import os
import re

body = os.environ.get("BODY") or ""
title = os.environ.get("TITLE") or ""

# GitHub issue forms render each field as "### Label\n\nvalue"
fields = {}
for chunk in re.split(r"^###\s+", body, flags=re.M):
    if "\n" in chunk:
        label, value = chunk.split("\n", 1)
        fields[label.strip().lower()] = value.strip()


def one_line(text, limit):
    """Collapse to a single line so nothing can inject extra env entries."""
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text or "")
    return " ".join(text.split())[:limit]


business = fields.get("business name") or re.sub(r"^App pitch:\s*", "", title)
detail = fields.get("what does it do, and what should the app handle?", "")

print("PITCH_BUSINESS=" + one_line(business, 60))
print("PITCH_DETAIL=" + one_line(detail, 200))
