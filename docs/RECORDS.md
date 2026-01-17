# 处理记录 / Processing Records

本文档记录了本项目在开发测试阶段处理的数据规模、抽样策略以及相关的省略说明。
This document records the data scale, sampling strategy, and omissions during the development and testing phases of this project.

## 1. 处理规模概览 / Overview of Processing Scale

我们针对三个具有代表性的代码库进行了完整流水线的测试运行：
We tested the complete pipeline on three representative codebases:

### 仓库明细 / Repository Breakdown

| 仓库名称 / Repository | 原始切片总数 / Total Slices | 处理场景 1 (函数) / Scenario 1 | 处理场景 2 (类) / Scenario 2 | 备注 / Note |
| :--- | :--- | :--- | :--- | :--- |
| repo_fastapi_light | 92 | 38 | 54 | 全量处理 / Full processing |
| repo_ecommerce_medium | 10,975 | 500 | 500 | 抽样处理 / Sampled |
| repo_iot_special | 35,241 | 200 | 200 | 抽样处理 / Sampled |

### 最终产出 / Final Output (2026-01-17)

*   加载原始响应 / Raw Responses Loaded: 1,492 项 (Items)
*   有效训练样本 / Valid Samples: 1,444 项 (Items)
*   训练集 / Training Set: 1,155 项 (Items)
*   验证集 / Validation Set: 289 项 (Items)

## 2. 抽样与省略说明 / Sampling and Omissions

为了兼顾测试效率与成本，我们在处理过程中作了以下调整：
To balance testing efficiency and cost, the following adjustments were made:

### 数量抽样 / Quantity Sampling
对于规模较大的仓库（Medium 和 Special），我们没有进行全量 LLM 生成，而是采用了限制数量的抽样策略（如上表所示）。这确保了我们在可控成本内验证了多样性。
For larger repositories (Medium and Special), we did not perform full LLM generation. Instead, we used a limited sampling strategy. This ensured diversity verification within controlled costs.

### 流程简化 / Process Simplification
在当前的自动化流程中，我们直接将 Stage 1 的切片结果输入到 Stage 2，跳过了人工审核切片（Manual Review）的环节。在生产环境中，建议根据需求保留审核步骤以提升数据精度。
In the current automated flow, we directly fed Stage 1 slices into Stage 2, skipping the manual review step. In production, we recommend keeping the review step to improve data precision.

## 3. 质量指标 / Quality Metrics

根据最近一次编译统计：
According to the latest compilation statistics:

*   解析成功率 / Parse Success Rate: ~96.78% (LLM 输出符合 JSON 规范的比例)
*   逻辑深度 / Reasoning Depth:
    *   场景 1 (QA) 平均推理步骤: 6.05 步 (Steps)
    *   场景 2 (Design) 平均决策点: 2.97 个 (Decision Points)

详细统计报告请参考根目录下的最新生成的 JSON 统计文件。
For detailed reports, please refer to the latest generated JSON statistics file in the root directory.
