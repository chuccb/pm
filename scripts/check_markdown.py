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
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
URL_RE = re.compile(r"https?://[^\s)]+")
HTML_TAG_RE = re.compile(r"<[^>]+>")
MARKDOWN_LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def strip_non_prose(line: str) -> str:
    """移除不需要做自然語言檢查的 Markdown／技術內容。"""
    text = INLINE_CODE_RE.sub("", line)
    text = URL_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    text = MARKDOWN_LINK_RE.sub("", text)
    return text


def is_fence(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{path}: 不是 UTF-8 編碼"]

    h1_count = 0
    previous_level = 0
    in_fence = False

    for number, raw_line in enumerate(content.splitlines(), start=1):
        if is_fence(raw_line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        text = strip_non_prose(raw_line)
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


def indexed_research_files() -> set[str]:
    """從唯一研究索引取得明確列出的 Research Markdown 路徑。"""
    index_path = ROOT / "Research" / "DOCUMENT_INDEX.md"
    content = index_path.read_text(encoding="utf-8")
    indexed: set[str] = set()

    for match in MARKDOWN_LINK_RE.finditer(content):
        target = match.group(1).split("#", 1)[0].strip()
        if not target.lower().endswith(".md"):
            continue
        if target.startswith(("http://", "https://")):
            continue
        indexed.add((Path("Research") / target).as_posix())

    return indexed


def check_index_coverage(markdown_files: list[Path]) -> list[str]:
    """只阻止新的 Research Markdown 漏掉唯一索引；不強制重寫既有索引連結。"""
    index_path = ROOT / "Research" / "DOCUMENT_INDEX.md"
    if not index_path.exists():
        return [f"{index_path}: 找不到唯一研究文件索引"]

    indexed = indexed_research_files()
    research_files = {
        path.relative_to(ROOT).as_posix()
        for path in markdown_files
        if "Research" in path.relative_to(ROOT).parts
        and path.name != "DOCUMENT_INDEX.md"
    }

    missing = sorted(research_files - indexed)
    return [f"{path}: 尚未出現在 Research/DOCUMENT_INDEX.md" for path in missing]


def main() -> int:
    markdown_files = sorted(ROOT.rglob("*.md"))
    markdown_files = [p for p in markdown_files if ".git" not in p.parts]

    if not markdown_files:
        print("找不到 Markdown 文件。")
        return 0

    errors: list[str] = []
    for path in markdown_files:
        errors.extend(check_file(path))

    errors.extend(check_index_coverage(markdown_files))

    if errors:
        print("Markdown 檢查失敗：")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Markdown 檢查通過：共 {len(markdown_files)} 份文件，Research 索引完整。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
