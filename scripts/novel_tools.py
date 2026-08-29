#!/usr/bin/env python3
"""Local utilities for a Markdown novel project. No third-party packages required."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
PLANS = ROOT / "outline" / "chapter-plans"
SUMMARIES = ROOT / "state" / "chapter-summaries"
CHAPTER_RE = re.compile(r"chapter-(\d{3})\.md$")
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
HOOK_RE = re.compile(r"\bH\d{3,}\b")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def chapter_files() -> list[Path]:
    return sorted(MANUSCRIPT.glob("volume-*/chapter-*.md"))


def count_text(text: str) -> tuple[int, int]:
    body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    body = re.sub(r"^#.*$", "", body, flags=re.M)
    body = re.sub(r"【.*?】", "", body, flags=re.S)
    han = len(HAN_RE.findall(body))
    nonspace = len(re.sub(r"\s", "", body))
    return han, nonspace


def cmd_stats(_: argparse.Namespace) -> int:
    files = chapter_files()
    if not files:
        print("未找到正文文件。")
        return 0
    total_han = total_nonspace = 0
    for path in files:
        han, nonspace = count_text(read_text(path))
        total_han += han
        total_nonspace += nonspace
        print(f"{path.relative_to(ROOT)}: 中文字符 {han:,}，非空白字符 {nonspace:,}")
    print(f"合计: 中文字符 {total_han:,}，非空白字符 {total_nonspace:,}")
    return 0


def cmd_check(_: argparse.Namespace) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        ROOT / "AGENTS.md",
        ROOT / "config" / "project.yaml",
        ROOT / "config" / "style-guide.md",
        ROOT / "outline" / "master-outline.md",
        ROOT / "state" / "current-state.md",
        ROOT / "state" / "timeline.md",
        ROOT / "state" / "unresolved-hooks.md",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"缺少必要文件: {path.relative_to(ROOT)}")

    seen: dict[int, Path] = {}
    for path in chapter_files():
        match = CHAPTER_RE.search(path.name)
        if not match:
            errors.append(f"章节文件名不规范: {path.relative_to(ROOT)}")
            continue
        number = int(match.group(1))
        if number in seen:
            errors.append(
                f"章节编号重复: {seen[number].relative_to(ROOT)} 与 {path.relative_to(ROOT)}"
            )
        seen[number] = path
        text = read_text(path)
        meta = frontmatter(text)
        for key in ("chapter", "volume", "title", "status", "pov"):
            if not meta.get(key):
                errors.append(f"{path.relative_to(ROOT)} 缺少元数据: {key}")
        if meta.get("chapter", "").isdigit() and int(meta["chapter"]) != number:
            errors.append(f"{path.relative_to(ROOT)} 文件编号与 chapter 元数据不一致")
        if "【从这里开始正文" in text:
            warnings.append(f"{path.relative_to(ROOT)} 仍是空白正文模板")
        plan = PLANS / path.name
        summary = SUMMARIES / path.name
        if not plan.exists():
            warnings.append(f"缺少对应章纲: {plan.relative_to(ROOT)}")
        if not summary.exists():
            warnings.append(f"缺少对应摘要: {summary.relative_to(ROOT)}")

    hooks_path = ROOT / "state" / "unresolved-hooks.md"
    if hooks_path.exists():
        hooks = HOOK_RE.findall(read_text(hooks_path))
        duplicates = sorted({hook for hook in hooks if hooks.count(hook) > 1})
        if duplicates:
            warnings.append("伏笔编号重复出现，请确认是否为同一条: " + ", ".join(duplicates))

    if errors:
        print("错误：")
        for item in errors:
            print(f"  - {item}")
    if warnings:
        print("提醒：")
        for item in warnings:
            print(f"  - {item}")
    if not errors and not warnings:
        print("检查通过，未发现结构问题。")
    elif not errors:
        print("结构检查通过；以上提醒不阻止继续写作。")
    return 1 if errors else 0


def replace_template(text: str, number: int, volume: int, title: str) -> str:
    padded = f"{number:03d}"
    text = re.sub(r"(?m)^chapter: 0$", f"chapter: {number}", text)
    text = re.sub(r"(?m)^volume: 1$", f"volume: {volume}", text)
    text = text.replace('title: "【章节标题】"', f'title: "{title}"')
    text = text.replace("第000章", f"第{padded}章")
    text = text.replace("第0章", f"第{number}章")
    text = text.replace("章节标题", title)
    return text


def cmd_new_chapter(args: argparse.Namespace) -> int:
    existing = [int(m.group(1)) for p in chapter_files() if (m := CHAPTER_RE.search(p.name))]
    number = args.number if args.number is not None else (max(existing, default=0) + 1)
    padded = f"{number:03d}"
    volume_dir = MANUSCRIPT / f"volume-{args.volume:02d}"
    targets = {
        PLANS / f"chapter-{padded}.md": ROOT / "templates" / "chapter-plan.md",
        volume_dir / f"chapter-{padded}.md": ROOT / "templates" / "chapter.md",
        SUMMARIES / f"chapter-{padded}.md": ROOT / "templates" / "chapter-summary.md",
    }
    collisions = [target for target in targets if target.exists()]
    if collisions:
        print("未创建：以下文件已经存在：")
        for path in collisions:
            print(f"  - {path.relative_to(ROOT)}")
        return 1
    for target, template in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        content = replace_template(read_text(template), number, args.volume, args.title)
        target.write_text(content, encoding="utf-8", newline="\n")
        print(f"已创建 {target.relative_to(ROOT)}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="本地小说项目辅助工具")
    sub = root.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="检查项目结构和章节配套文件")
    check.set_defaults(func=cmd_check)
    stats = sub.add_parser("stats", help="统计正文字符数")
    stats.set_defaults(func=cmd_stats)
    new = sub.add_parser("new-chapter", help="创建章纲、正文和摘要")
    new.add_argument("--volume", type=int, default=1, help="卷号，默认 1")
    new.add_argument("--number", type=int, help="章节号，默认自动递增")
    new.add_argument("--title", default="【章节标题】", help="章节标题")
    new.set_defaults(func=cmd_new_chapter)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
