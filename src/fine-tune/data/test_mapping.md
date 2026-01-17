# 测试问题与验证集 (Validation Dataset) 对应关系表

本文档记录了 `data/test_questions.csv` 中的 10 个测试问题与某次生成的验证集文件（示例：`data/val_dataset_20260117_194659.jsonl`）之间的对应关系，用于复核“测试题是否来自验证集样本”。

| 问题 ID | 难度 | 场景 | 对应验证集行号 | 关联代码/架构组件 | 关联文件路径 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Simple | 1 | 7 | `convert_field_to_camel_case` | `app\models\domain\rwmodel.py` |
| 2 | Simple | 1 | 20 | `fastapi_kwargs` | `app\core\settings\app.py` |
| 3 | Medium | 1 | 2 | `remove_the_oldest_user_address` | `saleor\account\utils.py` |
| 4 | Medium | 1 | 5 | `get_total_gift_cards_balance` | `saleor\checkout\models.py` |
| 5 | Complex | 1 | 6 | `_prepare_order_data` | `saleor\checkout\complete_checkout.py` |
| 6 | Simple | 2 | 9 | `BlockingCall` (IO 优化模式) | `homeassistant\block_async_io.py` |
| 7 | Simple | 2 | 11 | `CreateToken` (Mutation 扩展) | `saleor\graphql\account\mutations\authentication\create_token.py` |
| 8 | Medium | 2 | 4 | `CoreAppConfig` (初始化机制) | `saleor\core\apps.py` |
| 9 | Medium | 2 | 10 | `TransactionFlowStrategy` (支付策略) | `saleor\channel\__init__.py` |
| 10 | Complex | 2 | 15 | `Meta` (Discount 缓存方案设计) | `saleor\discount\models.py` |

---
**说明：**
- **场景 1** 侧重于对验证集中具体函数逻辑的理解与分析。
- **场景 2** 侧重于基于验证集中提供的类架构或模式，设计符合该模式的新需求方案。
- 问题的复杂度（Simple/Medium/Complex）是根据对应验证集样本的逻辑深度及设计要求的难度来确定的。
