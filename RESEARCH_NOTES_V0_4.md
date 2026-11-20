# SKILLFORGE V0.4 研究笔记

## 关键文献

- CodeTriage (2026): https://arxiv.org/abs/2610.15894
- RESKILL (2026): https://arxiv.org/abs/2609.15684
- Synapse (2026-11-16): https://arxiv.org/abs/2611.20856
- SkillRevise (2026): https://arxiv.org/abs/2606.01139
- Agent Skills Can Be Harmful (2026): https://arxiv.org/abs/2608.11888

## 研究定位

V0.4 的核心假设是：跨任务学习到的策略条件修复似然，可以帮助搜索器在观察补丁重测结果后更新竞争性根因假设；与右删失修复距离和回归风险联合后，可改善有限预算下的补丁搜索顺序。

与 RESKILL 的重测条件更新有明显关系；与 CodeTriage 的学习修复距离排序有明显关系；与 Synapse 的结构化诊断和回归测试选择有明显关系。因此不宣称这些组件本身全新。当前需进一步验证的组合差异是跨任务证据似然学习、根因后验更新和安全修复效用排序的联合行为。

## 需要防止的实验错误

- 不能把 synthetic benchmark 成绩写成真实 Agent 成绩。
- 不能把 CodeTriage-style 写成官方 CodeTriage 复现。
- 不能把简化 REx/AB-MCTS/BG-MCTS 写成原论文算法完整复现。
- 不能用 test split 选择信息价值权重或模型超参数。
- 不能把测试改善代理标签当作因果真值。
- 不能只报告成功率而不报告预算、回归、成本和置信区间。
