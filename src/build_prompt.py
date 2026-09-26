# 提示词组装器：异议文本 → 结构化提示词
#
# 用法：
#   python src/build_prompt.py "患者问调机太频繁能不能少来几次"
#   python src/build_prompt.py "..." --top 2 --out prompt.txt
#
# 纯标准库实现，无第三方依赖，无网络调用。组装结果可粘贴到任意大模型对话中使用。

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB_FILE = ROOT / "data" / "knowledge_base.json"
TEMPLATE_FILE = ROOT / "prompts" / "system-prompt-template.md"


def load_kb() -> dict:
    with open(KB_FILE, encoding="utf-8") as f:
        return json.load(f)


def tokenize(text: str) -> set:
    """中文按字符二元组 + 英文按词切分，足够支撑关键词匹配演示。"""
    tokens = set()
    cleaned = "".join(ch for ch in text if ch.isalnum())
    for i in range(len(cleaned) - 1):
        tokens.add(cleaned[i : i + 2])
    tokens.update(word.lower() for word in text.split() if len(word) > 1)
    return tokens


def score_entry(entry: dict, query_tokens: set) -> int:
    score = 0
    for kw in entry["keywords"]:
        for token in tokenize(kw):
            if token in query_tokens:
                score += 2
    return score


def retrieve(kb: dict, query: str, top: int) -> list:
    query_tokens = tokenize(query)
    scored = []
    for entry in kb["entries"]:
        s = score_entry(entry, query_tokens)
        # 关键词原文命中加权
        for kw in entry["keywords"]:
            if kw in query:
                s += 3
        if s > 0:
            scored.append((s, entry))
    scored.sort(key=lambda pair: -pair[0])
    return [entry for _, entry in scored[:top]]


def format_entries(entries: list) -> str:
    blocks = []
    for entry in entries:
        lines = [
            f"### {entry['id']} ｜ {entry['category']}",
            f"异议：{entry['objection']}",
            f"真实关切：{entry['underlying_concern']}",
            "要点：",
        ]
        lines += [f"- {point}" for point in entry["key_points"]]
        lines.append("话术提示：" + entry["talk_track_hint"])
        lines.append("红线：")
        lines += [f"- {rule}" for rule in entry["red_lines"]]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_prompt(query: str, entries: list) -> str:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    # 取模板中的代码块作为提示词骨架
    start = template.index("```text") + len("```text")
    end = template.index("```", start)
    skeleton = template[start:end].strip("\n")
    return skeleton.replace("{KNOWLEDGE}", format_entries(entries))


def main() -> None:
    parser = argparse.ArgumentParser(description="异议应对提示词组装器")
    parser.add_argument("query", help="患者异议原文")
    parser.add_argument("--top", type=int, default=2, help="检索条目数（默认 2）")
    parser.add_argument("--out", help="输出到文件（默认打印到终端）")
    args = parser.parse_args()

    kb = load_kb()
    entries = retrieve(kb, args.query, args.top)
    if not entries:
        print("未匹配到知识库条目。提示：换用更接近条目关键词的表述，或先扩充知识库。")
        sys.exit(1)

    matched_ids = "、".join(entry["id"] for entry in entries)
    prompt = build_prompt(args.query, entries)
    header = f"# 检索命中：{matched_ids}\n\n"
    result = header + prompt

    if args.out:
        Path(args.out).write_text(result, encoding="utf-8")
        print(f"已写入 {args.out}（命中 {matched_ids}）")
    else:
        print(result)


if __name__ == "__main__":
    main()
