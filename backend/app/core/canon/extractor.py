import re
from pathlib import Path


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
ADR_PATTERN = re.compile(r"\bADR-\d{3}\b")
SPRINT_PATTERN = re.compile(r"\bSprint-\d+(?:\.\d+)?(?:-[A-Za-z0-9-]+)?\b")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def read_markdown(path: Path) -> str:
    """
    Read a markdown file safely.
    """

    return path.read_text(encoding="utf-8")


def extract_title(content: str, fallback: str) -> str:
    """
    Extract the first H1 title from markdown content.
    """

    match = re.search(r"^#\s+(.*)$", content, re.MULTILINE)

    if match:
        return match.group(1).strip()

    return fallback


def extract_headings(content: str) -> list[dict]:
    """
    Extract markdown headings.
    """

    headings = []

    for match in HEADING_PATTERN.finditer(content):
        headings.append(
            {
                "level": len(match.group(1)),
                "text": match.group(2).strip(),
            }
        )

    return headings


def extract_adr_mentions(content: str) -> list[str]:
    """
    Extract ADR references from markdown content.
    """

    return sorted(set(ADR_PATTERN.findall(content)))


def extract_sprint_mentions(content: str) -> list[str]:
    """
    Extract Sprint references from markdown content.
    """

    return sorted(set(SPRINT_PATTERN.findall(content)))


def extract_markdown_links(content: str) -> list[dict]:
    """
    Extract markdown links.
    """

    return [
        {
            "label": match.group(1).strip(),
            "target": match.group(2).strip(),
        }
        for match in MARKDOWN_LINK_PATTERN.finditer(content)
    ]


def extract_document_signals(path: Path) -> dict:
    """
    Extract relationship signals from a Canon document.
    """

    content = read_markdown(path)

    return {
        "path": str(path),
        "title": extract_title(content, path.stem),
        "headings": extract_headings(content),
        "adr_mentions": extract_adr_mentions(content),
        "sprint_mentions": extract_sprint_mentions(content),
        "links": extract_markdown_links(content),
    }
