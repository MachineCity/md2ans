"""Unit and integration tests for md2ans."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from md2ans.ansi import PALETTES, pad_ansi, strip_ansi, truncate_ansi, visible_len, wrap_ansi
from md2ans.cli import main, render_markdown
from md2ans.parser import (
    BlockQuote,
    CodeBlock,
    DefinitionList,
    DetailsBlock,
    Frontmatter,
    Heading,
    ListBlock,
    MathBlock,
    Paragraph,
    Table,
    ThematicBreak,
    parse_markdown,
)


class TestAnsiHelpers(unittest.TestCase):
    def test_visible_len_and_strip(self) -> None:
        s = "\x1b[1;93mHELLO\x1b[0m \x1b[36mWORLD\x1b[0m"
        self.assertEqual(strip_ansi(s), "HELLO WORLD")
        self.assertEqual(visible_len(s), 11)

    def test_pad_and_truncate(self) -> None:
        s = "\x1b[1;96mBBS\x1b[0m"
        padded = pad_ansi(s, 7, align="center")
        self.assertEqual(visible_len(padded), 7)
        self.assertEqual(strip_ansi(padded), "  BBS  ")

        trunc = truncate_ansi("\x1b[1;93m1234567890\x1b[0m", 6)
        self.assertLessEqual(visible_len(trunc), 6)

    def test_wrap_ansi_preserves_width(self) -> None:
        text = "\x1b[1;93mThis is a long line of styled text that should wrap cleanly across multiple lines.\x1b[0m"
        lines = wrap_ansi(text, width=25)
        self.assertGreater(len(lines), 2)
        for line in lines:
            self.assertLessEqual(visible_len(line), 25)


class TestMarkdownParserAndRenderer(unittest.TestCase):
    def test_all_block_types_parsed_and_rendered(self) -> None:
        sample = """---
title: "TEST DOC"
system: "MS-DOS 3.30"
---

# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6

Setext H1
=========

Setext H2
---------

Paragraph with **bold**, *italic*, ***bold-italic***, ~~strike~~, ==highlight==, `inline_code`, <kbd>F1</kbd>, E=mc^2^, H~2~O, $x_1 + \\pi$, :floppy_disk:, [Link](https://example.com "Title"), [RefLink][ref1], and footnote[^fn1].

---

> Standard blockquote line 1
> Line 2

> [!WARNING]
> Hardware interrupt conflict on IRQ 7!

- Unordered 1
  - Nested 1.1
    - Deep 1.1.1
- [x] Completed task
- [ ] Pending task

1. First ordered
2. Second ordered

```python
def hello(name: str) -> None:
    print(f"Hello {name}")
```

| Adapter | Mode | Colors |
| :--- | :---: | ---: |
| CGA | 04h | 4 |
| VGA | 13h | 256 |

Term 1
: Definition 1

$$
\\sum_{i=1}^{n} x_i = \\infty
$$

![VGA Banner](https://example.com/vga.ans "ANSI Art")

<details>
<summary>Archive Log</summary>

Hidden body text inside details.
</details>

[ref1]: https://bbs.example.org "BBS Archive"
[^fn1]: Footnote explanation text.
"""
        doc = parse_markdown(sample)
        node_types = {type(n) for n in doc.nodes}
        self.assertIn(Frontmatter, node_types)
        self.assertIn(Heading, node_types)
        self.assertIn(Paragraph, node_types)
        self.assertIn(ThematicBreak, node_types)
        self.assertIn(BlockQuote, node_types)
        self.assertIn(ListBlock, node_types)
        self.assertIn(CodeBlock, node_types)
        self.assertIn(Table, node_types)
        self.assertIn(DefinitionList, node_types)
        self.assertIn(MathBlock, node_types)
        self.assertIn(DetailsBlock, node_types)
        self.assertIn("fn1", doc.footnotes)
        self.assertIn("ref1", doc.ref_links)

        # Render across all palettes
        for pal_name in PALETTES:
            rendered = render_markdown(sample, width=80, palette=pal_name, show_header=True)
            self.assertIn("\x1b[", rendered)
            plain = strip_ansi(rendered)
            self.assertIn("FILE_ID.DIZ", plain)
            self.assertIn("HEADING 1", plain)
            self.assertIn("SYSTEM WARNING", plain)
            self.assertIn("Hardware interrupt conflict on IRQ 7!", plain)
            self.assertIn("FOOTNOTES & REFERENCES", plain)
            self.assertIn("VGA / ANSI ART FRAME", plain)
            self.assertIn("EXPANDED RECORD: Archive Log", plain)
            for line in rendered.splitlines():
                self.assertLessEqual(visible_len(line), 80, f"Line exceeded width 80: {strip_ansi(line)!r}")

    def test_cli_demo_and_plain_mode(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["--demo", "--plain", "-w", "80"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertNotIn("\x1b[", out)
        self.assertIn("MD2ANS // 80S BBS MARKDOWN VIEWER", out)
        self.assertIn("╔", out)
        self.assertIn("░▒▓█", out)


if __name__ == "__main__":
    unittest.main()
