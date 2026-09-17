from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from opencc import OpenCC
except ImportError:
    print("找不到 opencc-python-reimplemented；請先安裝相依套件。", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
CONVERTER = OpenCC("s2twp")

# Markdown 語法中不應參與語言檢查的區域。
FENCED_BLOCK_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
URL_RE = re.compile(r"https?://[^\s)]+")
HTML_TAG_RE = re.compile(r"<[^>]+>")


def visible_text(line: str, in_fence: bool) -> tuple[str, bool]:
    stripped = line.lstrip()
    if stripped.startswith("```") or stripped.startswith("~~~"):
        return "", not in_fence
    if in_fence:
        return "", True

    text = INLINE_CODE_RE.sub("", line)
    text = URL_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    return text, False


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{path}: 不是 UTF-8 編碼"]

    lines = content.splitlines()
    h1_count = 0
    previous_level = 0
    in_fence = False

    for number, line in enumerate(lines, start=1):
        text, fence_changed = visible_text(line, in_fence)
        if fence_changed:
            in_fence = not in_fence
            continue

        if not text.strip():
            continue

        heading = re.match(r"^(#{1,6})\s+", text)
        if heading:
            level = len(heading.group(1))
            if level == 1:
                h1_count += 1
            if previous_level and level > previous_level + 1:
                errors.append(
                    f"{path}:{number}: Markdown 標題階層從 H{previous_level} 跳到 H{level}"
                )
            previous_level = level

        converted = CONVERTER.convert(text)
        if converted != text:
            errors.append(f"{path}:{number}: 一般文字含簡體中文，請改為繁體中文")

    if h1_count == 0:
        errors.append(f"{path}: 缺少 H1 標題")
    elif h1_count > 1:
        errors.append(f"{path}: 有 {h1_count} 個 H1；每份文件只保留一個 H1")

    return errors


def main() -> int:
    markdown_files = sorted(ROOT.rglob("*.md"))
    markdown_files = [p for p in markdown_files if ".git" not in p.parts]

    if not markdown_files:
        print("找不到 Markdown 文件。")
        return 0

    errors: list[str] = []
    for path in markdown_files:
        errors.extend(check_file(path))

    if errors:
        print("Markdown 檢查失敗：")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Markdown 檢查通過：共 {len(markdown_files)} 份文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
