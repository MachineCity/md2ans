"""80s Borland / Norton Commander style CGA/EGA syntax highlighter for code blocks."""

from __future__ import annotations

import re
from .ansi import Palette, RESET

# Common keywords across languages, plus 80s classics (BASIC, Pascal, ASM, C)
KEYWORDS = {
    # Python / JS / General
    "def", "class", "return", "if", "elif", "else", "for", "while", "break",
    "continue", "pass", "import", "from", "as", "try", "except", "finally",
    "raise", "with", "yield", "lambda", "async", "await", "assert", "del",
    "global", "nonlocal", "in", "is", "not", "and", "or",
    "function", "const", "let", "var", "new", "this", "super", "extends",
    "implements", "interface", "type", "enum", "export", "default", "switch",
    "case", "throw", "catch", "typeof", "instanceof", "void", "delete",
    # C / Rust / Go / Java
    "struct", "union", "typedef", "static", "extern", "register", "volatile",
    "sizeof", "goto", "do", "pub", "fn", "mut", "impl", "trait", "where",
    "match", "use", "mod", "crate", "move", "ref", "unsafe", "loop",
    "package", "func", "defer", "go", "chan", "select", "fallthrough",
    "public", "private", "protected", "final", "abstract", "synchronized",
    # SQL
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
    "DELETE", "CREATE", "TABLE", "DROP", "ALTER", "JOIN", "INNER", "LEFT",
    "RIGHT", "ON", "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "AS", "AND",
    "OR", "NOT", "NULL", "PRIMARY", "KEY",
    # 80s Classics: BASIC, Pascal, Assembly
    "PRINT", "INPUT", "LET", "GOTO", "GOSUB", "RETURN", "IF", "THEN", "ELSE",
    "FOR", "TO", "STEP", "NEXT", "REM", "DIM", "POKE", "PEEK", "SYS", "RUN",
    "END", "STOP", "DATA", "READ", "RESTORE", "CLS", "LOCATE", "COLOR",
    "BEEP", "SOUND", "PLAY", "SCREEN", "PSET", "LINE", "CIRCLE",
    "PROGRAM", "BEGIN", "PROCEDURE", "FUNCTION", "VAR", "CONST", "TYPE",
    "ARRAY", "RECORD", "OF", "REPEAT", "UNTIL", "WRITELN", "READLN", "USES",
    "MOV", "PUSH", "POP", "LEA", "ADD", "SUB", "INC", "DEC", "CMP", "JMP",
    "JE", "JNE", "JG", "JL", "CALL", "RET", "INT", "NOP", "XOR", "SHL", "SHR",
    # Shell
    "echo", "export", "local", "readonly", "fi", "then", "done", "esac",
}

TYPES_AND_CONSTANTS = {
    "True", "False", "None", "true", "false", "null", "undefined", "NaN",
    "Infinity", "self", "cls",
    "int", "float", "double", "char", "void", "bool", "string", "str", "bytes",
    "list", "dict", "set", "tuple", "u8", "u16", "u32", "u64", "usize",
    "i8", "i16", "i32", "i64", "isize", "f32", "f64", "Option", "Result",
    "Some", "Ok", "Err", "String", "Vec", "Box", "INTEGER", "TEXT", "VARCHAR",
    "BOOLEAN", "AX", "BX", "CX", "DX", "SI", "DI", "BP", "SP", "CS", "DS",
    "ES", "SS", "AL", "AH", "BL", "BH", "CL", "CH", "DL", "DH",
}

BUILTINS = {
    "print", "len", "range", "open", "map", "filter", "zip", "enumerate",
    "isinstance", "getattr", "setattr", "hasattr", "super", "min", "max",
    "sum", "sorted", "reversed", "any", "all", "abs", "round", "console",
    "log", "require", "Math", "JSON", "Object", "Array", "Promise",
    "printf", "scanf", "malloc", "free", "memcpy", "strlen", "println",
    "format", "vec", "panic",
}

TOKEN_RE = re.compile(
    r"(?P<comment>#.*$|//.*$|--.*$|;.*$|^\s*REM\b.*$|\(\*.*?\*\)|/\*.*?\*/)"
    r"|(?P<string>\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)"
    r"|(?P<decorator>@[A-Za-z_][A-Za-z0-9_.]*|^\s*#[a-zA-Z_]+)"
    r"|(?P<tag></?[A-Za-z][A-Za-z0-9_-]*|/?>)"
    r"|(?P<func>\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\())"
    r"|(?P<ident>\b[A-Za-z_][A-Za-z0-9_]*\$?\b)"
    r"|(?P<number>\b(?:0[xX][0-9a-fA-F]+|0[bB][01]+|\$[0-9a-fA-F]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[hH]?)\b)"
    r"|(?P<operator>[+\-*/%=<>!&|^~?:]+)",
    re.MULTILINE,
)


def highlight_line(line: str, lang: str, palette: Palette) -> str:
    """Highlight a single line of source code with 80s EGA/Borland colors."""
    if not line:
        return ""

    lang_lower = (lang or "").strip().lower()
    if lang_lower in ("text", "txt", "plain", "ascii", "ansi"):
        return f"{palette.body}{line}{RESET}"

    out: list[str] = []
    pos = 0

    for match in TOKEN_RE.finditer(line):
        start, end = match.span()
        if start > pos:
            out.append(f"{palette.body}{line[pos:start]}{RESET}")

        tok = match.group(0)
        kind = match.lastgroup

        if kind == "comment":
            out.append(f"{palette.syn_comment}{tok}{RESET}")
        elif kind == "string":
            out.append(f"{palette.syn_string}{tok}{RESET}")
        elif kind == "decorator":
            out.append(f"{palette.syn_type}{tok}{RESET}")
        elif kind == "tag":
            out.append(f"{palette.syn_keyword}{tok}{RESET}")
        elif kind == "number":
            out.append(f"{palette.syn_number}{tok}{RESET}")
        elif kind == "func":
            if tok in KEYWORDS or tok.upper() in KEYWORDS:
                out.append(f"{palette.syn_keyword}{tok}{RESET}")
            elif tok in BUILTINS:
                out.append(f"{palette.syn_builtin}{tok}{RESET}")
            else:
                out.append(f"{palette.syn_func}{tok}{RESET}")
        elif kind == "ident":
            if tok in KEYWORDS or (lang_lower in ("sql", "basic", "bas", "asm", "pascal", "pas") and tok.upper() in KEYWORDS):
                out.append(f"{palette.syn_keyword}{tok}{RESET}")
            elif tok in TYPES_AND_CONSTANTS:
                out.append(f"{palette.syn_type}{tok}{RESET}")
            elif tok in BUILTINS:
                out.append(f"{palette.syn_builtin}{tok}{RESET}")
            else:
                out.append(f"{palette.body}{tok}{RESET}")
        elif kind == "operator":
            out.append(f"{palette.syn_operator}{tok}{RESET}")
        else:
            out.append(f"{palette.body}{tok}{RESET}")

        pos = end

    if pos < len(line):
        out.append(f"{palette.body}{line[pos:]}{RESET}")

    return "".join(out)
