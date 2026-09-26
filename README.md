# CI Sales Copilot · 听力医疗异议应对知识引擎

**EN**: A knowledge engine that turns field sales objection-handling experience into a structured, compliance-checkable asset — objection taxonomy + curated knowledge base + deterministic prompt assembly + automated compliance evaluation. Pure standard library, no API key needed.

> 数据与内容声明：知识库条目为品牌中立的合成示例，用于演示结构与方法；异议**分类法**来自一线销售经验的归纳泛化。不含任何品牌的竞争话术或未公开信息。

## 一句话定位

把"老销售脑子里的应对经验"变成四件可维护的东西：分类法、知识库、组装器、评估器——让每次拜访前的准备从"翻文档、凭记忆"变成"检索、组装、过检"。

## 问题背景

患者异议高度重复，但应对质量靠运气：口径因人而异、合规红线靠自觉、新人成长靠耳濡目染。更麻烦的是，大语言模型可以直接生成话术，却没人检查它有没有说出"保证治愈"或者贬低竞品——在医疗行业，这是真实的风险。

## 方案：一条四段流水线

```text
患者异议原文
   │  ① 分类法（docs/objection-taxonomy.md）—— 八大类，每类标注真实关切与红线
   ▼
② 知识库检索（data/knowledge_base.json）—— 关键词评分，取 Top-N 条目
   │
   ▼
③ 提示词组装（src/build_prompt.py）—— 回答契约 + 检索条目 → 结构化提示词
   │  （粘贴到任意大模型即可生成四层结构的应对草稿）
   ▼
④ 合规评估（src/evaluate.py）—— 红线正则 + 结构完整性 + 转诊检查 + 引用校验
      输出 PASS / FAIL 与逐项问题清单
```

**回答契约**（[prompts/answer-contract.md](prompts/answer-contract.md)）：AI 草稿必须是四层结构——事实层（带来源 ID）、逻辑层（关切→要点对应）、话术层（90 秒口语稿）、合规自查。缺一层即不合格。

**红线规则是数据不是代码**：`evaluate.py` 里的正则规则表可以随合规要求随时扩充，不用改代码。

## 实测演示

组装器按异议检索并命中正确条目：

```text
$ python src/build_prompt.py "患者说调机太频繁了，能不能少来几次"
# 检索命中：OBJ-FLOW-001
（输出完整结构化提示词，含知识库条目、四层契约与红线）
```

评估器对违规草稿 FAIL、对合格草稿 PASS：

```text
$ python src/evaluate.py bad_draft.txt
评估结果：FAIL（8 项问题）
  [红线/疗效承诺] …我们的产品保证效果恢复得和正常人一样… ｜ 绝对化疗效承诺
  [红线/品牌贬低] …别的品牌这方面不行… ｜ 点名/暗示贬低其他品牌
  [红线/拍板医保金额] …医保肯定能报销大头… ｜ 对报销金额做保证性表述
  [结构] 缺少段落：事实层 / 逻辑层 / 话术层 / 合规自查
  [转诊] 涉及医疗判断但未发现转诊语句

$ python src/evaluate.py good_draft.txt
评估结果：PASS（0 项问题）
  [引用] 通过：OBJ-FLOW-001
```

## 复现

```bash
# 纯标准库，无需安装依赖
python src/build_prompt.py "患者异议原文"              # 组装提示词
python src/build_prompt.py "..." --top 2 --out p.txt  # 检索 2 条并落盘
python src/evaluate.py draft.txt                      # 评估草稿
```

## 边界与反思

1. **草稿不是答案**。工具服务"拜访前准备"，最终对患者说的话，由懂这个患者的人负责——这条边界写在系统提示词里，也写在团队工作方式里。
2. **评估器是护栏不是真理**。正则能抓住"保证治愈"，抓不住微妙的误导。合规审查的最后一环永远是人，评估器的价值是把明显的错误拦在人工之前。
3. **知识库是活的资产**。一线遇到的新异议和更好的讲法应该回写知识库——这套结构的意义就是让经验可以积累、口径可以统一、新人可以更快上手。

## 工作流时间自测（框架）

评估"这个工具省了多少时间"的正确方式是前后对照，而不是估 feel：

| 环节 | 工具前 | 工具后 | 度量方式 |
|---|---|---|---|
| 检索应对口径 | 翻文档/问同事 ___ 分钟 | 检索 + 组装 ___ 分钟 | 计时 10 次真实准备 |
| 口径一致性 | 各说各话 | 知识库单一来源 | 抽查周例会口径差异 |
| 合规检查 | 靠自觉 | 评估器强制 + 人工复核 | 每周 FAIL 拦截数 |

【自测数据待补：按上表实测后回填，不估算、不编造】

## 与作品集的关系

本仓库对应简历主张："AI 落地真实业务场景"。配套仓库：[ci-patient-journey-assistant](https://github.com/teniuniu1-wq/ci-patient-journey-assistant)（患者旅程产品化）、[patient-journey-analytics](https://github.com/teniuniu1-wq/patient-journey-analytics)（旅程量化分析）——一个定义旅程，一个量化旅程，一个武装旅程中的人。
