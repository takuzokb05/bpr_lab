# 阿里最新论文「SkillRouter」

- URL: https://x.com/shao__meng/status/2036975150500057570
- ソース: x
- 言語: zh
- テーマ: ai-news
- 取得日: 2026-03-29
- いいね: 227 / RT: 44 / リプライ: 23
- 投稿者: @shao__meng / フォロワー 28,646

## 投稿内容

阿里最新论文「SkillRouter」

AI Agent 生态中 Skills 已达数万规模，上下文窗口无法容纳全部，导致 “Skill Routing” 成为瓶颈。现有框架采用“渐进披露”设计，仅向 Agent 暴露 Skill 名称+描述，隐含假设“元数据足以选择”。

论文首次在大规模基准（≈80K Skills、75 个专家验证查询）上系统验证该假设，结果彻底推翻：Skill 主体（body，即完整实现代码）是决定性信号。移除 body 后，所有检索方法准确率下降 29–44 个百分点；交叉编码器注意力分析显示 91.7% 注意力集中在 body 上，描述仅占 1.0%。Skills 池中功能高度重叠，进一步放大 body 的区分价值。

提出方法：SkillRouter
两阶段 retrieve-and-rerank 流水线，总参数仅 1.2B（0.6B 编码器 + 0.6B 重排序器），专为消费级硬件设计。
· 第一阶段（SR-Emb-0.6B）：双编码器，用完整 Skills 文本（name+desc+body）预编码 Skills 池，ANN 检索 Top-20 候选。采用精心负例挖掘 + 三层假阴性过滤 + In-batch InfoNCE 对比学习。
· 第二阶段（SR-Rank-0.6B）：交叉编码器，逐对处理 query 与候选的完整文本，采用 listwise 交叉熵损失（LW），迫使模型在同质 Skills 间进行相对排序。
训练数据：37,979 对查询-Skills 样本（GPT-4o-mini 合成，训练/测试完全 disjoint）。

实验结果
· 主要指标：Hit@1（Top-1 路由准确率，主指标）、MRR@10、nDCG@10、Recall@K、FC@10。
· 紧凑模型性能：SkillRouter-1.2B 在 Easy/Hard 难度上平均 Hit@1 达 74.0%（单 Skill 查询 72.9%，多 Skills 查询 74.5%）。
· 对比：显著优于最强零样本 8B 基线（Qwen3-Emb-8B × Qwen3-Rank-8B，68.0%），提升 +6.0pp；也优于 GPT-4o-mini/GPT-5.4-mini 等 LLM Judge 作为重排序器。
· 8B 扩展：相同配方下 Hit@1 升至 76.0%，验证方法可扩展。
· 关键消融：
  · 假阴性过滤：+4.0pp Hit@1（Hard 难度更明显）。
  · Listwise 损失 vs Pointwise BCE：+30.7pp（后者在高度同质池中失效）。

论文提交到 @HuggingPapers 了（@_akhaliq 创建）
https://t.co/ILN7zatUEc

## 要約

（要約は次回 /curate 時に追記）
