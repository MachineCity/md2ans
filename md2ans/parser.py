"""Comprehensive Markdown parser supporting CommonMark, GFM, and extended Markdown tags."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# --- AST Node Definitions ---

@dataclass
class Node:
    """Base AST block node."""


@dataclass
class Frontmatter(Node):
    entries: List[Tuple[str, str]]


@dataclass
class Heading(Node):
    level: int
    text: str


@dataclass
class Paragraph(Node):
    text: str


@dataclass
class ThematicBreak(Node):
    style: str = "---"


@dataclass
class CodeBlock(Node):
    code: str
    language: str = ""
    meta: str = ""


@dataclass
class MathBlock(Node):
    formula: str


@dataclass
class BlockQuote(Node):
    children: List[Node]
    alert_type: Optional[str] = None   # NOTE, TIP, IMPORTANT, WARNING, CAUTION
    alert_title: Optional[str] = None


@dataclass
class ListItem:
    text: str
    children: List[Node] = field(default_factory=list)
    checked: Optional[bool] = None     # None = normal item, True = [x], False = [ ]


@dataclass
class ListBlock(Node):
    ordered: bool
    start: int = 1
    items: List[ListItem] = field(default_factory=list)


@dataclass
class DefinitionItem:
    term: str
    definitions: List[str]


@dataclass
class DefinitionList(Node):
    items: List[DefinitionItem]


@dataclass
class Table(Node):
    headers: List[str]
    alignments: List[str]  # "left", "center", "right"
    rows: List[List[str]]


@dataclass
class DetailsBlock(Node):
    summary: str
    children: List[Node]


@dataclass
class HtmlBlock(Node):
    raw: str


@dataclass
class Document:
    nodes: List[Node]
    footnotes: Dict[str, str] = field(default_factory=dict)
    ref_links: Dict[str, Tuple[str, str]] = field(default_factory=dict)


# --- Regex Patterns ---

ATX_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})(?:\s+(.*?))?(?:\s+#+\s*)?$")
SETEXT_H1_RE = re.compile(r"^\s{0,3}=+=\s*$")
SETEXT_H2_RE = re.compile(r"^\s{0,3}-+-\s*$")
THEMATIC_BREAK_RE = re.compile(r"^\s{0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})\s*$")
FENCE_OPEN_RE = re.compile(r"^(\s{0,3})(`{3,}|~{3,})\s*([^\s`~]*)(?:\s+(.*))?$")
REF_DEF_RE = re.compile(
    r'^\s{0,3}\[([^\^\]]+)\]:\s*<?([^\s>]+)>?(?:\s+["\'(](.*?)["\')])?\s*$'
)
FOOTNOTE_DEF_RE = re.compile(r"^\s{0,3}\[\^([^\]]+)\]:\s*(.*)$")
ALERT_HEADER_RE = re.compile(
    r"^\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION|INFO|DANGER|BUG|SUCCESS)\](?:\s+(.*))?$",
    re.IGNORECASE,
)
LIST_ITEM_RE = re.compile(r"^(\s*)([*+-]|\d+[.)])\s+(.*)$")
TASK_MARKER_RE = re.compile(r"^\[([ xX])\]\s+(.*)$")
DEF_LINE_RE = re.compile(r"^\s{0,3}:\s+(.*)$")
TABLE_SEP_CELL_RE = re.compile(r"^:?-+:?$")


def _split_table_row(line: str) -> List[str]:
    """Split a GFM pipe table row into cells, respecting escaped pipes and inline code spans."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith(r"\|"):
        s = s[:-1]

    cells: List[str] = []
    cur: List[str] = []
    in_code = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
            cur.append(ch)
            i += 1
            continue
        if ch == "|" and not in_code:
            cells.append("".join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def _is_table_separator(line: str) -> Optional[List[str]]:
    """If `line` is a valid GFM table alignment row, return list of alignments, else None."""
    if "|" not in line:
        return None
    cells = _split_table_row(line)
    if not cells:
        return None
    alignments: List[str] = []
    for cell in cells:
        c = cell.strip()
        if not TABLE_SEP_CELL_RE.match(c):
            return None
        if c.startswith(":") and c.endswith(":"):
            alignments.append("center")
        elif c.endswith(":"):
            alignments.append("right")
        else:
            alignments.append("left")
    return alignments


def parse_markdown(text: str) -> Document:
    """Parse a Markdown string into a Document AST."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    footnotes: Dict[str, str] = {}
    ref_links: Dict[str, Tuple[str, str]] = {}

    idx = 0
    frontmatter_node: Optional[Frontmatter] = None

    # 1. Check for YAML Frontmatter at top of document
    if lines and lines[0].strip() == "---":
        end_idx = None
        for j in range(1, min(len(lines), 60)):
            if lines[j].strip() in ("---", "..."):
                end_idx = j
                break
        if end_idx is not None and end_idx > 1:
            entries: List[Tuple[str, str]] = []
            valid_fm = True
            for fm_line in lines[1:end_idx]:
                s = fm_line.strip()
                if not s or s.startswith("#"):
                    continue
                if ":" in s:
                    k, v = s.split(":", 1)
                    entries.append((k.strip(), v.strip().strip("\"'")))
                else:
                    valid_fm = False
                    break
            if valid_fm and entries:
                frontmatter_node = Frontmatter(entries=entries)
                idx = end_idx + 1

    # 2. First pass: extract reference link definitions and footnote definitions
    filtered_lines: List[str] = []
    i = idx
    in_fence = False
    fence_marker = ""

    while i < len(lines):
        line = lines[i]
        fm = FENCE_OPEN_RE.match(line)
        if fm:
            marker = fm.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif line.strip().startswith(fence_marker[0] * len(fence_marker)) and not line.strip().lstrip(fence_marker[0]):
                in_fence = False
            filtered_lines.append(line)
            i += 1
            continue

        if not in_fence:
            fn_m = FOOTNOTE_DEF_RE.match(line)
            if fn_m:
                fn_id = fn_m.group(1).strip()
                fn_parts = [fn_m.group(2).strip()]
                i += 1
                while i < len(lines) and (lines[i].startswith("    ") or lines[i].startswith("\t")):
                    fn_parts.append(lines[i].strip())
                    i += 1
                footnotes[fn_id] = " ".join(p for p in fn_parts if p)
                continue

            ref_m = REF_DEF_RE.match(line)
            if ref_m:
                ref_key = ref_m.group(1).strip().lower()
                ref_url = ref_m.group(2).strip()
                ref_title = (ref_m.group(3) or "").strip()
                ref_links[ref_key] = (ref_url, ref_title)
                i += 1
                continue

        filtered_lines.append(line)
        i += 1

    nodes = _parse_blocks(filtered_lines, ref_links=ref_links, footnotes=footnotes)
    if frontmatter_node is not None:
        nodes.insert(0, frontmatter_node)

    return Document(nodes=nodes, footnotes=footnotes, ref_links=ref_links)


def _parse_blocks(
    lines: List[str],
    ref_links: Dict[str, Tuple[str, str]],
    footnotes: Dict[str, str],
) -> List[Node]:
    """Parse a list of lines into block AST nodes."""
    nodes: List[Node] = []
    n = len(lines)
    i = 0

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Blank line
        if not stripped:
            i += 1
            continue

        # HTML Comment block
        if stripped.startswith("<!--"):
            comment_lines = [line]
            while i + 1 < n and "-->" not in lines[i]:
                i += 1
                comment_lines.append(lines[i])
            i += 1
            continue

        # Details / Summary block (<details>...)
        if stripped.lower().startswith("<details"):
            det_lines: List[str] = [line]
            i += 1
            while i < n and "</details>" not in lines[i].lower():
                det_lines.append(lines[i])
                i += 1
            if i < n:
                det_lines.append(lines[i])
                i += 1
            raw_det = "\n".join(det_lines)
            sum_m = re.search(r"<summary[^>]*>(.*?)</summary>", raw_det, re.IGNORECASE | re.DOTALL)
            summary = sum_m.group(1).strip() if sum_m else "Details"
            body = re.sub(r"</?details[^>]*>", "", raw_det, flags=re.IGNORECASE)
            body = re.sub(r"<summary[^>]*>.*?</summary>", "", body, flags=re.IGNORECASE | re.DOTALL)
            child_nodes = _parse_blocks(body.split("\n"), ref_links, footnotes)
            nodes.append(DetailsBlock(summary=summary, children=child_nodes))
            continue

        # Math block ($$ ... $$)
        if stripped.startswith("$$"):
            if stripped.endswith("$$") and len(stripped) > 4:
                nodes.append(MathBlock(formula=stripped[2:-2].strip()))
                i += 1
                continue
            math_lines: List[str] = []
            first_rest = stripped[2:].strip()
            if first_rest:
                math_lines.append(first_rest)
            i += 1
            while i < n:
                s = lines[i].strip()
                if s.endswith("$$"):
                    before = s[:-2].strip()
                    if before:
                        math_lines.append(before)
                    i += 1
                    break
                math_lines.append(lines[i])
                i += 1
            nodes.append(MathBlock(formula="\n".join(math_lines).strip()))
            continue

        # Fenced Code Block (``` or ~~~)
        fence_m = FENCE_OPEN_RE.match(line)
        if fence_m:
            indent_len = len(fence_m.group(1))
            fence_chars = fence_m.group(2)
            lang = (fence_m.group(3) or "").strip()
            meta = (fence_m.group(4) or "").strip()
            code_lines: List[str] = []
            i += 1
            close_re = re.compile(rf"^\s{{0,3}}{re.escape(fence_chars[0])}{{{len(fence_chars)},}}\s*$")
            while i < n and not close_re.match(lines[i]):
                cl = lines[i]
                if indent_len > 0 and cl.startswith(" " * indent_len):
                    cl = cl[indent_len:]
                code_lines.append(cl)
                i += 1
            if i < n:
                i += 1  # skip closing fence
            nodes.append(CodeBlock(code="\n".join(code_lines), language=lang, meta=meta))
            continue

        # ATX Heading (# .. ######)
        atx_m = ATX_HEADING_RE.match(line)
        if atx_m:
            level = len(atx_m.group(1))
            title = (atx_m.group(2) or "").strip()
            nodes.append(Heading(level=level, text=title))
            i += 1
            continue

        # Thematic Break (---, ***, ___)
        if THEMATIC_BREAK_RE.match(line):
            nodes.append(ThematicBreak(style=stripped))
            i += 1
            continue

        # Blockquote (> ...)
        if line.lstrip().startswith(">"):
            bq_lines: List[str] = []
            while i < n:
                cur = lines[i]
                if cur.lstrip().startswith(">"):
                    stripped_bq = re.sub(r"^\s*>\s?", "", cur)
                    bq_lines.append(stripped_bq)
                    i += 1
                elif cur.strip() and bq_lines and not THEMATIC_BREAK_RE.match(cur) and not ATX_HEADING_RE.match(cur):
                    # Lazy continuation
                    bq_lines.append(cur)
                    i += 1
                else:
                    break

            alert_type: Optional[str] = None
            alert_title: Optional[str] = None
            if bq_lines:
                am = ALERT_HEADER_RE.match(bq_lines[0])
                if am:
                    alert_type = am.group(1).upper()
                    alert_title = (am.group(2) or "").strip() or None
                    bq_lines = bq_lines[1:]

            children = _parse_blocks(bq_lines, ref_links, footnotes)
            nodes.append(BlockQuote(children=children, alert_type=alert_type, alert_title=alert_title))
            continue

        # GFM Table (Header row + separator row `| --- | --- |`)
        if i + 1 < n and "|" in line:
            alignments = _is_table_separator(lines[i + 1])
            if alignments is not None:
                headers = _split_table_row(line)
                num_cols = max(len(headers), len(alignments))
                while len(headers) < num_cols:
                    headers.append("")
                while len(alignments) < num_cols:
                    alignments.append("left")

                i += 2
                rows: List[List[str]] = []
                while i < n and lines[i].strip() and "|" in lines[i]:
                    if THEMATIC_BREAK_RE.match(lines[i]):
                        break
                    row_cells = _split_table_row(lines[i])
                    if len(row_cells) < num_cols:
                        row_cells.extend([""] * (num_cols - len(row_cells)))
                    elif len(row_cells) > num_cols:
                        row_cells = row_cells[:num_cols]
                    rows.append(row_cells)
                    i += 1
                nodes.append(Table(headers=headers, alignments=alignments, rows=rows))
                continue

        # Lists (Unordered `-`, `*`, `+` and Ordered `1.`, `1)`)
        list_m = LIST_ITEM_RE.match(line)
        if list_m:
            list_node, i = _parse_list(lines, i, ref_links, footnotes)
            nodes.append(list_node)
            continue

        # Indented Code Block (4+ leading spaces or tab)
        if line.startswith("    ") or line.startswith("\t"):
            ind_lines: List[str] = []
            while i < n and (lines[i].startswith("    ") or lines[i].startswith("\t") or not lines[i].strip()):
                if lines[i].startswith("    "):
                    ind_lines.append(lines[i][4:])
                elif lines[i].startswith("\t"):
                    ind_lines.append(lines[i][1:])
                else:
                    ind_lines.append("")
                i += 1
            while ind_lines and not ind_lines[-1].strip():
                ind_lines.pop()
            nodes.append(CodeBlock(code="\n".join(ind_lines), language=""))
            continue

        # Definition List (`Term` followed by `: Definition`)
        if i + 1 < n and DEF_LINE_RE.match(lines[i + 1]):
            def_items: List[DefinitionItem] = []
            while i < n and lines[i].strip() and i + 1 < n and DEF_LINE_RE.match(lines[i + 1]):
                term = lines[i].strip()
                i += 1
                defs: List[str] = []
                while i < n:
                    dm = DEF_LINE_RE.match(lines[i])
                    if dm:
                        defs.append(dm.group(1).strip())
                        i += 1
                    elif not lines[i].strip():
                        # Check if next non-empty line is another `: def`
                        if i + 1 < n and DEF_LINE_RE.match(lines[i + 1]):
                            i += 1
                            continue
                        i += 1
                        break
                    else:
                        break
                def_items.append(DefinitionItem(term=term, definitions=defs))
            nodes.append(DefinitionList(items=def_items))
            continue

        # Setext Heading (Paragraph line followed by `===` or `---`)
        if i + 1 < n:
            next_line = lines[i + 1]
            if SETEXT_H1_RE.match(next_line):
                nodes.append(Heading(level=1, text=stripped))
                i += 2
                continue
            if SETEXT_H2_RE.match(next_line) and not LIST_ITEM_RE.match(line):
                nodes.append(Heading(level=2, text=stripped))
                i += 2
                continue

        # Paragraph (accumulate until blank line or block starter)
        para_lines: List[str] = []
        while i < n:
            cur = lines[i]
            cur_s = cur.strip()
            if not cur_s:
                break
            if para_lines:
                # Check if next line starts another block
                if (
                    ATX_HEADING_RE.match(cur)
                    or FENCE_OPEN_RE.match(cur)
                    or THEMATIC_BREAK_RE.match(cur)
                    or cur.lstrip().startswith(">")
                    or LIST_ITEM_RE.match(cur)
                    or cur_s.startswith("$$")
                    or cur_s.lower().startswith("<details")
                    or (i + 1 < n and "|" in cur and _is_table_separator(lines[i + 1]) is not None)
                    or DEF_LINE_RE.match(cur)
                ):
                    break
                if SETEXT_H1_RE.match(cur):
                    # Convert accumulated paragraph into H1
                    heading_text = " ".join(p.strip() for p in para_lines)
                    nodes.append(Heading(level=1, text=heading_text))
                    para_lines = []
                    i += 1
                    break
                if SETEXT_H2_RE.match(cur):
                    heading_text = " ".join(p.strip() for p in para_lines)
                    nodes.append(Heading(level=2, text=heading_text))
                    para_lines = []
                    i += 1
                    break

            # Support hard line break (two trailing spaces or trailing backslash)
            if cur.endswith("  ") or cur.endswith("\\"):
                clean = cur[:-1].rstrip() if cur.endswith("\\") else cur.rstrip()
                para_lines.append(clean + "\n")
            else:
                para_lines.append(cur.strip())
            i += 1

        if para_lines:
            # Join lines, keeping explicit hard breaks (\n)
            merged: List[str] = []
            for p in para_lines:
                if merged and merged[-1].endswith("\n"):
                    merged.append(p)
                elif merged:
                    merged.append(" " + p)
                else:
                    merged.append(p)
            nodes.append(Paragraph(text="".join(merged)))

    return nodes


def _parse_list(
    lines: List[str],
    start_idx: int,
    ref_links: Dict[str, Tuple[str, str]],
    footnotes: Dict[str, str],
) -> Tuple[ListBlock, int]:
    """Parse a potentially nested ordered or unordered list."""
    n = len(lines)
    first_m = LIST_ITEM_RE.match(lines[start_idx])
    assert first_m is not None
    base_indent = len(first_m.group(1).expandtabs(4))
    first_marker = first_m.group(2)
    ordered = first_marker[0].isdigit()
    start_num = int(first_marker[:-1]) if ordered else 1

    items: List[ListItem] = []
    i = start_idx

    while i < n:
        line = lines[i]
        if not line.strip():
            # Look ahead to see if list continues after blank line
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j >= n:
                break
            next_m = LIST_ITEM_RE.match(lines[j])
            next_indent = len(lines[j]) - len(lines[j].lstrip(" \t"))
            if next_m and len(next_m.group(1).expandtabs(4)) >= base_indent:
                i = j
                continue
            elif next_indent > base_indent and items:
                i = j
            else:
                break

        if THEMATIC_BREAK_RE.match(lines[i]):
            break

        m = LIST_ITEM_RE.match(lines[i])
        if m:
            indent = len(m.group(1).expandtabs(4))
            marker = m.group(2)
            content = m.group(3).strip()

            if indent < base_indent:
                break

            if indent == base_indent:
                # Check if marker type changed between ordered and unordered at same level
                is_ord = marker[0].isdigit()
                if is_ord != ordered and items:
                    break

                checked: Optional[bool] = None
                tm = TASK_MARKER_RE.match(content)
                if tm:
                    checked = tm.group(1).lower() == "x"
                    content = tm.group(2).strip()

                item = ListItem(text=content, checked=checked)
                items.append(item)
                i += 1

                # Collect sub-lines or nested lists belonging to this item
                sub_lines: List[str] = []
                while i < n:
                    sub = lines[i]
                    if not sub.strip():
                        # Check if next non-empty line is still indented under this item
                        k = i + 1
                        while k < n and not lines[k].strip():
                            k += 1
                        if k < n:
                            sub_m = LIST_ITEM_RE.match(lines[k])
                            sub_ind = len(lines[k].expandtabs(4)) - len(lines[k].expandtabs(4).lstrip(" "))
                            if (sub_m and len(sub_m.group(1).expandtabs(4)) > base_indent) or (not sub_m and sub_ind > base_indent):
                                sub_lines.append("")
                                i += 1
                                continue
                        break

                    if THEMATIC_BREAK_RE.match(sub):
                        break

                    sub_m = LIST_ITEM_RE.match(sub)
                    if sub_m:
                        sub_ind = len(sub_m.group(1).expandtabs(4))
                        if sub_ind <= base_indent:
                            break
                        sub_lines.append(sub)
                        i += 1
                    else:
                        sub_ind = len(sub.expandtabs(4)) - len(sub.expandtabs(4).lstrip(" "))
                        if sub_ind > base_indent:
                            # Continuation line or child block
                            sub_lines.append(sub[min(len(sub) - len(sub.lstrip()), base_indent + 2):])
                            i += 1
                        else:
                            break

                if sub_lines:
                    # If first sub_line is plain continuation text (not a list/block starter), append to item.text
                    while sub_lines and sub_lines[0].strip() and not LIST_ITEM_RE.match(sub_lines[0]) and not FENCE_OPEN_RE.match(sub_lines[0]) and not sub_lines[0].lstrip().startswith(">"):
                        item.text = (item.text + " " + sub_lines.pop(0).strip()).strip()
                    if sub_lines:
                        item.children = _parse_blocks(sub_lines, ref_links, footnotes)
                continue

            # If indent > base_indent without a parent item (unusual), parse as nested list
            if items:
                nested_list, i = _parse_list(lines, i, ref_links, footnotes)
                items[-1].children.append(nested_list)
                continue

        break

    return ListBlock(ordered=ordered, start=start_num, items=items), i
