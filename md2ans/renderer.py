"""80s BBS / DOS ANSI Art Renderer for Markdown AST nodes and inline tags."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .ansi import (
    PALETTES,
    RESET,
    Palette,
    pad_ansi,
    shade_bar,
    strip_ansi,
    truncate_ansi,
    visible_len,
    wrap_ansi,
)
from .parser import (
    BlockQuote,
    CodeBlock,
    DefinitionList,
    DetailsBlock,
    Document,
    Frontmatter,
    Heading,
    HtmlBlock,
    ListBlock,
    MathBlock,
    Node,
    Paragraph,
    Table,
    ThematicBreak,
)
from .syntax import highlight_line

# Retro emoji shortcode lookup table
EMOJI_MAP: Dict[str, str] = {
    "floppy_disk": "💾",
    "computer": "🖥️",
    "desktop_computer": "🖥️",
    "keyboard": "⌨️",
    "joystick": "🕹️",
    "video_game": "👾",
    "space_invader": "👾",
    "alien": "👽",
    "robot": "🤖",
    "skull": "💀",
    "fire": "🔥",
    "zap": "⚡",
    "bolt": "⚡",
    "rocket": "🚀",
    "star": "★",
    "sparkles": "✦",
    "warning": "⚠",
    "check": "✔",
    "white_check_mark": "✔",
    "x": "✖",
    "cross_mark": "✖",
    "heart": "♥",
    "music": "♫",
    "notes": "♫",
    "phone": "☎",
    "telephone": "☎",
    "modem": "📠",
    "pager": "📟",
    "cassette": "📼",
    "vhs": "📼",
    "tv": "📺",
    "radio": "📻",
    "cd": "💿",
    "dvd": "📀",
    "bulb": "💡",
    "gear": "⚙",
    "lock": "🔒",
    "key": "🔑",
    "mag": "🔍",
    "bug": "🐞",
    "trophy": "🏆",
    "crown": "♛",
    "diamond": "◆",
    "coffee": "☕",
    "beer": "🍺",
    "pizza": "🍕",
    "sunglasses": "😎",
    "thumbsup": "👍",
    "+1": "👍",
    "-1": "👎",
    "wave": "👋",
    "eyes": "👀",
    "100": "💯",
    "info": "ℹ",
}

SUPERSCRIPT_CHARS = str.maketrans(
    "0123456789+-=()nija",
    "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱʲᵃ",
)

SUBSCRIPT_CHARS = str.maketrans(
    "0123456789+-=()aeioruvx",
    "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑᵢₒᵣᵤᵥₓ",
)

MATH_SYMBOLS: List[Tuple[str, str]] = [
    (r"\alpha", "α"),
    (r"\beta", "β"),
    (r"\gamma", "γ"),
    (r"\delta", "δ"),
    (r"\epsilon", "ε"),
    (r"\theta", "θ"),
    (r"\lambda", "λ"),
    (r"\mu", "μ"),
    (r"\pi", "π"),
    (r"\sigma", "σ"),
    (r"\tau", "τ"),
    (r"\phi", "φ"),
    (r"\omega", "ω"),
    (r"\Delta", "Δ"),
    (r"\Sigma", "Σ"),
    (r"\Omega", "Ω"),
    (r"\Pi", "Π"),
    (r"\sum", "∑"),
    (r"\prod", "∏"),
    (r"\int", "∫"),
    (r"\sqrt", "√"),
    (r"\infty", "∞"),
    (r"\approx", "≈"),
    (r"\neq", "≠"),
    (r"\ne", "≠"),
    (r"\leq", "≤"),
    (r"\le", "≤"),
    (r"\geq", "≥"),
    (r"\ge", "≥"),
    (r"\pm", "±"),
    (r"\mp", "∓"),
    (r"\times", "×"),
    (r"\cdot", "·"),
    (r"\div", "÷"),
    (r"\partial", "∂"),
    (r"\nabla", "∇"),
    (r"\forall", "∀"),
    (r"\exists", "∃"),
    (r"\in", "∈"),
    (r"\notin", "∉"),
    (r"\subset", "⊂"),
    (r"\subseteq", "⊆"),
    (r"\cup", "∪"),
    (r"\cap", "∩"),
    (r"\rightarrow", "→"),
    (r"\to", "→"),
    (r"\leftarrow", "←"),
    (r"\Rightarrow", "⇒"),
    (r"\iff", "⇔"),
    (r"\log", "log"),
    (r"\ln", "ln"),
    (r"\sin", "sin"),
    (r"\cos", "cos"),
    (r"\tan", "tan"),
    (r"\lim", "lim"),
    (r"\max", "max"),
    (r"\min", "min"),
    (r"\exp", "exp"),
]

STANDALONE_IMG_RE = re.compile(
    r'^\s*!\[([^\]]*)\]\(\s*<?([^\s>")]*)>?(?:\s+["\'](.*?)["\'])?\s*\)\s*$'
)


def format_math(formula: str) -> str:
    """Convert LaTeX-like math symbols into retro terminal Unicode glyphs."""
    out = formula
    # Handle \frac{a}{b} -> (a)/(b)
    out = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1/\2)", out)
    # Handle \sqrt{x} -> √(x)
    out = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", out)
    for latex_sym, uni_sym in MATH_SYMBOLS:
        out = out.replace(latex_sym, uni_sym)
    # Superscripts ^{...} or ^x
    out = re.sub(
        r"\^\{([^{}]+)\}",
        lambda m: m.group(1).translate(SUPERSCRIPT_CHARS),
        out,
    )
    out = re.sub(
        r"\^([0-9nija+-])",
        lambda m: m.group(1).translate(SUPERSCRIPT_CHARS),
        out,
    )
    # Subscripts _{...} or _x
    out = re.sub(
        r"_\{([^{}]+)\}",
        lambda m: m.group(1).translate(SUBSCRIPT_CHARS),
        out,
    )
    out = re.sub(
        r"_([0-9aeioruvx+-])",
        lambda m: m.group(1).translate(SUBSCRIPT_CHARS),
        out,
    )
    out = out.replace("{", "").replace("}", "")
    return out


class AnsiRenderer:
    """Render a parsed Markdown Document into 80s BBS / DOS ANSI Art."""

    def __init__(
        self,
        width: int = 80,
        palette_name: str = "bbs",
        show_header: bool = False,
        plain: bool = False,
    ) -> None:
        self.width = max(40, width)
        self.palette = PALETTES.get(palette_name, PALETTES["bbs"])
        self.show_header = show_header
        self.plain = plain
        self.ref_links: Dict[str, Tuple[str, str]] = {}
        self.footnotes: Dict[str, str] = {}

    def render(self, doc: Document) -> str:
        """Render a Document AST into an ANSI-formatted string."""
        self.ref_links = doc.ref_links
        self.footnotes = doc.footnotes

        blocks: List[str] = []

        if self.show_header:
            blocks.append(self._render_bbs_banner())

        for node in doc.nodes:
            rendered = self._render_node(node, width=self.width)
            if rendered:
                blocks.append(rendered)

        if doc.footnotes:
            blocks.append(self._render_footnotes(doc.footnotes, width=self.width))

        if self.show_header:
            blocks.append(self._render_bbs_footer())

        output = "\n\n".join(blocks) + "\n"
        if self.plain:
            return strip_ansi(output)
        return output

    # --- Inline Markdown Renderer ---

    def render_inline(self, text: str, base_style: Optional[str] = None) -> str:
        """Render all inline Markdown tags into ANSI-styled text."""
        if not text:
            return ""
        p = self.palette
        b_style = base_style if base_style is not None else p.body

        # Protect escaped characters and inline code spans with placeholders
        placeholders: List[str] = []

        def save_placeholder(rendered_val: str) -> str:
            idx = len(placeholders)
            placeholders.append(rendered_val + b_style)
            return f"\x00PH{idx}PH\x00"

        # 1. Inline code spans (``code`` or `code`) - parsed before backslash escapes per CommonMark
        def replace_code_span(m: re.Match[str]) -> str:
            code_content = m.group(2).strip() if len(m.group(1)) > 1 else m.group(2)
            styled = (
                f"{p.border_dim}▐{RESET}"
                f"{p.code_inline} {code_content} {RESET}"
                f"{p.border_dim}▌{RESET}"
            )
            return save_placeholder(styled)

        out = re.sub(r"(`+)(.+?)\1", replace_code_span, text)

        # 2. Escaped characters (e.g. \*, \_, \`, \|, \\)
        out = re.sub(
            r"\\([\\`*_{}\[\]()#+\-.!|<>~^$=])",
            lambda m: save_placeholder(f"{b_style}{m.group(1)}"),
            out,
        )

        # 3. Inline Math ($...$)
        def replace_inline_math(m: re.Match[str]) -> str:
            expr = format_math(m.group(1).strip())
            styled = f"{p.border_dim}ƒ({RESET}{p.sub_sup}{expr}{RESET}{p.border_dim}){RESET}"
            return save_placeholder(styled)

        out = re.sub(r"(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)", replace_inline_math, out)

        # 4. HTML <kbd>...</kbd>
        def replace_kbd(m: re.Match[str]) -> str:
            key = m.group(1).strip()
            styled = (
                f"{p.border_bright}▐{RESET}"
                f"{p.kbd}[{key}]{RESET}"
                f"{p.shadow}▌{RESET}"
            )
            return save_placeholder(styled)

        out = re.sub(r"<kbd>(.*?)</kbd>", replace_kbd, out, flags=re.IGNORECASE)

        # 5. HTML inline tags (<br>, <mark>, <u>, <ins>, <del>, <s>, <b>, <strong>, <i>, <em>, <sup>, <sub>, <abbr>)
        out = re.sub(r"<br\s*/?>", "\n", out, flags=re.IGNORECASE)
        out = re.sub(
            r"<mark>(.*?)</mark>",
            lambda m: save_placeholder(f"{p.highlight} {m.group(1)} {RESET}"),
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"<(?:u|ins)>(.*?)</(?:u|ins)>",
            lambda m: f"{p.underline}{m.group(1)}{RESET}{b_style}",
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"<(?:del|s)>(.*?)</(?:del|s)>",
            lambda m: f"{p.strikethrough}{m.group(1)}{RESET}{b_style}",
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"<(?:b|strong)>(.*?)</(?:b|strong)>",
            lambda m: f"{p.bold}{m.group(1)}{RESET}{b_style}",
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"<(?:i|em)>(.*?)</(?:i|em)>",
            lambda m: f"{p.italic}{m.group(1)}{RESET}{b_style}",
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"<sup>(.*?)</sup>",
            lambda m: save_placeholder(f"{p.sub_sup}{m.group(1).translate(SUPERSCRIPT_CHARS)}{RESET}"),
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"<sub>(.*?)</sub>",
            lambda m: save_placeholder(f"{p.sub_sup}{m.group(1).translate(SUBSCRIPT_CHARS)}{RESET}"),
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r'<abbr\s+title=["\'](.*?)["\'][^>]*>(.*?)</abbr>',
            lambda m: f"{p.underline}{m.group(2)}{RESET}{p.shadow}({m.group(1)}){RESET}{b_style}",
            out,
            flags=re.IGNORECASE,
        )

        # 6. Inline Images: ![alt](url "title") and ![alt][ref]
        def replace_image(m: re.Match[str]) -> str:
            alt = m.group(1).strip() or "IMAGE"
            url = m.group(2).strip()
            title = (m.group(3) or "").strip()
            title_part = f" \"{title}\"" if title else ""
            styled = (
                f"{p.image_border}╔═[{RESET}"
                f"{p.image_label} ▀▄ IMG: {alt} ▄▀ {RESET}"
                f"{p.image_border}]═►{RESET}"
                f"{p.link_bracket}({RESET}{p.link_url}{url}{title_part}{RESET}{p.link_bracket}){RESET}"
            )
            return save_placeholder(styled)

        out = re.sub(
            r'!\[([^\]]*)\]\(\s*<?([^\s>")]*)>?(?:\s+["\'](.*?)["\'])?\s*\)',
            replace_image,
            out,
        )

        def replace_ref_image(m: re.Match[str]) -> str:
            alt = m.group(1).strip() or "IMAGE"
            ref = (m.group(2).strip() or alt).lower()
            url, title = self.ref_links.get(ref, (f"#{ref}", ""))
            title_part = f" \"{title}\"" if title else ""
            styled = (
                f"{p.image_border}╔═[{RESET}"
                f"{p.image_label} ▀▄ IMG: {alt} ▄▀ {RESET}"
                f"{p.image_border}]═►{RESET}"
                f"{p.link_bracket}({RESET}{p.link_url}{url}{title_part}{RESET}{p.link_bracket}){RESET}"
            )
            return save_placeholder(styled)

        out = re.sub(r"!\[([^\]]*)\]\[([^\]]*)\]", replace_ref_image, out)

        # 7. Footnote references: [^id]
        def replace_footnote_ref(m: re.Match[str]) -> str:
            fn_id = m.group(1).strip()
            styled = f"{p.link_bracket}[{RESET}{p.footnote}#{fn_id}{RESET}{p.link_bracket}]{RESET}"
            return save_placeholder(styled)

        out = re.sub(r"\[\^([^\]]+)\]", replace_footnote_ref, out)

        # 8. Links: [text](url "title")
        def replace_link(m: re.Match[str]) -> str:
            label = self.render_inline(m.group(1).strip(), base_style=p.link_text)
            url = m.group(2).strip()
            title = (m.group(3) or "").strip()
            title_suffix = f" · {title}" if title else ""
            if strip_ansi(label) == url:
                styled = f"{p.link_bracket}◄{RESET}{p.link_text}{url}{RESET}{p.link_bracket}►{RESET}"
            else:
                styled = (
                    f"{p.link_bracket}◄{RESET}{p.link_text}{label}{RESET}{p.link_bracket}►{RESET}"
                    f"{p.link_bracket}─[{RESET}{p.link_url}{url}{title_suffix}{RESET}{p.link_bracket}]{RESET}"
                )
            return save_placeholder(styled)

        out = re.sub(
            r'\[([^\]]+)\]\(\s*<?([^\s>")]*)>?(?:\s+["\'](.*?)["\'])?\s*\)',
            replace_link,
            out,
        )

        # Reference links: [text][ref] or [ref]
        def replace_ref_link(m: re.Match[str]) -> str:
            label_raw = m.group(1).strip()
            ref_key = (m.group(2).strip() or label_raw).lower()
            if ref_key not in self.ref_links:
                return m.group(0)
            url, title = self.ref_links[ref_key]
            label = self.render_inline(label_raw, base_style=p.link_text)
            title_suffix = f" · {title}" if title else ""
            styled = (
                f"{p.link_bracket}◄{RESET}{p.link_text}{label}{RESET}{p.link_bracket}►{RESET}"
                f"{p.link_bracket}─[{RESET}{p.link_url}{url}{title_suffix}{RESET}{p.link_bracket}]{RESET}"
            )
            return save_placeholder(styled)

        out = re.sub(r"\[([^\]]+)\]\[([^\]]*)\]", replace_ref_link, out)

        def replace_shortcut_ref_link(m: re.Match[str]) -> str:
            label_raw = m.group(1).strip()
            ref_key = label_raw.lower()
            if ref_key not in self.ref_links:
                return m.group(0)
            url, title = self.ref_links[ref_key]
            label = self.render_inline(label_raw, base_style=p.link_text)
            title_suffix = f" · {title}" if title else ""
            styled = (
                f"{p.link_bracket}◄{RESET}{p.link_text}{label}{RESET}{p.link_bracket}►{RESET}"
                f"{p.link_bracket}─[{RESET}{p.link_url}{url}{title_suffix}{RESET}{p.link_bracket}]{RESET}"
            )
            return save_placeholder(styled)

        out = re.sub(r"(?<!!)\[([^\^\]]+)\](?!\(|\[)", replace_shortcut_ref_link, out)

        # Autolinks: <https://...> or <user@host>
        out = re.sub(
            r"<((?:https?|ftp|mailto|telnet|bbs|gopher)://[^>]+)>",
            lambda m: save_placeholder(
                f"{p.link_bracket}◄{RESET}{p.link_text}{m.group(1)}{RESET}{p.link_bracket}►{RESET}"
            ),
            out,
        )
        out = re.sub(
            r"<([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})>",
            lambda m: save_placeholder(
                f"{p.link_bracket}◄{RESET}{p.link_text}{m.group(1)}{RESET}{p.link_bracket}►{RESET}"
            ),
            out,
        )

        # Bare URLs
        out = re.sub(
            r"(?<![\"'(<\[])(https?://[^\s<>)\]]+)",
            lambda m: save_placeholder(
                f"{p.link_bracket}◄{RESET}{p.link_text}{m.group(1)}{RESET}{p.link_bracket}►{RESET}"
            ),
            out,
        )

        # 9. Highlight / Mark: ==text==
        out = re.sub(
            r"==([^=\n]+?)==",
            lambda m: f"{p.highlight} {m.group(1)} {RESET}{b_style}",
            out,
        )

        # 10. Strikethrough: ~~text~~
        out = re.sub(
            r"~~([^~\n]+?)~~",
            lambda m: f"{p.strikethrough}{m.group(1)}{RESET}{b_style}",
            out,
        )

        # 11. Bold + Italic: ***text*** or ___text___
        out = re.sub(
            r"\*\*\*(?=\S)(.+?)(?<=\S)\*\*\*",
            lambda m: f"{p.bold_italic}{m.group(1)}{RESET}{b_style}",
            out,
        )
        out = re.sub(
            r"___(?=\S)(.+?)(?<=\S)___",
            lambda m: f"{p.bold_italic}{m.group(1)}{RESET}{b_style}",
            out,
        )

        # 12. Bold: **text** or __text__
        out = re.sub(
            r"\*\*(?=\S)(.+?)(?<=\S)\*\*",
            lambda m: f"{p.bold}{m.group(1)}{RESET}{b_style}",
            out,
        )
        out = re.sub(
            r"__(?=\S)(.+?)(?<=\S)__",
            lambda m: f"{p.bold}{m.group(1)}{RESET}{b_style}",
            out,
        )

        # 13. Italic: *text* or _text_
        out = re.sub(
            r"(?<!\*)\*(?=\S)([^\*\n]+?)(?<=\S)\*(?!\*)",
            lambda m: f"{p.italic}{m.group(1)}{RESET}{b_style}",
            out,
        )
        out = re.sub(
            r"(?<![A-Za-z0-9_])_(?=\S)([^_\n]+?)(?<=\S)_(?![A-Za-z0-9_])",
            lambda m: f"{p.italic}{m.group(1)}{RESET}{b_style}",
            out,
        )

        # 14. Superscript ^sup^ and Subscript ~sub~
        out = re.sub(
            r"\^([^\^\s]+)\^",
            lambda m: f"{p.sub_sup}{m.group(1).translate(SUPERSCRIPT_CHARS)}{RESET}{b_style}",
            out,
        )
        out = re.sub(
            r"(?<!~)~([^~\s]+)~(?!~)",
            lambda m: f"{p.sub_sup}{m.group(1).translate(SUBSCRIPT_CHARS)}{RESET}{b_style}",
            out,
        )

        # 15. Emoji shortcodes :name:
        def replace_emoji(m: re.Match[str]) -> str:
            code = m.group(1).lower()
            if code in EMOJI_MAP:
                return EMOJI_MAP[code]
            return m.group(0)

        out = re.sub(r":([a-z0-9_+-]+):", replace_emoji, out)

        # 16. Retro typographic arrows
        out = out.replace("<->", "◄─►").replace("->", "──►").replace("<-", "◄──")

        # Restore placeholders
        for idx in range(len(placeholders) - 1, -1, -1):
            out = out.replace(f"\x00PH{idx}PH\x00", placeholders[idx])

        return f"{b_style}{out}{RESET}"

    # --- Block Node Dispatch ---

    def _render_node(self, node: Node, width: int, list_depth: int = 0) -> str:
        if isinstance(node, Frontmatter):
            return self._render_frontmatter(node, width)
        if isinstance(node, Heading):
            return self._render_heading(node, width)
        if isinstance(node, Paragraph):
            return self._render_paragraph(node, width)
        if isinstance(node, ThematicBreak):
            return self._render_thematic_break(node, width)
        if isinstance(node, CodeBlock):
            return self._render_code_block(node, width)
        if isinstance(node, MathBlock):
            return self._render_math_block(node, width)
        if isinstance(node, BlockQuote):
            return self._render_blockquote(node, width)
        if isinstance(node, ListBlock):
            return self._render_list(node, width, depth=list_depth)
        if isinstance(node, DefinitionList):
            return self._render_definition_list(node, width)
        if isinstance(node, Table):
            return self._render_table(node, width)
        if isinstance(node, DetailsBlock):
            return self._render_details(node, width)
        if isinstance(node, HtmlBlock):
            return self._render_paragraph(Paragraph(text=node.raw), width)
        return ""

    # --- BBS Header & Footer ---

    def _render_bbs_banner(self) -> str:
        p = self.palette
        w = self.width
        inner = w - 2  # space inside ║ ... ║
        center_w = max(10, inner - 8)  # 4 chars left shade + 4 chars right shade
        top = f"{p.border_bright}╔{'═' * inner}╗{RESET}"
        status_l = " ☎ ATDT 555-0199 // CONNECT 2400 "
        status_r = f" MODE: {p.name.upper()} 80x25 "
        if len(status_l) + len(status_r) + 1 <= center_w:
            mid_pad = center_w - len(status_l) - len(status_r)
            center_text = status_l + (" " * mid_pad) + status_r
        else:
            center_text = truncate_ansi(status_l + " " + status_r, center_w)
        mid = (
            f"{p.border_bright}║{RESET}"
            f"{shade_bar(p)}"
            f"{p.h1_text}{pad_ansi(center_text, center_w, 'center')}{RESET}"
            f"{shade_bar(p, reverse=True)}"
            f"{p.border_bright}║{RESET}"
        )
        bot = f"{p.border_bright}╚{'═' * inner}╝{RESET}"
        return "\n".join([top, mid, bot])

    def _render_bbs_footer(self) -> str:
        p = self.palette
        w = self.width
        label = " ▀▄▀▄ [ EOF // CARRIER LOST // PRESS ANY KEY ] ▄▀▄▀ "
        bar_len = max(2, (w - len(label) - 8) // 2)
        return (
            f"{shade_bar(p)}"
            f"{p.border_dim}{'═' * bar_len}{RESET}"
            f"{p.border_bright}{label}{RESET}"
            f"{p.border_dim}{'═' * (w - 8 - bar_len - len(label))}{RESET}"
            f"{shade_bar(p, reverse=True)}"
        )

    # --- Frontmatter (FILE_ID.DIZ / NFO Box) ---

    def _render_frontmatter(self, node: Frontmatter, width: int) -> str:
        p = self.palette
        w = max(36, width - 2)
        inner = w - 4
        title = " ▀▄ FILE_ID.DIZ // SYSTEM METADATA ▄▀ "
        dash_total = max(2, w - 2 - len(title))
        left_d = dash_total // 2
        right_d = dash_total - left_d

        lines: List[str] = [
            f"{p.border_mid}╔{'═' * left_d}{p.h3_accent}{title}{p.border_mid}{'═' * right_d}╗{RESET}"
        ]
        max_key = max((len(k) for k, _ in node.entries), default=8)
        max_key = min(max_key, 20)

        for k, v in node.entries:
            key_str = f"{p.h3_text}{k.upper().ljust(max_key)}{RESET}"
            val_str = self.render_inline(v, base_style=p.body)
            prefix = f" {p.border_dim}▪{RESET} {key_str} {p.border_mid}:{RESET} "
            prefix_w = visible_len(prefix)
            val_avail = max(10, inner - prefix_w)
            val_trunc = truncate_ansi(val_str, val_avail)
            row_content = prefix + pad_ansi(val_trunc, val_avail)
            lines.append(
                f"{p.border_mid}║ {RESET}{row_content}{p.border_mid} ║{RESET}{p.shadow}░{RESET}"
            )

        lines.append(f"{p.border_mid}╚{'═' * (w - 2)}╝{RESET}{p.shadow}░{RESET}")
        lines.append(f" {p.shadow}{'░' * w}{RESET}")
        return "\n".join(lines)

    # --- Headings (H1 - H6) ---

    def _render_heading(self, node: Heading, width: int) -> str:
        p = self.palette
        lvl = node.level
        inline_title = self.render_inline(node.text, base_style="")
        plain_title = strip_ansi(inline_title)

        if lvl == 1:
            # H1: Full-width 80s BBS Double-Walled Banner with CP437 Shade Bars & Drop Shadow
            box_w = max(30, width - 2)
            inner_w = box_w - 2
            top = (
                f"{p.border_bright}╔══╦{'═' * max(1, inner_w - 6)}╦══╗{RESET}"
            )
            # Wrap title if needed
            title_upper = plain_title.upper()
            wing_l = shade_bar(p, reverse=False)
            wing_r = shade_bar(p, reverse=True)
            center_avail = max(10, inner_w - 10)
            wrapped_title = wrap_ansi(title_upper, center_avail)

            mid_lines: List[str] = []
            for tline in wrapped_title:
                padded_t = pad_ansi(f" {tline.strip()} ", center_avail, align="center")
                mid_lines.append(
                    f"{p.border_bright}║{RESET}{wing_l} "
                    f"{p.h1_text}{padded_t}{RESET}"
                    f" {wing_r}{p.border_bright}║{RESET}{p.shadow}▓▒{RESET}"
                )

            bot = (
                f"{p.border_bright}╚══╩{'═' * max(1, inner_w - 6)}╩══╝{RESET}{p.shadow}▓▒{RESET}"
            )
            shadow_line = f"  {p.shadow}{'▀' * (box_w - 2)}▒▒{RESET}"
            return "\n".join([top, *mid_lines, bot, shadow_line])

        if lvl == 2:
            # H2: Graduated CP437 Shade Bar + Double Line
            styled = self.render_inline(node.text.upper(), base_style=p.h2_text)
            prefix = f"{shade_bar(p)} {p.h2_accent}▐{RESET} {styled} {p.h2_accent}▌{RESET} {shade_bar(p, reverse=True)}"
            pref_len = visible_len(prefix)
            rem = max(3, width - pref_len - 2)
            line1 = f"{prefix} {p.border_mid}{'═' * (rem - 1)}╡{RESET}"
            line2 = f"{p.border_dim}{'─' * min(width, pref_len + 4)}{RESET}"
            return f"{line1}\n{line2}"

        if lvl == 3:
            # H3: Framed Cyber/BBS Sub-Banner
            styled = self.render_inline(node.text, base_style=p.h3_text)
            head = f"{p.border_bright}┌──[{RESET} {p.h3_accent}■{RESET} {styled} {p.border_bright}]{RESET}"
            rem = max(3, width - visible_len(head) - 1)
            return f"{head}{p.border_mid}{'─' * rem}┐{RESET}"

        if lvl == 4:
            styled = self.render_inline(node.text, base_style=p.h4_text)
            return f"{p.shade_2}▒▒{p.shade_3}▓{p.border_bright}▌{RESET} {p.h3_accent}◆{RESET} {styled} {p.border_bright}▐{p.shade_3}▓{p.shade_2}▒▒{RESET}"

        if lvl == 5:
            styled = self.render_inline(node.text, base_style=p.h5_text)
            return f"{p.shade_2}░░{p.border_bright}▌{RESET} {p.h5_text}►{RESET} {styled}"

        # H6
        styled = self.render_inline(node.text, base_style=p.h6_text)
        return f"{p.shadow}∙∙∙{RESET} {p.h6_text}» {styled} {p.h6_text}«{RESET} {p.shadow}∙∙∙{RESET}"

    # --- Paragraphs & Standalone Images ---

    def _render_paragraph(self, node: Paragraph, width: int) -> str:
        # Check if paragraph is a standalone image
        img_m = STANDALONE_IMG_RE.match(node.text.strip())
        if img_m:
            alt = img_m.group(1).strip() or "UNTITLED GRAPHIC"
            url = img_m.group(2).strip()
            title = (img_m.group(3) or "").strip()
            return self._render_image_frame(alt, url, title, width)

        styled = self.render_inline(node.text, base_style=self.palette.body)
        lines = wrap_ansi(styled, width=width, base_style=self.palette.body)
        return "\n".join(lines)

    def _render_image_frame(self, alt: str, url: str, title: str, width: int) -> str:
        """Render a standalone Markdown image as a classic 80s VGA/ANSI Art Viewer Frame."""
        p = self.palette
        w = min(width - 2, max(44, min(68, width - 2)))
        inner = w - 4
        header_label = " ▀▄▀▄ VGA / ANSI ART FRAME ▄▀▄▀ "
        dash_len = max(2, w - 2 - len(header_label))
        d_l = dash_len // 2
        d_r = dash_len - d_l

        art_bar = ("░▒▓█▀▄▀▄█▓▒░" * ((inner // 12) + 2))[:inner]
        alt_line = pad_ansi(f"{p.image_label}[ {alt.upper()} ]{RESET}", inner, "center")
        src_line = pad_ansi(truncate_ansi(f"{p.link_url}SRC: {url}{RESET}", inner), inner, "center")

        lines = [
            f"{p.image_border}╔{'═' * d_l}{p.image_label}{header_label}{p.image_border}{'═' * d_r}╗{RESET}",
            f"{p.image_border}║ {RESET}{p.shade_3}{art_bar}{RESET}{p.image_border} ║{RESET}{p.shadow}░{RESET}",
            f"{p.image_border}║ {RESET}{alt_line}{p.image_border} ║{RESET}{p.shadow}░{RESET}",
            f"{p.image_border}║ {RESET}{src_line}{p.image_border} ║{RESET}{p.shadow}░{RESET}",
        ]
        if title:
            title_line = pad_ansi(truncate_ansi(f"{p.italic}\"{title}\"{RESET}", inner), inner, "center")
            lines.append(
                f"{p.image_border}║ {RESET}{title_line}{p.image_border} ║{RESET}{p.shadow}░{RESET}"
            )
        lines.append(
            f"{p.image_border}║ {RESET}{p.shade_2}{art_bar}{RESET}{p.image_border} ║{RESET}{p.shadow}░{RESET}"
        )
        lines.append(f"{p.image_border}╚{'═' * (w - 2)}╝{RESET}{p.shadow}░{RESET}")
        lines.append(f" {p.shadow}{'░' * w}{RESET}")
        return "\n".join(lines)

    # --- Thematic Break (Horizontal Rule) ---

    def _render_thematic_break(self, node: ThematicBreak, width: int) -> str:
        p = self.palette
        center = f"{p.border_bright}◄══[{RESET} {p.h3_accent}❖{RESET} {p.border_bright}]══►{RESET}"
        center_w = visible_len(center)
        wings_w = 8  # 4 chars left shade + 4 chars right shade
        side_total = max(4, width - center_w - wings_w)
        left_w = side_total // 2
        right_w = side_total - left_w

        pattern_l = ("▀▄" * ((left_w // 2) + 2))[:left_w]
        pattern_r = ("▄▀" * ((right_w // 2) + 2))[:right_w]
        return (
            f"{shade_bar(p)}"
            f"{p.border_mid}{pattern_l}{RESET}"
            f"{center}"
            f"{p.border_mid}{pattern_r}{RESET}"
            f"{shade_bar(p, reverse=True)}"
        )

    # --- Code Block (80s Borland IDE / DOS Window) ---

    def _render_code_block(self, node: CodeBlock, width: int) -> str:
        p = self.palette
        w = max(36, width - 2)
        inner_w = w - 4

        lang_label = (node.language or "DOS/TEXT").upper()
        if node.meta:
            lang_label = f"{lang_label} · {node.meta}"
        title_chip = f" ▀▄ {lang_label} ▄▀ "
        win_controls = "[ ─ □ X ]"
        rem_dashes = max(2, w - 2 - len(title_chip) - len(win_controls) - 4)

        top = (
            f"{p.code_border}╔══{RESET}"
            f"{p.code_title}{title_chip}{RESET}"
            f"{p.code_border}{'═' * rem_dashes}{win_controls}══╗{RESET}"
        )

        raw_lines = node.code.split("\n") if node.code else [""]
        num_digits = max(3, len(str(len(raw_lines))))
        lineno_w = num_digits + 3  # e.g. "001 │ "
        code_avail = max(10, inner_w - lineno_w)

        body_lines: List[str] = []
        for idx, rline in enumerate(raw_lines, start=1):
            expanded = rline.expandtabs(4)
            # Wrap long code lines cleanly so the right border stays aligned
            chunks: List[str] = []
            if len(expanded) <= code_avail:
                chunks.append(expanded)
            else:
                for start in range(0, len(expanded), code_avail):
                    chunks.append(expanded[start : start + code_avail])

            for c_idx, chunk in enumerate(chunks):
                if c_idx == 0:
                    ln_str = f"{p.code_lineno}{str(idx).rjust(num_digits)} │ {RESET}"
                else:
                    ln_str = f"{p.code_lineno}{'↪'.rjust(num_digits)} │ {RESET}"
                hl = highlight_line(chunk, node.language, p)
                padded_hl = pad_ansi(hl, code_avail)
                body_lines.append(
                    f"{p.code_border}║ {RESET}{ln_str}{padded_hl}{p.code_border} ║{RESET}{p.shadow}▒{RESET}"
                )

        bot = f"{p.code_border}╚{'═' * (w - 2)}╝{RESET}{p.shadow}▒{RESET}"
        shadow = f" {p.shadow}{'▒' * w}{RESET}"
        return "\n".join([top, *body_lines, bot, shadow])

    # --- Math Block (8087 FPU Formula Window) ---

    def _render_math_block(self, node: MathBlock, width: int) -> str:
        p = self.palette
        w = max(36, width - 2)
        inner = w - 4
        header = " ∑ INTEL 8087 FPU // MATH PROCESSOR "
        rem = max(2, w - 2 - len(header))
        dl = rem // 2
        dr = rem - dl

        lines = [
            f"{p.border_mid}╔{'═' * dl}{p.sub_sup}{header}{p.border_mid}{'═' * dr}╗{RESET}"
        ]
        for raw_line in node.formula.split("\n"):
            formatted = format_math(raw_line.strip())
            for wline in wrap_ansi(formatted, inner, base_style=p.sub_sup):
                centered = pad_ansi(wline, inner, align="center")
                lines.append(
                    f"{p.border_mid}║ {RESET}{centered}{p.border_mid} ║{RESET}{p.shadow}░{RESET}"
                )
        lines.append(f"{p.border_mid}╚{'═' * (w - 2)}╝{RESET}{p.shadow}░{RESET}")
        lines.append(f" {p.shadow}{'░' * w}{RESET}")
        return "\n".join(lines)

    # --- Blockquotes & GitHub Alerts ---

    def _render_blockquote(self, node: BlockQuote, width: int) -> str:
        p = self.palette
        if node.alert_type:
            return self._render_alert(node, width)

        gutter = f"{p.shade_2}▒{p.shade_3}▓{p.quote_bar}║{RESET} "
        gutter_w = visible_len(gutter)
        inner_w = max(20, width - gutter_w)

        rendered_children: List[str] = []
        for child in node.children:
            if isinstance(child, Paragraph):
                styled = self.render_inline(child.text, base_style=p.quote_text)
                wrapped = wrap_ansi(styled, width=inner_w, base_style=p.quote_text)
                rendered_children.append("\n".join(wrapped))
            else:
                rendered_children.append(self._render_node(child, width=inner_w))

        combined = "\n\n".join(c for c in rendered_children if c)
        out_lines = [f"{gutter}{line}" for line in combined.split("\n")]
        return "\n".join(out_lines)

    def _render_alert(self, node: BlockQuote, width: int) -> str:
        p = self.palette
        atype = (node.alert_type or "NOTE").upper()
        alert_configs = {
            "NOTE": (p.note_color, "[i]", "SYSOP NOTE"),
            "INFO": (p.note_color, "[i]", "SYSTEM INFO"),
            "TIP": (p.tip_color, "[★]", "PRO-TIP // CHEAT CODE"),
            "SUCCESS": (p.tip_color, "[✔]", "OPERATION SUCCESS"),
            "IMPORTANT": (p.important_color, "[!]", "PRIORITY TRANSMISSION"),
            "WARNING": (p.warning_color, "[▲]", "SYSTEM WARNING"),
            "CAUTION": (p.caution_color, "[✖]", "CRITICAL HAZARD"),
            "DANGER": (p.caution_color, "[✖]", "CRITICAL DANGER"),
            "BUG": (p.caution_color, "[🐞]", "KNOWN SYSTEM BUG"),
        }
        color, icon, default_label = alert_configs.get(
            atype, (p.note_color, "[!]", atype)
        )
        label = node.alert_title if node.alert_title else default_label

        w = max(36, width - 2)
        inner = w - 4
        head_text = f" ░▒▓█ {icon} {label.upper()} █▓▒░ "
        rem = max(2, w - 2 - len(head_text))

        lines = [
            f"{color}╔══{head_text}{'═' * max(0, rem - 2)}╗{RESET}"
        ]

        rendered_children: List[str] = []
        for child in node.children:
            rendered_children.append(self._render_node(child, width=inner))

        body = "\n\n".join(c for c in rendered_children if c)
        for bline in body.split("\n"):
            padded = pad_ansi(bline, inner)
            lines.append(f"{color}║ {RESET}{padded}{color} ║{RESET}{p.shadow}░{RESET}")

        lines.append(f"{color}╚{'═' * (w - 2)}╝{RESET}{p.shadow}░{RESET}")
        lines.append(f" {p.shadow}{'░' * w}{RESET}")
        return "\n".join(lines)

    # --- Lists (Ordered, Unordered, Task Lists, Nested) ---

    def _render_list(self, node: ListBlock, width: int, depth: int = 0) -> str:
        p = self.palette
        bullets = [
            f"{p.list_bullet_1}■{RESET}",
            f"{p.list_bullet_2}◆{RESET}",
            f"{p.list_bullet_3}►{RESET}",
            f"{p.border_mid}∙{RESET}",
        ]
        out_lines: List[str] = []
        indent_str = "   " * depth

        for idx, item in enumerate(node.items):
            if item.checked is not None:
                if item.checked:
                    marker = f"{p.task_done}[✔]{RESET}"
                    item_base = p.body
                else:
                    marker = f"{p.task_todo}[░]{RESET}"
                    item_base = p.body
            elif node.ordered:
                num = node.start + idx
                if depth == 0:
                    marker = f"{p.link_bracket}[{RESET}{p.list_number}{num:02d}{RESET}{p.link_bracket}]{RESET}"
                else:
                    marker = f"{p.list_number}{num}.{RESET}"
                item_base = p.body
            else:
                marker = bullets[min(depth, len(bullets) - 1)]
                item_base = p.body

            first_prefix = f"{indent_str}{marker} "
            sub_prefix = f"{indent_str}{' ' * visible_len(marker)} "

            if item.text:
                styled_text = self.render_inline(item.text, base_style=item_base)
                wrapped = wrap_ansi(
                    styled_text,
                    width=width,
                    initial_indent=first_prefix,
                    subsequent_indent=sub_prefix,
                    base_style=item_base,
                )
                out_lines.extend(wrapped)
            else:
                out_lines.append(first_prefix.rstrip())

            for child in item.children:
                if isinstance(child, ListBlock):
                    out_lines.append(self._render_list(child, width=width, depth=depth + 1))
                else:
                    child_rendered = self._render_node(
                        child, width=max(20, width - visible_len(sub_prefix)), list_depth=depth + 1
                    )
                    for cline in child_rendered.split("\n"):
                        out_lines.append(f"{sub_prefix}{cline}")

        return "\n".join(out_lines)

    # --- Definition Lists ---

    def _render_definition_list(self, node: DefinitionList, width: int) -> str:
        p = self.palette
        lines: List[str] = []
        for idx, item in enumerate(node.items):
            if idx > 0:
                lines.append("")
            term_styled = self.render_inline(item.term, base_style=p.bold)
            lines.append(f"{p.border_bright}▐►{RESET} {term_styled}")
            for d in item.definitions:
                def_styled = self.render_inline(d, base_style=p.body)
                wrapped = wrap_ansi(
                    def_styled,
                    width=width,
                    initial_indent=f"  {p.border_mid}└──►{RESET} ",
                    subsequent_indent="       ",
                    base_style=p.body,
                )
                lines.extend(wrapped)
        return "\n".join(lines)

    # --- Tables (GFM Pipe Tables with CP437 Double/Single Grid) ---

    def _render_table(self, node: Table, width: int) -> str:
        p = self.palette
        num_cols = len(node.headers)
        if num_cols == 0:
            return ""

        # Render inline formatting for headers and all cells
        rendered_headers = [
            self.render_inline(h, base_style=p.table_header_text) for h in node.headers
        ]
        rendered_rows: List[List[str]] = []
        for r_idx, row in enumerate(node.rows):
            row_style = p.table_row_even if r_idx % 2 == 0 else p.table_row_odd
            rendered_rows.append(
                [self.render_inline(cell, base_style=row_style) for cell in row]
            )

        # Compute natural width of each column
        col_widths: List[int] = []
        for c in range(num_cols):
            max_w = max(3, visible_len(rendered_headers[c]))
            for r in rendered_rows:
                if c < len(r):
                    max_w = max(max_w, visible_len(r[c]))
            col_widths.append(max_w)

        # Total width with borders: 1 (left) + sum(col_w + 2 padding) + (num_cols - 1) separators + 1 (right) + 1 (shadow)
        overhead = 2 + (3 * num_cols - 1) + 1
        avail_for_cols = max(num_cols * 4, width - overhead)

        if sum(col_widths) > avail_for_cols:
            # Proportionally shrink wider columns while preserving small columns
            min_col = 4
            while sum(col_widths) > avail_for_cols and max(col_widths) > min_col:
                widest_idx = col_widths.index(max(col_widths))
                col_widths[widest_idx] -= 1

        def hline(left: str, mid: str, right: str, fill: str) -> str:
            segs = [fill * (cw + 2) for cw in col_widths]
            return f"{p.table_border}{left}{mid.join(segs)}{right}{RESET}"

        lines: List[str] = [hline("╔", "╤", "╗", "═")]

        # Render header row (with wrapping if needed)
        header_wrapped = [
            wrap_ansi(rendered_headers[c], col_widths[c], base_style=p.table_header_text)
            for c in range(num_cols)
        ]
        max_h_lines = max(len(hw) for hw in header_wrapped)
        for l_idx in range(max_h_lines):
            cells_str: List[str] = []
            for c in range(num_cols):
                cell_line = header_wrapped[c][l_idx] if l_idx < len(header_wrapped[c]) else ""
                align = node.alignments[c] if c < len(node.alignments) else "left"
                padded = pad_ansi(cell_line, col_widths[c], align=align)
                cells_str.append(f"{p.table_header_text} {padded} {RESET}")
            sep = f"{p.table_border}│{RESET}"
            lines.append(
                f"{p.table_border}║{RESET}{sep.join(cells_str)}{p.table_border}║{RESET}{p.shadow}░{RESET}"
            )

        lines.append(hline("╠", "╪", "╣", "═") + f"{p.shadow}░{RESET}")

        # Render data rows
        for r_idx, r_cells in enumerate(rendered_rows):
            row_style = p.table_row_even if r_idx % 2 == 0 else p.table_row_odd
            row_wrapped = [
                wrap_ansi(r_cells[c] if c < len(r_cells) else "", col_widths[c], base_style=row_style)
                for c in range(num_cols)
            ]
            max_r_lines = max(len(rw) for rw in row_wrapped)
            for l_idx in range(max_r_lines):
                cells_str = []
                for c in range(num_cols):
                    cell_line = row_wrapped[c][l_idx] if l_idx < len(row_wrapped[c]) else ""
                    align = node.alignments[c] if c < len(node.alignments) else "left"
                    padded = pad_ansi(cell_line, col_widths[c], align=align)
                    cells_str.append(f" {row_style}{padded}{RESET} ")
                sep = f"{p.table_border}│{RESET}"
                lines.append(
                    f"{p.table_border}║{RESET}{sep.join(cells_str)}{p.table_border}║{RESET}{p.shadow}░{RESET}"
                )
            if r_idx + 1 < len(rendered_rows):
                lines.append(hline("╟", "┼", "╢", "─") + f"{p.shadow}░{RESET}")

        lines.append(hline("╚", "╧", "╝", "═") + f"{p.shadow}░{RESET}")
        total_box_w = sum(col_widths) + 3 * num_cols + 1
        lines.append(f" {p.shadow}{'░' * total_box_w}{RESET}")
        return "\n".join(lines)

    # --- Details / Summary Accordion Block ---

    def _render_details(self, node: DetailsBlock, width: int) -> str:
        p = self.palette
        w = max(36, width - 2)
        inner = w - 4
        summary_plain = strip_ansi(self.render_inline(node.summary))
        title = f" ▼ EXPANDED RECORD: {summary_plain} "
        rem = max(2, w - 2 - len(title))

        lines = [
            f"{p.border_mid}╔══{p.h3_accent}{title}{p.border_mid}{'═' * max(0, rem - 2)}╗{RESET}"
        ]
        rendered_children = [self._render_node(c, width=inner) for c in node.children]
        body = "\n\n".join(c for c in rendered_children if c)
        for bline in body.split("\n"):
            padded = pad_ansi(bline, inner)
            lines.append(f"{p.border_mid}║ {RESET}{padded}{p.border_mid} ║{RESET}{p.shadow}░{RESET}")
        lines.append(f"{p.border_mid}╚{'═' * (w - 2)}╝{RESET}{p.shadow}░{RESET}")
        return "\n".join(lines)

    # --- Footnotes Section ---

    def _render_footnotes(self, footnotes: Dict[str, str], width: int) -> str:
        p = self.palette
        w = max(36, width - 2)
        inner = w - 4
        title = " ▀▄ FOOTNOTES & REFERENCES ▄▀ "
        rem = max(2, w - 2 - len(title))
        dl = rem // 2
        dr = rem - dl

        lines = [
            f"{p.border_dim}╔{'═' * dl}{p.footnote}{title}{p.border_dim}{'═' * dr}╗{RESET}"
        ]
        for fn_id, fn_text in footnotes.items():
            prefix = f"{p.link_bracket}[{RESET}{p.footnote}#{fn_id}{RESET}{p.link_bracket}]{RESET} "
            styled = self.render_inline(fn_text, base_style=p.body)
            wrapped = wrap_ansi(
                styled,
                width=inner,
                initial_indent=prefix,
                subsequent_indent=" " * visible_len(prefix),
                base_style=p.body,
            )
            for wline in wrapped:
                padded = pad_ansi(wline, inner)
                lines.append(f"{p.border_dim}║ {RESET}{padded}{p.border_dim} ║{RESET}")
        lines.append(f"{p.border_dim}╚{'═' * (w - 2)}╝{RESET}")
        return "\n".join(lines)
