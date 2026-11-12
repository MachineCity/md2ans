# MD2ANS // 80s BBS & DOS ANSI Art Markdown Viewer

**`md2ans`** is a dependency-free Python CLI Markdown viewer and ANSI renderer with an authentic **1980s BBS / DOS ANSI Art / Warez NFO** vibe. It transforms standard and extended Markdown files into 16-color **CGA/EGA ANSI art** complete with **CP437 block shading (`░▒▓█`)**, **double-line boxes (`╔═╗`)**, drop shadows, and Borland-style syntax highlighting.

---

## Features & Supported Markdown Tags

- **YAML Frontmatter (`---`)**: Rendered as a classic `FILE_ID.DIZ // SYSTEM METADATA` double-walled dossier with drop shadows.
- **Headings (`# H1` – `###### H6` & Setext `===`/`---`)**:
  - `H1`: Full-width double-walled BBS banner with `░▒▓█` CP437 shading wings, Royal Blue bar, and drop shadow (`▀▀▀`).
  - `H2`: Graduated CP437 shade bars (`░▒▓█ ▐ TITLE ▌ █▓▒░═══╡`) + underline rule.
  - `H3`–`H6`: Distinct bracketed, shaded, and diamond-marked retro sub-headers.
- **Inline Formatting**:
  - **Bold** (`**bold**`, `__bold__`), *Italic* (`*italic*`, `_italic_`), ***Bold+Italic*** (`***both***`)
  - ~~Strikethrough~~ (`~~del~~`, `<del>`), ==Highlight== (`==mark==`, `<mark>`), <u>Underline</u> (`<u>`, `<ins>`)
  - Inline code chips (`` `code` `` -> `▐ code ▌` in phosphor green on black)
  - 3D DOS Keycaps (`<kbd>Ctrl</kbd>`) -> `▐[Ctrl]▌`
  - Superscript (`^2^`, `<sup>`), Subscript (`~2~`, `<sub>`), and Inline Math (`$f(x) = \pi r^2$`)
  - Links (`[label](url "title")`, reference links `[label][id]`, `<https://...>`, bare URLs) styled as hypertext BBS dial-up nodes: `◄label►─[url]`
  - Emoji shortcodes (`:floppy_disk:`, `:computer:`, `:joystick:`, `:space_invader:`, `:zap:`, `:rocket:`, etc.)
- **Fenced & Indented Code Blocks**:
  - Rendered as a **Borland Turbo Pascal / DOS IDE Window** (`╔══[ ▀▄ PYTHON ▄▀ ]════[ ─ □ X ]══╗`) with line numbers, drop shadows, and built-in **CGA/EGA syntax highlighting** (Python, JS/TS, C/C++/Rust/Go, SQL, Bash, BASIC, Pascal, Assembly).
- **Blockquotes & GitHub Alerts**:
  - Standard quotes (`>`) with `▒▓║` shaded BBS quote bars.
  - System Alert Dialog Boxes for `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`.
- **GFM Pipe Tables**:
  - Full CP437 double/single-line data grid (`╔═╤═╗`, `╠═╪═╣`, `╟─┼─╢`, `╚═╧═╝`) with left/center/right column alignment, automatic multi-line cell wrapping, alternating row contrast, and drop shadows.
- **Lists & Task Lists**:
  - Unordered lists (`■`, `◆`, `►`, `∙`), Ordered lists (`[01]`, `[02]`), Task lists (`[✔]` / `[░]`), and nested hierarchies.
- **Extended Blocks**:
  - Standalone Images (`![alt](url "title")`) rendered as an **80s VGA / ANSI Art Frame**
  - Display Math Blocks (`$$ ... $$`) rendered in an **Intel 8087 FPU Math Processor** frame
  - Definition Lists (`Term \n : Definition`)
  - Collapsible `<details><summary>...</summary>...</details>` archive records
  - Footnotes (`[^1]` and `[^1]: definition`) collected in a bottom reference box
  - Horizontal Rules (`---`, `***`, `___`) with CP437 `░▒▓█▀▄` ornaments

---

## Quick Start

```bash
# Run the built-in 80s BBS showcase demo
python3 -m md2ans --demo

# Render any Markdown file to stdout
python3 -m md2ans README.md

# Include the 2400-baud modem connection banner and EOF carrier footer
python3 -m md2ans --header README.md

# Switch between 80s hardware palettes (bbs, cga1, cga0, phosphor, amber)
python3 -m md2ans -p cga1 README.md
python3 -m md2ans -p phosphor README.md
python3 -m md2ans -p amber README.md

# Pipe into less -R for paging
python3 -m md2ans --header README.md | less -R
```
