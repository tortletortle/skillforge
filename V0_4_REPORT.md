# SKILLFORGE V0.4 研发报告

**版本：** 0.4.0  
**日期：** 2026-11-18  
**核心模块：** Evidence-Guided Repair Search (EGRS)

## 1. 研发目标

V0.3 已具备多类型故障诊断、多候选补丁生成、固定启发式排序和安全发布。V0.4 将重点转向搜索策略学习：利用跨任务历史证据估计根因可信度、补丁功能修复概率、回归风险和修复距离，并在每轮重测后更新竞争性根因假设。

V0.4 不替换 V0.1–V0.3 的编译器、受限补丁、版本库和历史回归机制。

## 2. 文献调研与研究边界

### 2.1 CodeTriage

Sharony et al., *Make Every Expansion Count: Learning to Search Efficiently in LLM Code Repair* (2026), https://arxiv.org/abs/2610.15894

CodeTriage 使用 0.6B 参数的优先级模型，读取测试反馈、故障诊断和候选编辑，预测修复距离分布，并按剩余深度计算优先级。论文报告相对最强基线减少 21% 程序修订次数和 12% 输出 token。官方项目页在本版本研发时标注代码即将发布，因此本项目实现的是透明的 CodeTriage-style 结构化生存模型，不是官方权重或精确复现。

### 2.2 RESKILL

Deng et al., *RESKILL: Explicit Failure Attribution and Structured Repair for Interactive Language Agents* (2026), https://arxiv.org/abs/2609.15684

RESKILL 已研究失败假设、候选补丁覆盖关系及重测结果驱动的后续修复更新。V0.4 不将“根因—补丁映射”或“重测后更新”单独宣称为原创。我们的当前研究假设是：跨任务学习策略条件似然，并将根因后验、功能修复概率、回归概率和删失修复距离联合用于候选搜索排序。

### 2.3 Synapse

Li et al., *Synapse: Optimizing Natural-Language Agent Skills through Program Repair* (2026-11-16), https://arxiv.org/abs/2611.20856

Synapse 已涉及 SkIR、控制流/数据依赖、类型化编辑和相关回归测试选择。它是直接竞争性研究，后续应在真实自然语言技能基准上比较；本轮没有复现其完整系统。

### 2.4 SkillRevise

Liu et al., *SkillRevise: Improving LLM-Authored Agent Skills via Trace-Conditioned Skill Revision* (2026), https://arxiv.org/abs/2606.01139

SkillRevise 已将执行证据、修复原则检索、迭代修订和效用门控结合。本轮未声称超过该系统。

## 3. EGRS 方法

### 3.1 多头预测

训练三个二元预测器：

- `P(root_cause_correct | evidence)`：根因假设正确概率。
- `P(functional_fix | evidence)`：功能修复概率。
- `P(no_regression | evidence)`：无历史回归概率。

工程安全分数采用三项概率乘积作为保守近似。该乘积不意味着三个事件统计独立，也不是已校准的联合概率。

### 3.2 修复距离模型

使用五个离散区间：1、2、3、4、>4 次扩展。训练采用右删失目标：超过候选当前剩余深度的样本只提供下界，不被错误标记为永久失败。

### 3.3 根因后验更新

训练集估计不同修复策略在根因假设正确/错误时的功能修复率。测试时，每次候选补丁重测后，利用观察到的功能修复结果更新该根因假设的后验，并重新排序未尝试候选。

### 3.4 证据价值项

评分包含不确定性、失败测试覆盖率和证据多样性构成的信息价值项。该权重只在验证集上调节。本次验证集选择的权重为 **0.0**，说明在当前合成基准上，额外信息价值奖励没有改善平均搜索成本。V0.4 保留此项供后续真实环境研究，但没有强行启用。

## 4. 公平对照协议

- 总计 700 个任务，按任务划分为 398 train / 99 validation / 203 test。
- 每个任务 12 个候选补丁，所有策略使用完全相同的候选前沿。
- 排序策略在候选展开前不能读取隐藏结果；候选结果仅在模拟选择后揭示。
- CodeTriage-style 与 EGRS 使用相同训练任务和任务级划分；EGRS 额外使用结构化证据特征。
- EGRS 信息价值权重只在验证集调节。
- Random、REx-lite、AB-MCTS-β-lite、BG-MCTS-lite 使用 5 个随机种子；其余方法确定性执行。
- 所有任务都按基准生成协议包含至少一个安全修复路线。
- 采用按任务配对 Bootstrap，报告 95% 百分位区间。

### 4.1 对照方法

1. Random
2. BFS
3. DFS
4. Pass-rate
5. V0.3 固定启发式
6. REx-lite：pass-rate-informed Beta Thompson sampling 的有限前沿适配
7. AB-MCTS-β-lite：Beta(0.5, 0.5) 后验的有限前沿适配
8. BG-MCTS-lite：有限候选前沿 UCB 适配
9. CodeTriage-style：结构化输入 + 右删失修复距离模型 + 平均 CDF 优先级
10. EGRS-static：多头证据模型，不做重测后根因后验更新
11. EGRS：多头证据模型 + 贝叶斯根因后验更新

注意：REx/AB-MCTS/BG-MCTS 是轻量有限前沿适配，不是各论文的完整原版实现；CodeTriage-style 也不是官方 0.6B 模型。当前实验适合比较本项目中实现的策略，不适合与原论文报告的数值横向比较。

## 5. 实验结果

测试集 203 个任务、2,436 个候选补丁。

| 方法 | 离散预算曲线面积 | 平均封顶扩展次数 |
|---|---:|---:|
| Random | 58.44% | 4.101 |
| BFS | 57.83% | 4.138 |
| DFS | 57.34% | 4.236 |
| Pass-rate | 60.00% | 3.916 |
| V0.3 Heuristic | 87.88% | 1.640 |
| REx-lite | 67.72% | 3.192 |
| AB-MCTS-β-lite | 69.67% | 2.854 |
| BG-MCTS-lite | 69.06% | 2.847 |
| CodeTriage-style | 90.74% | 1.468 |
| EGRS-static | 92.12% | 1.394 |
| **EGRS** | **93.89%** | **1.305** |

### 5.1 相对 CodeTriage-style

- 平均扩展次数差（EGRS − CodeTriage-style）：-0.163，95% CI [-0.251, -0.064]。
- 离散预算曲线面积差：+3.15 个百分点，95% CI [+1.18, +4.93] 个百分点。
- 预算 1 成功率差：+8.87 个百分点，95% CI [+1.48, +15.76] 个百分点。
- 预算 2 成功率差：+6.90 个百分点，95% CI [+3.45, +10.84] 个百分点。

### 5.2 动态后验更新消融

相对 EGRS-static，动态 EGRS：

- 平均扩展次数降低 0.089，95% CI [-0.138, -0.049]。
- 离散预算曲线面积提高 1.77 个百分点，95% CI [+0.99, +2.95] 个百分点。

### 5.3 校准与根因指标

- 安全修复概率 Brier score：0.1455。
- 安全修复概率 ECE（10 bins）：0.0573。
- 根因二分类准确率（阈值 0.5）：98.07%。

这些指标来自合成标签。尤其根因准确率较高，反映的是当前合成证据生成规则可学习，不能外推为真实 Agent 根因诊断准确率。

## 6. 重要限制

1. 当前 benchmark 为合成修复前沿，未接入真实 LLM Agent。
2. 每个任务被保证至少存在一个安全修复路线，现实中可能无可行修复。
3. 结果生成机制和训练/测试分布同源，仍需 OOD、真实任务及不同模型提议器验证。
4. CodeTriage-style 不是官方模型，不能将本实验结果解释为击败官方 CodeTriage。
5. REx/AB-MCTS/BG-MCTS 为简化适配，不是严格复现。
6. 当前补丁候选生成器沿用 V0.3 的确定性规则；V0.4 主要改进候选搜索和排序，不等于开放式 LLM 补丁生成。
7. 真实运行时证据中的根因标签可能只是测试改善代理。代码将其标记为 `runtime_proxy_not_independent_causal_label`，不会纳入 `verified_runtime` 训练集。
8. 本轮验证集选择的信息价值权重为 0.0；该奖励在当前基准上没有显示增益，需要在交互式真实环境中重新研究。

## 7. 下一步

- 接入 SkillFlow、SkillLearnBench、SkillsBench、SWE-Skills-Bench 或自建真实 Agent 执行轨迹适配器。
- 实现真正的 repair-tree 多层展开，而不仅是单层候选前沿。
- 加入 OOD 按故障类型留出、跨提议器迁移和模型校准实验。
- 与 RESKILL、Synapse、SkillRevise 做可复现的真实环境对照。
- 用独立干预实验产生根因标签，减少弱代理标签。
- 研究何时应继续修补、何时应停止并请求人工介入。

## 8. 可复现命令

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
python -m skillforge.cli v04-demo --tasks 700 --stochastic-runs 5
```

结果文件：`benchmarks/V0_4_BENCHMARK_RESULTS.json`。训练合成证据：`benchmarks/synthetic_train_evidence.jsonl`。数据清单：`benchmarks/DATASET_MANIFEST.json`。
