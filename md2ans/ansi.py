"""ANSI escape sequence utilities, CGA/EGA 80s palettes, and CP437 box/wrap helpers."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Tuple

# Regex matching ANSI CSI / OSC escape sequences
ANSI_RE = re.compile(r"\x1b(?:\[[0-9;]*[a-zA-Z]|\].*?(?:\x07|\x1b\\))")

RESET = "\x1b[0m"


@dataclass(frozen=True)
class Palette:
    """80s BBS / DOS CGA-EGA Color Palette specification."""

    name: str
    description: str

    # Primary structural colors
    border_bright: str      # High-intensity frame border
    border_mid: str         # Medium frame border
    border_dim: str         # Low-intensity / shadow border
    shadow: str             # Drop shadow color

    # Shading gradient (4 steps: light -> dark or outer -> inner)
    shade_1: str
    shade_2: str
    shade_3: str
    shade_4: str

    # Headings
    h1_text: str
    h1_bg: str
    h1_accent: str
    h2_text: str
    h2_accent: str
    h3_text: str
    h3_accent: str
    h4_text: str
    h5_text: str
    h6_text: str

    # Body & Inline styles
    body: str
    bold: str
    italic: str
    bold_italic: str
    strikethrough: str
    underline: str
    highlight: str
    code_inline: str
    kbd: str
    sub_sup: str

    # Links & Media
    link_text: str
    link_url: str
    link_bracket: str
    image_border: str
    image_label: str
    footnote: str

    # Blocks
    quote_bar: str
    quote_text: str
    list_bullet_1: str
    list_bullet_2: str
    list_bullet_3: str
    list_number: str
    task_done: str
    task_todo: str

    # Code block & Syntax
    code_border: str
    code_title: str
    code_bg: str
    code_lineno: str
    syn_keyword: str
    syn_string: str
    syn_comment: str
    syn_number: str
    syn_func: str
    syn_type: str
    syn_operator: str
    syn_builtin: str

    # Tables
    table_border: str
    table_header_text: str
    table_header_bg: str
    table_row_even: str
    table_row_odd: str

    # Admonitions / Alerts
    note_color: str
    tip_color: str
    important_color: str
    warning_color: str
    caution_color: str


PALETTES: dict[str, Palette] = {
    "bbs": Palette(
        name="bbs",
        description="Classic 80s BBS / DOS ANSI Art (16-color EGA/VGA palette)",
        border_bright="\x1b[1;96m",      # Bright Cyan
        border_mid="\x1b[36m",           # Cyan
        border_dim="\x1b[1;34m",         # Bright Blue
        shadow="\x1b[90m",               # Dark Gray (EGA Bright Black)
        shade_1="\x1b[90m",              # Dark Gray
        shade_2="\x1b[34m",              # Blue
        shade_3="\x1b[36m",              # Cyan
        shade_4="\x1b[1;96m",            # Bright Cyan
        h1_text="\x1b[1;93;44m",         # Bright Yellow on Royal Blue
        h1_bg="\x1b[44m",                # Blue BG
        h1_accent="\x1b[1;97;44m",       # Bright White on Blue
        h2_text="\x1b[1;97m",            # Bright White
        h2_accent="\x1b[1;95m",          # Bright Magenta
        h3_text="\x1b[1;96m",            # Bright Cyan
        h3_accent="\x1b[1;93m",          # Bright Yellow
        h4_text="\x1b[1;92m",            # Bright Green
        h5_text="\x1b[1;93m",            # Bright Yellow
        h6_text="\x1b[36m",              # Dim Cyan
        body="\x1b[37m",                 # Light Gray (Standard DOS text)
        bold="\x1b[1;93m",               # High-intensity Yellow
        italic="\x1b[3;96m",             # Italic Bright Cyan
        bold_italic="\x1b[1;3;95m",      # Bold Italic Bright Magenta
        strikethrough="\x1b[9;90m",      # Strikethrough Dark Gray
        underline="\x1b[4;97m",          # Underlined Bright White
        highlight="\x1b[1;93;45m",       # Bright Yellow on Magenta
        code_inline="\x1b[1;92;40m",     # Phosphor Green on Black
        kbd="\x1b[1;97;100m",            # Bright White on Dark Gray keycap
        sub_sup="\x1b[1;95m",            # Bright Magenta
        link_text="\x1b[1;4;96m",        # Bold Underlined Bright Cyan
        link_url="\x1b[32m",             # Green
        link_bracket="\x1b[1;90m",       # Dark Gray brackets
        image_border="\x1b[1;95m",       # Bright Magenta
        image_label="\x1b[1;93m",        # Bright Yellow
        footnote="\x1b[1;95m",           # Bright Magenta
        quote_bar="\x1b[1;95m",          # Bright Magenta
        quote_text="\x1b[3;96m",         # Italic Cyan
        list_bullet_1="\x1b[1;96m",      # Bright Cyan
        list_bullet_2="\x1b[1;95m",      # Bright Magenta
        list_bullet_3="\x1b[1;93m",      # Bright Yellow
        list_number="\x1b[1;93m",        # Bright Yellow
        task_done="\x1b[1;92m",          # Bright Green
        task_todo="\x1b[90m",            # Dark Gray
        code_border="\x1b[1;34m",        # Bright Blue (Borland IDE style)
        code_title="\x1b[1;93;44m",      # Bright Yellow on Blue
        code_bg="",
        code_lineno="\x1b[90m",          # Dark Gray
        syn_keyword="\x1b[1;93m",        # Bright Yellow (Turbo Pascal keywords)
        syn_string="\x1b[1;92m",         # Bright Green
        syn_comment="\x1b[36m",          # Cyan/Dim comments
        syn_number="\x1b[1;95m",         # Bright Magenta
        syn_func="\x1b[1;97m",           # Bright White
        syn_type="\x1b[1;96m",           # Bright Cyan
        syn_operator="\x1b[93m",         # Yellow/Brown
        syn_builtin="\x1b[95m",          # Magenta
        table_border="\x1b[36m",         # Cyan
        table_header_text="\x1b[1;93;44m",
        table_header_bg="\x1b[44m",
        table_row_even="\x1b[37m",
        table_row_odd="\x1b[97m",
        note_color="\x1b[1;96m",         # Bright Cyan
        tip_color="\x1b[1;92m",          # Bright Green
        important_color="\x1b[1;95m",    # Bright Magenta
        warning_color="\x1b[1;93m",      # Bright Yellow
        caution_color="\x1b[1;91m",      # Bright Red
    ),
    "cga1": Palette(
        name="cga1",
        description="IBM CGA Mode 4 Palette 1 (High-Intensity Cyan / Magenta / White)",
        border_bright="\x1b[1;96m",
        border_mid="\x1b[1;95m",
        border_dim="\x1b[36m",
        shadow="\x1b[35m",
        shade_1="\x1b[35m",
        shade_2="\x1b[36m",
        shade_3="\x1b[1;95m",
        shade_4="\x1b[1;96m",
        h1_text="\x1b[1;97;45m",
        h1_bg="\x1b[45m",
        h1_accent="\x1b[1;96;45m",
        h2_text="\x1b[1;97m",
        h2_accent="\x1b[1;95m",
        h3_text="\x1b[1;96m",
        h3_accent="\x1b[1;95m",
        h4_text="\x1b[1;97m",
        h5_text="\x1b[96m",
        h6_text="\x1b[95m",
        body="\x1b[37m",
        bold="\x1b[1;97m",
        italic="\x1b[3;96m",
        bold_italic="\x1b[1;3;95m",
        strikethrough="\x1b[9;35m",
        underline="\x1b[4;96m",
        highlight="\x1b[1;97;45m",
        code_inline="\x1b[1;96;40m",
        kbd="\x1b[1;97;45m",
        sub_sup="\x1b[1;95m",
        link_text="\x1b[1;4;96m",
        link_url="\x1b[95m",
        link_bracket="\x1b[36m",
        image_border="\x1b[1;95m",
        image_label="\x1b[1;97m",
        footnote="\x1b[1;95m",
        quote_bar="\x1b[1;95m",
        quote_text="\x1b[3;96m",
        list_bullet_1="\x1b[1;96m",
        list_bullet_2="\x1b[1;95m",
        list_bullet_3="\x1b[1;97m",
        list_number="\x1b[1;95m",
        task_done="\x1b[1;96m",
        task_todo="\x1b[35m",
        code_border="\x1b[1;95m",
        code_title="\x1b[1;97;45m",
        code_bg="",
        code_lineno="\x1b[36m",
        syn_keyword="\x1b[1;95m",
        syn_string="\x1b[1;96m",
        syn_comment="\x1b[36m",
        syn_number="\x1b[1;97m",
        syn_func="\x1b[1;97m",
        syn_type="\x1b[1;96m",
        syn_operator="\x1b[95m",
        syn_builtin="\x1b[96m",
        table_border="\x1b[1;95m",
        table_header_text="\x1b[1;97;45m",
        table_header_bg="\x1b[45m",
        table_row_even="\x1b[37m",
        table_row_odd="\x1b[96m",
        note_color="\x1b[1;96m",
        tip_color="\x1b[1;97m",
        important_color="\x1b[1;95m",
        warning_color="\x1b[1;95m",
        caution_color="\x1b[1;97;45m",
    ),
    "cga0": Palette(
        name="cga0",
        description="IBM CGA Mode 4 Palette 0 (Green / Red / Yellow-Brown)",
        border_bright="\x1b[1;92m",
        border_mid="\x1b[1;93m",
        border_dim="\x1b[32m",
        shadow="\x1b[33m",
        shade_1="\x1b[33m",
        shade_2="\x1b[32m",
        shade_3="\x1b[1;91m",
        shade_4="\x1b[1;92m",
        h1_text="\x1b[1;93;41m",
        h1_bg="\x1b[41m",
        h1_accent="\x1b[1;92;41m",
        h2_text="\x1b[1;93m",
        h2_accent="\x1b[1;91m",
        h3_text="\x1b[1;92m",
        h3_accent="\x1b[1;93m",
        h4_text="\x1b[1;91m",
        h5_text="\x1b[93m",
        h6_text="\x1b[32m",
        body="\x1b[92m",
        bold="\x1b[1;93m",
        italic="\x1b[3;92m",
        bold_italic="\x1b[1;3;91m",
        strikethrough="\x1b[9;31m",
        underline="\x1b[4;93m",
        highlight="\x1b[1;93;41m",
        code_inline="\x1b[1;93;40m",
        kbd="\x1b[1;93;41m",
        sub_sup="\x1b[1;91m",
        link_text="\x1b[1;4;92m",
        link_url="\x1b[93m",
        link_bracket="\x1b[32m",
        image_border="\x1b[1;91m",
        image_label="\x1b[1;93m",
        footnote="\x1b[1;91m",
        quote_bar="\x1b[1;93m",
        quote_text="\x1b[3;92m",
        list_bullet_1="\x1b[1;92m",
        list_bullet_2="\x1b[1;91m",
        list_bullet_3="\x1b[1;93m",
        list_number="\x1b[1;93m",
        task_done="\x1b[1;92m",
        task_todo="\x1b[33m",
        code_border="\x1b[32m",
        code_title="\x1b[1;93;42m",
        code_bg="",
        code_lineno="\x1b[33m",
        syn_keyword="\x1b[1;93m",
        syn_string="\x1b[1;92m",
        syn_comment="\x1b[32m",
        syn_number="\x1b[1;91m",
        syn_func="\x1b[1;93m",
        syn_type="\x1b[1;92m",
        syn_operator="\x1b[91m",
        syn_builtin="\x1b[93m",
        table_border="\x1b[32m",
        table_header_text="\x1b[1;93;41m",
        table_header_bg="\x1b[41m",
        table_row_even="\x1b[92m",
        table_row_odd="\x1b[93m",
        note_color="\x1b[1;92m",
        tip_color="\x1b[1;93m",
        important_color="\x1b[1;91m",
        warning_color="\x1b[1;93m",
        caution_color="\x1b[1;91m",
    ),
    "phosphor": Palette(
        name="phosphor",
        description="IBM 5151 Green Phosphor CRT Monochrome Monitor",
        border_bright="\x1b[1;92m",
        border_mid="\x1b[32m",
        border_dim="\x1b[2;32m",
        shadow="\x1b[2;32m",
        shade_1="\x1b[2;32m",
        shade_2="\x1b[32m",
        shade_3="\x1b[92m",
        shade_4="\x1b[1;92m",
        h1_text="\x1b[1;30;102m",
        h1_bg="\x1b[102m",
        h1_accent="\x1b[1;30;102m",
        h2_text="\x1b[1;92m",
        h2_accent="\x1b[32m",
        h3_text="\x1b[1;92m",
        h3_accent="\x1b[32m",
        h4_text="\x1b[92m",
        h5_text="\x1b[32m",
        h6_text="\x1b[2;32m",
        body="\x1b[32m",
        bold="\x1b[1;92m",
        italic="\x1b[3;92m",
        bold_italic="\x1b[1;3;92m",
        strikethrough="\x1b[9;2;32m",
        underline="\x1b[4;92m",
        highlight="\x1b[30;42m",
        code_inline="\x1b[1;92m",
        kbd="\x1b[30;42m",
        sub_sup="\x1b[1;92m",
        link_text="\x1b[1;4;92m",
        link_url="\x1b[2;32m",
        link_bracket="\x1b[2;32m",
        image_border="\x1b[1;92m",
        image_label="\x1b[1;92m",
        footnote="\x1b[1;92m",
        quote_bar="\x1b[1;92m",
        quote_text="\x1b[3;32m",
        list_bullet_1="\x1b[1;92m",
        list_bullet_2="\x1b[92m",
        list_bullet_3="\x1b[32m",
        list_number="\x1b[1;92m",
        task_done="\x1b[1;92m",
        task_todo="\x1b[2;32m",
        code_border="\x1b[32m",
        code_title="\x1b[30;42m",
        code_bg="",
        code_lineno="\x1b[2;32m",
        syn_keyword="\x1b[1;92m",
        syn_string="\x1b[92m",
        syn_comment="\x1b[2;32m",
        syn_number="\x1b[1;92m",
        syn_func="\x1b[1;92m",
        syn_type="\x1b[92m",
        syn_operator="\x1b[32m",
        syn_builtin="\x1b[92m",
        table_border="\x1b[32m",
        table_header_text="\x1b[30;42m",
        table_header_bg="\x1b[42m",
        table_row_even="\x1b[32m",
        table_row_odd="\x1b[92m",
        note_color="\x1b[1;92m",
        tip_color="\x1b[1;92m",
        important_color="\x1b[1;92m",
        warning_color="\x1b[1;92m",
        caution_color="\x1b[1;92m",
    ),
    "amber": Palette(
        name="amber",
        description="1980s Amber Phosphor P3 CRT Monitor",
        border_bright="\x1b[1;93m",
        border_mid="\x1b[33m",
        border_dim="\x1b[2;33m",
        shadow="\x1b[2;33m",
        shade_1="\x1b[2;33m",
        shade_2="\x1b[33m",
        shade_3="\x1b[93m",
        shade_4="\x1b[1;93m",
        h1_text="\x1b[1;30;103m",
        h1_bg="\x1b[103m",
        h1_accent="\x1b[1;30;103m",
        h2_text="\x1b[1;93m",
        h2_accent="\x1b[33m",
        h3_text="\x1b[1;93m",
        h3_accent="\x1b[33m",
        h4_text="\x1b[93m",
        h5_text="\x1b[33m",
        h6_text="\x1b[2;33m",
        body="\x1b[33m",
        bold="\x1b[1;93m",
        italic="\x1b[3;93m",
        bold_italic="\x1b[1;3;93m",
        strikethrough="\x1b[9;2;33m",
        underline="\x1b[4;93m",
        highlight="\x1b[30;43m",
        code_inline="\x1b[1;93m",
        kbd="\x1b[30;43m",
        sub_sup="\x1b[1;93m",
        link_text="\x1b[1;4;93m",
        link_url="\x1b[2;33m",
        link_bracket="\x1b[2;33m",
        image_border="\x1b[1;93m",
        image_label="\x1b[1;93m",
        footnote="\x1b[1;93m",
        quote_bar="\x1b[1;93m",
        quote_text="\x1b[3;33m",
        list_bullet_1="\x1b[1;93m",
        list_bullet_2="\x1b[93m",
        list_bullet_3="\x1b[33m",
        list_number="\x1b[1;93m",
        task_done="\x1b[1;93m",
        task_todo="\x1b[2;33m",
        code_border="\x1b[33m",
        code_title="\x1b[30;43m",
        code_bg="",
        code_lineno="\x1b[2;33m",
        syn_keyword="\x1b[1;93m",
        syn_string="\x1b[93m",
        syn_comment="\x1b[2;33m",
        syn_number="\x1b[1;93m",
        syn_func="\x1b[1;93m",
        syn_type="\x1b[93m",
        syn_operator="\x1b[33m",
        syn_builtin="\x1b[93m",
        table_border="\x1b[33m",
        table_header_text="\x1b[30;43m",
        table_header_bg="\x1b[43m",
        table_row_even="\x1b[33m",
        table_row_odd="\x1b[93m",
        note_color="\x1b[1;93m",
        tip_color="\x1b[1;93m",
        important_color="\x1b[1;93m",
        warning_color="\x1b[1;93m",
        caution_color="\x1b[1;93m",
    ),
}


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from text."""
    return ANSI_RE.sub("", text)


def char_width(ch: str) -> int:
    """Return terminal column width of a single Unicode character."""
    if not ch or ch in ("\n", "\r"):
        return 0
    if unicodedata.combining(ch):
        return 0
    eaw = unicodedata.east_asian_width(ch)
    if eaw in ("W", "F"):
        return 2
    return 1


def visible_len(text: str) -> int:
    """Return the visible column width of an ANSI-formatted string."""
    plain = strip_ansi(text)
    return sum(char_width(c) for c in plain)


def _tokenize_ansi(text: str) -> List[Tuple[str, bool]]:
    """Split string into (token, is_ansi) pairs."""
    tokens: List[Tuple[str, bool]] = []
    pos = 0
    for match in ANSI_RE.finditer(text):
        start, end = match.span()
        if start > pos:
            tokens.append((text[pos:start], False))
        tokens.append((match.group(0), True))
        pos = end
    if pos < len(text):
        tokens.append((text[pos:], False))
    return tokens


def pad_ansi(text: str, width: int, align: str = "left", fill: str = " ") -> str:
    """Pad an ANSI string to `width` visible columns."""
    vlen = visible_len(text)
    if vlen >= width:
        return text
    diff = width - vlen
    if align == "right":
        return (fill * diff) + text
    if align == "center":
        left = diff // 2
        right = diff - left
        return (fill * left) + text + (fill * right)
    return text + (fill * diff)


def truncate_ansi(text: str, max_width: int, ellipsis: str = "…") -> str:
    """Truncate an ANSI string to at most `max_width` visible columns."""
    if visible_len(text) <= max_width:
        return text
    ell_w = visible_len(ellipsis)
    target = max(0, max_width - ell_w)
    out: List[str] = []
    cur = 0
    has_ansi = False
    for tok, is_ansi in _tokenize_ansi(text):
        if is_ansi:
            out.append(tok)
            has_ansi = True
        else:
            for ch in tok:
                cw = char_width(ch)
                if cur + cw > target:
                    out.append(ellipsis)
                    if has_ansi:
                        out.append(RESET)
                    return "".join(out)
                out.append(ch)
                cur += cw
    if has_ansi:
        out.append(RESET)
    return "".join(out)


def wrap_ansi(
    text: str,
    width: int,
    initial_indent: str = "",
    subsequent_indent: str = "",
    base_style: str = "",
) -> List[str]:
    """Word-wrap an ANSI-styled paragraph while preserving active SGR styles across line breaks."""
    if width <= 4:
        return [text]

    # Split into words while keeping track of ANSI codes attached to words
    # First split by explicit newlines
    raw_lines = text.split("\n")
    result_lines: List[str] = []

    active_codes: List[str] = []
    if base_style:
        active_codes.append(base_style)

    def current_style_prefix() -> str:
        return "".join(active_codes)

    def update_active_codes(seq: str) -> None:
        if seq in ("\x1b[0m", "\x1b[m"):
            active_codes.clear()
            if base_style:
                active_codes.append(base_style)
        else:
            active_codes.append(seq)

    for line_idx, raw_line in enumerate(raw_lines):
        indent = initial_indent if (line_idx == 0 and not result_lines) else subsequent_indent
        indent_w = visible_len(indent)
        avail = max(4, width - indent_w)

        # Break raw_line into word tokens (preserving spaces and ANSI sequences)
        # A word token is a sequence of non-space characters + attached ANSI codes
        words: List[str] = []
        current_word: List[str] = []
        in_space = False

        for tok, is_ansi in _tokenize_ansi(raw_line):
            if is_ansi:
                current_word.append(tok)
            else:
                for ch in tok:
                    if ch == " ":
                        if not in_space and current_word:
                            words.append("".join(current_word))
                            current_word = []
                        in_space = True
                        current_word.append(ch)
                    else:
                        if in_space and current_word:
                            words.append("".join(current_word))
                            current_word = []
                        in_space = False
                        current_word.append(ch)
        if current_word:
            words.append("".join(current_word))

        if not words:
            result_lines.append(indent.rstrip())
            continue

        cur_line_parts: List[str] = [indent, current_style_prefix()]
        cur_w = 0

        for word in words:
            w_plain = strip_ansi(word)
            w_len = visible_len(word)
            is_whitespace = len(w_plain) > 0 and w_plain.strip(" ") == ""

            if is_whitespace:
                # Only add space if not at start of line and fits on current line
                if cur_w > 0 and cur_w + w_len <= avail:
                    cur_line_parts.append(word)
                    cur_w += w_len
                # Update any ANSI state inside the whitespace token
                for tok, is_ansi in _tokenize_ansi(word):
                    if is_ansi:
                        update_active_codes(tok)
                continue

            # If a single word is wider than `avail`, break it by character
            if w_len > avail:
                if cur_w > 0:
                    cur_line_parts.append(RESET)
                    result_lines.append("".join(cur_line_parts))
                    indent = subsequent_indent
                    indent_w = visible_len(indent)
                    avail = max(4, width - indent_w)
                    cur_line_parts = [indent, current_style_prefix()]
                    cur_w = 0

                for tok, is_ansi in _tokenize_ansi(word):
                    if is_ansi:
                        cur_line_parts.append(tok)
                        update_active_codes(tok)
                    else:
                        for ch in tok:
                            cw = char_width(ch)
                            if cur_w + cw > avail and cur_w > 0:
                                cur_line_parts.append(RESET)
                                result_lines.append("".join(cur_line_parts))
                                indent = subsequent_indent
                                indent_w = visible_len(indent)
                                avail = max(4, width - indent_w)
                                cur_line_parts = [indent, current_style_prefix()]
                                cur_w = 0
                            cur_line_parts.append(ch)
                            cur_w += cw
                continue

            if cur_w + w_len > avail and cur_w > 0:
                # Strip trailing spaces before wrapping
                cur_line_parts.append(RESET)
                result_lines.append("".join(cur_line_parts))
                indent = subsequent_indent
                indent_w = visible_len(indent)
                avail = max(4, width - indent_w)
                cur_line_parts = [indent, current_style_prefix()]
                cur_w = 0

            cur_line_parts.append(word)
            cur_w += w_len
            for tok, is_ansi in _tokenize_ansi(word):
                if is_ansi:
                    update_active_codes(tok)

        cur_line_parts.append(RESET)
        result_lines.append("".join(cur_line_parts))

    return result_lines


def shade_bar(palette: Palette, reverse: bool = False) -> str:
    """Return a 4-character CP437 graduated shading block bar (░▒▓█ or █▓▒░)."""
    if not reverse:
        return (
            f"{palette.shade_1}░"
            f"{palette.shade_2}▒"
            f"{palette.shade_3}▓"
            f"{palette.shade_4}█{RESET}"
        )
    return (
        f"{palette.shade_4}█"
        f"{palette.shade_3}▓"
        f"{palette.shade_2}▒"
        f"{palette.shade_1}░{RESET}"
    )
