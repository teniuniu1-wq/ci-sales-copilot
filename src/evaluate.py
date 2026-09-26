# 合规与结构评估器：检查 AI 生成的异议应对草稿
#
# 用法：
#   python src/evaluate.py draft.txt
#   cat draft.txt | python src/evaluate.py
#
# 检查两类问题：
#   1. 红线违规：绝对化用语、疗效承诺、品牌贬低词、缺失转诊语句
#   2. 结构完整：四层契约（事实层/逻辑层/话术层/合规自查）是否齐全
#
# 纯标准库实现。评估规则可随合规要求扩充——规则是数据，不是代码。

import re
import sys
from pathlib import Path

# 红线规则：(名称, 正则, 说明)
RED_LINE_RULES = [
    ("疗效承诺", r"治愈|根治|保证.{0,6}(效果|恢复)|百分之百|恢复(得|的)?和(正常|常人)", "绝对化疗效承诺"),
    ("绝对化用语", r"最好|最强|第一品牌|无人能及|遥遥领先", "广告法意义上的绝对化表述"),
    ("品牌贬低", r"(别的?品牌|他家|友商).{0,12}(差|不行|落后|有问题)", "点名/暗示贬低其他品牌"),
    ("拍板医保金额", r"(医保|报销)(一定|肯定|绝对)(能报|报)", "对报销金额做保证性表述"),
]

# 结构要求：四层契约的段落标记
REQUIRED_SECTIONS = ["事实层", "逻辑层", "话术层", "合规自查"]

# 医疗判断类问题必须包含转诊语句
REFERRAL_PATTERNS = [r"以(医生|听力师|植入团队|专业)[^。]{0,10}(评估|意见|为准)", "转诊", "建议.{0,8}(咨询|就诊)"]


def check_red_lines(text: str) -> list:
    findings = []
    for name, pattern, note in RED_LINE_RULES:
        for match in re.finditer(pattern, text):
            context = text[max(0, match.start() - 12) : match.end() + 12].replace("\n", " ")
            findings.append(f"[红线/{name}] …{context}… ｜ {note}")
    return findings


def check_structure(text: str) -> list:
    findings = []
    for section in REQUIRED_SECTIONS:
        if section not in text:
            findings.append(f"[结构] 缺少段落：{section}")
    return findings


def check_referral(text: str) -> list:
    findings = []
    medical_topics = any(kw in text for kw in ["手术", "效果", "时机", "诊断", "调机"])
    if medical_topics and not any(re.search(p, text) for p in REFERRAL_PATTERNS):
        findings.append("[转诊] 涉及医疗判断但未发现转诊语句（以医生/听力师评估为准）")
    return findings


def check_citations(text: str, kb_ids: set) -> list:
    findings = []
    cited = set(re.findall(r"\[(OBJ-[A-Z]+-\d{3})\]", text))
    unknown = cited - kb_ids
    if unknown:
        findings.append(f"[引用] 引用了知识库中不存在的条目：{ '、'.join(sorted(unknown)) }（疑似幻觉）")
    if cited and not unknown and "事实层" in text:
        findings.append(f"[引用] 通过：{ '、'.join(sorted(cited)) }")
    return findings


def load_kb_ids() -> set:
    import json

    kb_file = Path(__file__).resolve().parents[1] / "data" / "knowledge_base.json"
    with open(kb_file, encoding="utf-8") as f:
        kb = json.load(f)
    return {entry["id"] for entry in kb["entries"]}


def main() -> None:
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("未提供草稿内容。用法：python src/evaluate.py draft.txt 或管道输入。")
        sys.exit(1)

    findings = []
    findings += check_red_lines(text)
    findings += check_structure(text)
    findings += check_referral(text)
    findings += check_citations(text, load_kb_ids())

    violations = [f for f in findings if not f.startswith("[引用] 通过")]
    print(f"评估结果：{'FAIL' if violations else 'PASS'}（{len(violations)} 项问题）")
    for finding in findings:
        print(f"  {finding}")
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
