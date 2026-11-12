"""Command-line interface for md2ans (80s BBS / DOS ANSI Art Markdown Renderer)."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .ansi import PALETTES
from .parser import parse_markdown
from .renderer import AnsiRenderer


def render_markdown(
    text: str,
    width: int = 80,
    palette: str = "bbs",
    show_header: bool = False,
    plain: bool = False,
) -> str:
    """Parse and render a Markdown string to 80s BBS ANSI Art."""
    doc = parse_markdown(text)
    renderer = AnsiRenderer(
        width=width,
        palette_name=palette,
        show_header=show_header,
        plain=plain,
    )
    return renderer.render(doc)


def _resolve_width(width_arg: str) -> int:
    if width_arg.lower() == "auto":
        cols = shutil.get_terminal_size(fallback=(80, 25)).columns
        return max(40, min(cols, 140))
    try:
        return max(40, int(width_arg))
    except ValueError:
        return 80


def build_arg_parser() -> argparse.ArgumentParser:
    palette_help = ", ".join(
        f"{k} ({v.description})" for k, v in PALETTES.items()
    )
    parser = argparse.ArgumentParser(
        prog="md2ans",
        description="Classic 80s BBS / DOS ANSI Art Markdown Viewer & Renderer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  md2ans README.md                  Render README.md in 80-col BBS ANSI style\n"
            "  md2ans --header README.md         Include retro 2400-baud BBS modem banner\n"
            "  md2ans -p cga1 README.md          Use IBM CGA Palette 1 (Cyan/Magenta/White)\n"
            "  md2ans -p phosphor README.md      Use Green CRT Phosphor monitor palette\n"
            "  md2ans --demo                     Display built-in 80s BBS Markdown showcase\n"
            "  cat doc.md | md2ans -w auto       Pipe Markdown and auto-fit terminal width\n"
        ),
    )
    parser.add_argument(
        "files",
         nargs="*",
        help="Markdown file(s) to render. Reads from stdin if omitted or '-'.",
    )
    parser.add_argument(
        "-w",
        "--width",
        default="80",
        help="Output column width (integer >= 40, or 'auto' for terminal width; default: 80).",
    )
    parser.add_argument(
        "-p",
        "--palette",
        choices=list(PALETTES.keys()),
        default="bbs",
        help=f"80s color palette: {palette_help} (default: bbs).",
    )
    parser.add_argument(
        "-b",
        "--header",
        action="store_true",
        help="Show classic 2400-baud BBS connection header and EOF carrier footer.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Render the built-in 80s BBS showcase document demonstrating all Markdown tags.",
    )
    parser.add_argument(
        "--no-color",
        "--plain",
        dest="plain",
        action="store_true",
        help="Strip ANSI color codes while keeping CP437 box/block art.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"md2ans {__version__}",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    width = _resolve_width(str(args.width))
    plain = bool(args.plain or os.environ.get("NO_COLOR"))

    if args.demo:
        demo_path = Path(__file__).with_name("demo.md")
        content = demo_path.read_text(encoding="utf-8")
        sys.stdout.write(
            render_markdown(
                content,
                width=width,
                palette=args.palette,
                show_header=True,
                plain=plain,
            )
        )
        return 0

    if not args.files:
        if sys.stdin.isatty():
            parser.print_help(sys.stderr)
            return 1
        content = sys.stdin.read()
        sys.stdout.write(
            render_markdown(
                content,
                width=width,
                palette=args.palette,
                show_header=args.header,
                plain=plain,
            )
        )
        return 0

    exit_code = 0
    for idx, file_arg in enumerate(args.files):
        if file_arg == "-":
            content = sys.stdin.read()
        else:
            path = Path(file_arg)
            if not path.is_file():
                sys.stderr.write(f"md2ans: error: file not found: {file_arg}\n")
                exit_code = 1
                continue
            content = path.read_text(encoding="utf-8")

        if idx > 0:
            sys.stdout.write("\n")
        sys.stdout.write(
            render_markdown(
                content,
                width=width,
                palette=args.palette,
                show_header=args.header,
                plain=plain,
            )
        )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
