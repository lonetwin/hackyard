#!/usr/bin/env python3
"""Convert standard Markdown to Confluence-compatible Markdown.

Performs the following transformations:
  - Replaces arrow characters (-->, <--) and em dashes (--)
  - Removes horizontal rules
  - Converts tree-drawing characters to indented bullet lists
  - Converts footnote references and definitions to either:
      (a) inline (Ref N) markers with a reference table at the end, or
      (b) inline hyperlinks when --base-url is provided and footnote
          definitions contain relative file paths
  - Adjusts ToC anchor links to Confluence heading-anchor format
  - Removes backticks around text that is immediately adjacent to a
    hyperlink (Confluence renders these literally instead of as code)
  - Strips remaining non-ASCII characters that Confluence cannot render

Usage:
    python markdown-to-confluence.py INPUT.md [-o OUTPUT.md] [--base-url URL]

If -o / --output is omitted the result is written to stdout.

When --base-url is supplied, footnote definitions that look like relative
file paths (with optional :LINE or :LINE-LINE suffixes) are turned into
full URLs.  Line-number suffixes are converted to GitHub-style #L anchors
(e.g. :42 becomes #L42, :10-20 becomes #L10-L20).
"""

import argparse
import re
import sys
from typing import Optional


def replace_arrows(text: str) -> str:
    text = text.replace(" \u2192 ", " --> ")
    text = text.replace("\u2192", " --> ")
    text = text.replace(" \u2190 ", " <-- ")
    text = text.replace("\u2190", " <-- ")
    text = text.replace(" \u2194 ", " <--> ")
    text = text.replace("\u2194", " <--> ")
    text = text.replace(" \u21d2 ", " ==> ")
    text = text.replace("\u21d2", " ==> ")
    return text


def replace_em_dashes(text: str) -> str:
    return text.replace("\u2014", "--")


def remove_horizontal_rules(text: str) -> str:
    return re.sub(r"\n---\n", "\n\n", text)


def convert_tree_characters(text: str) -> str:
    text = re.sub(r"\u251c\u2500\u2500 ", "- ", text)
    text = re.sub(r"\u2514\u2500\u2500 ", "- ", text)
    text = re.sub(r"\u2502   ", "  ", text)
    text = re.sub(r"\u2502", "|", text)
    text = re.sub(r"\u2500", "-", text)
    return text


def _line_ref_to_anchor(line_ref: str) -> str:
    """Convert a colon-separated line reference to a GitHub #L anchor.

    Examples:
        "42"     --> "#L42"
        "10-20"  --> "#L10-L20"
        "5,12"   --> "#L5"        (first number only for comma-separated)
    """
    if "," in line_ref:
        line_ref = line_ref.split(",")[0]
    if "-" in line_ref:
        start, end = line_ref.split("-", 1)
        return f"#L{start}-L{end}"
    return f"#L{line_ref}"


def _build_url(base_url: str, path: str, line_ref: Optional[str] = None) -> str:
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if line_ref:
        url += _line_ref_to_anchor(line_ref)
    return url


def _extract_path_and_lines(
    defn: str, base_url: Optional[str] = None
) -> Optional[tuple[str, Optional[str]]]:
    """Try to extract a file path and optional line reference from a
    footnote definition string.  Returns ``(path, line_ref)`` or *None*
    if the definition does not look like a file path.

    Handles backtick-wrapped paths, absolute paths, and definitions that
    contain descriptive text after the path (separated by `` -- `` or
    em-dash).  When *base_url* is provided and the path is absolute, the
    script finds the longest suffix of the path that shares a leading
    component with the base URL's path, ensuring the generated URL is
    correct regardless of the local checkout location.
    """
    # Strip leading descriptive noise: take the first backtick-wrapped
    # token or the first whitespace-free token.
    token_match = re.match(r"^`([^`]+)`", defn) or re.match(r"^(\S+)", defn)
    if not token_match:
        return None
    token = token_match.group(1)

    path_match = re.match(r"^(.+?)(?::(\d[\d,\-]*))?$", token)
    if not path_match:
        return None

    path = path_match.group(1)
    line_ref = path_match.group(2)

    if path.startswith("/") and base_url:
        # Find repo-relative portion by matching path components against
        # the trailing segments of the base URL.
        from urllib.parse import urlparse

        url_path_parts = urlparse(base_url).path.strip("/").split("/")
        path_parts = path.strip("/").split("/")
        # Walk the absolute path looking for the first component that
        # appears in the base URL path — everything from the component
        # *after* that match onwards is repo-relative.
        for i, part in enumerate(path_parts):
            if part in url_path_parts:
                # Take everything after the matching repo-name component
                path = "/".join(path_parts[i + 1 :])
                break
        else:
            path = path.lstrip("/")

    # Reject tokens that don't look like file paths
    if "/" not in path and "." not in path:
        return None

    return path, line_ref


def convert_footnotes(
    text: str,
    base_url: Optional[str] = None,
) -> str:
    """Replace footnote markers and definitions.

    Without base_url: markers become ``(Ref N)`` and definitions are
    collected into a Markdown reference table appended at the end.

    With base_url: definitions that look like file paths are turned into
    full URLs and markers become inline hyperlinks with the text "ref".
    Absolute paths are automatically made relative.
    """
    definitions: dict[int, str] = {}
    for m in re.finditer(r"^\[\^(\d+)\]:\s*(.+)$", text, re.MULTILINE):
        definitions[int(m.group(1))] = m.group(2).strip()

    text = re.sub(r"^\[\^(\d+)\]:\s*.+$", "", text, flags=re.MULTILINE)

    if base_url and definitions:
        urls: dict[int, str] = {}
        for num, defn in definitions.items():
            extracted = _extract_path_and_lines(defn, base_url)
            if extracted:
                path, line_ref = extracted
                urls[num] = _build_url(base_url, path, line_ref)

        def _replace_with_link(m: re.Match[str]) -> str:
            num = int(m.group(1))
            if num in urls:
                return f"([ref]({urls[num]}))"
            return f"(Ref {num})"

        text = re.sub(r"\[\^(\d+)\]", _replace_with_link, text)
        # Ensure a space before every ([ref]...) that doesn't have one
        text = re.sub(r"(?<! )\(\[ref\]", " ([ref]", text)
    elif definitions:
        text = re.sub(
            r"\[\^(\d+)\]",
            lambda m: f"(Ref {m.group(1)})",
            text,
        )
        # Ensure a space before every (Ref N) that doesn't have one
        text = re.sub(r"(?<! )\(Ref \d+\)", lambda m: " " + m.group(0), text)
        rows = ["", "## References", "", "| Ref | Location |", "|-----|----------|"]
        for num in sorted(definitions):
            rows.append(f"| {num} | {definitions[num]} |")
        text = text.rstrip() + "\n" + "\n".join(rows) + "\n"

    return text


def fix_toc_anchors(text: str) -> str:
    """Rewrite ToC-style anchor links to Confluence heading-anchor format."""

    def _rewrite(m: re.Match[str]) -> str:
        label = m.group(1)
        return f"[{label}](#{label.replace(' ', '-')})"

    return re.sub(r"\[([^\]]+)\]\(#[^)]+\)", _rewrite, text)


def remove_backticks_around_links(text: str) -> str:
    """Remove backticks wrapping text that is immediately followed by a
    Markdown hyperlink, since Confluence renders these literally."""
    return re.sub(
        r"`([^`]+)`(\s*\(\[[^\]]*\]\(https?://[^)]+\)\))",
        r"\1 \2",
        text,
    )


def strip_non_ascii(text: str) -> str:
    """Remove remaining non-ASCII characters that Confluence cannot render,
    preserving common safe ones (smart quotes, bullets, etc.)."""
    safe = set("\u00a0\u00b7\u2018\u2019\u201c\u201d\u2022\u2026\u00e9\u00e8")

    def _replace(m: re.Match[str]) -> str:
        ch = m.group(0)
        if ch in safe:
            return ch
        return ""

    return re.sub(r"[^\x00-\x7f]", _replace, text)


def remove_empty_footnotes_heading(text: str) -> str:
    """Remove a 'Footnotes' heading left behind after footnote conversion."""
    return re.sub(r"\n+##\s+\d*\.?\s*Footnotes\s*\n*", "\n", text)


def remove_footnotes_toc_entry(text: str) -> str:
    """Remove ToC entries that point to a Footnotes section."""
    return re.sub(r"^-?\s*\d*\.?\s*\[Footnotes\].*\n?", "", text, flags=re.MULTILINE)


def convert(
    text: str,
    base_url: Optional[str] = None,
) -> str:
    text = replace_arrows(text)
    text = replace_em_dashes(text)
    text = remove_horizontal_rules(text)
    text = convert_tree_characters(text)
    text = convert_footnotes(text, base_url=base_url)
    text = remove_empty_footnotes_heading(text)
    text = remove_footnotes_toc_entry(text)
    text = fix_toc_anchors(text)
    text = remove_backticks_around_links(text)
    text = strip_non_ascii(text)
    # Collapse multiple spaces within lines (but not leading indentation)
    text = re.sub(r"(?<=\S)  +", " ", text)
    # Collapse runs of 3+ blank lines down to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Markdown to Confluence-compatible Markdown."
    )
    parser.add_argument("input", help="Input Markdown file")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=(
            "Base URL to prepend to relative file-path footnote definitions, "
            "converting them to full hyperlinks. Line-number suffixes are "
            "converted to GitHub-style #L anchors."
        ),
    )
    args = parser.parse_args()

    with open(args.input) as f:
        text = f.read()

    result = convert(text, base_url=args.base_url)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
    else:
        sys.stdout.write(result)


if __name__ == "__main__":
    main()
