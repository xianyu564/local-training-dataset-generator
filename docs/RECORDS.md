# 处理记录 / Processing Records

本文档记录了开发与测试阶段的处理规模、抽样策略及产出数据。

This document records the processing scale, sampling strategy, and output data during development and testing.

## 1. 示例仓库差异与规模 / Repository Differences & Scale

为了验证系统在不同复杂度和领域下的表现，我们选择了三个具有代表性的异构仓库：

| 仓库名称 | 领域 / 特点 | 代码规模 | 复杂度等级 | 选样原因 |
| :--- | :--- | :--- | :--- | :--- |
| **repo_fastapi_light** | Web 框架 / 后端 API | ~100 切片 (小型) | 低 | 验证基础 CRUD 逻辑的 QA 生成。 |
| **repo_ecommerce_medium** | 电商系统 / 复杂业务 | ~1.1k 切片 (中型) | 中 | 验证复杂业务规则（如支付、折扣）的提取。 |
| **repo_iot_special** | 物联网平台 / 高度模块化 | ~3.5k 切片 (大型) | 高 | 验证大规模仓库下的静态分析与异步 Batch 处理能力。 |

## 2. 处理规模概览 / Processing Overview

| 仓库名称 | 原始切片总数 | 场景 1（函数） | 场景 2（类） | 处理策略 |
| :--- | ---: | ---: | ---: | :--- |
| repo_fastapi_light | 92 | 38 | 54 | **全量**：处理所有检测到的符号。 |
| repo_ecommerce_medium | 10,975 | 500 | 500 | **抽样**：随机抽取核心逻辑块。 |
| repo_iot_special | 35,241 | 200 | 200 | **抽样**：侧重于核心集成模块。 |

## 3. 当次运行的最终产出（2026-01-17）/ Final Outputs

- 加载的原始响应条目：1,492
- 编译得到的有效训练样本：1,444
- 训练集：1,155
- 验证集：289

## 3. 抽样与省略说明

- **数量抽样**：对规模较大的仓库未进行全量 LLM 生成，而是限制场景 1/2 的样本数量以控制成本与时间。
- **流程简化**：本次运行将 Stage 1 输出直接用于 Stage 2（即未使用 `data/2.reviewed_slices` 的人工审核环节）。

## 4. 质量指标（来自当次统计文件）

- 解析成功率（JSON 可解析比例）：约 96.78%
- 平均推理深度：
  - 场景 1：约 6.05 步
  - 场景 2：约 2.97 个分析/决策点

详细统计以 `data/5.final_output/` 下最新生成的统计文件为准。
