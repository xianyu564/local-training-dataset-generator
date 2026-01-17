# Training Dataset Generation System Design Document
# 训练数据集生成系统设计文档

## 1. Overview / 概述

### 1.1 Purpose / 目的
This system automates the generation and processing of training data for proprietary model training based on local code repositories. It supports two primary scenarios for generating high-quality training datasets.

本系统自动化生成和处理训练数据，以支持基于本地代码仓的专有模型训练。系统支持两个主要场景的高质量训练数据集生成。

### 1.2 Key Features / 核心特性
- **Automated Q&A Generation**: Extracts business logic and generates Q&A pairs with code context
- **Design Solution Generation**: Creates architecture-based design solutions with reasoning traces
- **Bilingual Support**: Full Chinese and English language support
- **Quality Assurance**: Built-in validation and quality checks
- **Extensible Architecture**: Modular design for future enhancements

---

## 2. Dataset Structure / 数据集结构

### 2.1 Scenario 1: Q&A Pair Dataset / 场景1: 问答对数据集

#### Data Schema / 数据模式
```json
{
  "id": "unique_identifier",
  "type": "qa_pair",
  "language": "en|zh",
  "question": "The question text",
  "answer": "The answer text",
  "code_context": {
    "file_path": "path/to/file.py",
    "function_name": "function_name",
    "class_name": "class_name (optional)",
    "code_snippet": "relevant code snippet",
    "start_line": 10,
    "end_line": 25
  },
  "business_rules": [
    "extracted business rule 1",
    "extracted business rule 2"
  ],
  "reasoning_trace": {
    "steps": [
      {
        "step_number": 1,
        "description": "Analysis step description",
        "code_reference": "specific code element",
        "reasoning": "explanation of the logic"
      }
    ],
    "conclusion": "final reasoning conclusion"
  },
  "metadata": {
    "repository": "owner/repo_name",
    "generated_at": "timestamp",
    "complexity": "simple|medium|complex",
    "tags": ["tag1", "tag2"]
  }
}
```

#### Q&A Types / 问答类型
1. **Code Understanding / 代码理解**: Questions about what code does
2. **Business Logic / 业务逻辑**: Questions about business rules and workflows
3. **Design Patterns / 设计模式**: Questions about architectural patterns used
4. **API Usage / API使用**: Questions about how to use specific APIs
5. **Error Handling / 错误处理**: Questions about error scenarios

### 2.2 Scenario 2: Design Solution Dataset / 场景2: 设计方案数据集

#### Data Schema / 数据模式
```json
{
  "id": "unique_identifier",
  "type": "design_solution",
  "language": "en|zh",
  "requirement": {
    "title": "Requirement title",
    "description": "Detailed requirement description",
    "constraints": ["constraint1", "constraint2"],
    "functional_requirements": ["req1", "req2"],
    "non_functional_requirements": ["nfr1", "nfr2"]
  },
  "design_solution": {
    "overview": "High-level design overview",
    "architecture": {
      "style": "microservices|monolithic|layered|etc",
      "components": [
        {
          "name": "component_name",
          "responsibility": "what it does",
          "interfaces": ["interface1", "interface2"],
          "dependencies": ["dep1", "dep2"]
        }
      ],
      "data_flow": "description of data flow",
      "technology_stack": {
        "languages": ["Python", "JavaScript"],
        "frameworks": ["Flask", "React"],
        "databases": ["PostgreSQL"],
        "infrastructure": ["Docker", "Kubernetes"]
      }
    },
    "implementation_plan": [
      {
        "phase": 1,
        "description": "Phase description",
        "tasks": ["task1", "task2"],
        "estimated_effort": "time estimate"
      }
    ]
  },
  "code_references": {
    "similar_patterns": [
      {
        "file_path": "path/to/similar/code.py",
        "pattern_name": "pattern name",
        "code_snippet": "relevant code",
        "explanation": "why this is relevant"
      }
    ],
    "reusable_components": ["component1", "component2"]
  },
  "reasoning_trace": {
    "decision_points": [
      {
        "decision": "Key architectural decision",
        "rationale": "Why this decision was made",
        "alternatives_considered": [
          {
            "option": "alternative option",
            "pros": ["pro1", "pro2"],
            "cons": ["con1", "con2"],
            "rejection_reason": "why rejected"
          }
        ],
        "chosen_solution": {
          "description": "chosen approach",
          "justification": "detailed justification",
          "trade_offs": ["tradeoff1", "tradeoff2"]
        }
      }
    ],
    "architecture_evolution": [
      {
        "stage": "evolution stage",
        "rationale": "why this evolution"
      }
    ]
  },
  "metadata": {
    "repository": "owner/repo_name",
    "generated_at": "timestamp",
    "complexity": "simple|medium|complex",
    "domain": "web|mobile|backend|data|etc",
    "tags": ["tag1", "tag2"]
  }
}
```

---

## 3. System Architecture / 系统架构

### 3.1 Component Overview / 组件概览

```
┌─────────────────────────────────────────────────────────┐
│                   Input Layer / 输入层                    │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │ Git Repository Clone │  │  Configuration Manager   │ │
│  └──────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Analysis Layer / 分析层                      │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │   Code Parser        │  │  AST Analyzer            │ │
│  └──────────────────────┘  └──────────────────────────┘ │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │ Business Logic       │  │  Pattern Detector        │ │
│  │ Extractor            │  │                          │ │
│  └──────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│           Generation Layer / 生成层                       │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │ Q&A Generator        │  │  Design Solution         │ │
│  │ (Scenario 1)         │  │  Generator (Scenario 2)  │ │
│  └──────────────────────┘  └──────────────────────────┘ │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │ Reasoning Trace      │  │  Bilingual Translator    │ │
│  │ Generator            │  │                          │ │
│  └──────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│          Quality Assurance Layer / 质量保证层             │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │ Diversity Checker    │  │  Validation Engine       │ │
│  └──────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Output Layer / 输出层                        │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │ Dataset Formatter    │  │  Export Manager          │ │
│  └──────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Key Components / 关键组件

#### 3.2.1 Code Repository Analyzer / 代码仓库分析器
- **Purpose**: Parse and analyze code repositories
- **Functions**:
  - Clone and navigate repositories
  - Extract code structure (classes, functions, modules)
  - Identify dependencies and relationships
  - Detect design patterns

#### 3.2.2 Q&A Generator / 问答生成器
- **Purpose**: Generate question-answer pairs from code
- **Strategy**:
  - Function-level analysis for simple Q&A
  - Class-level analysis for design Q&A
  - Module-level analysis for architecture Q&A
  - Cross-file analysis for workflow Q&A

#### 3.2.3 Design Solution Generator / 设计方案生成器
- **Purpose**: Create design solutions based on requirements
- **Strategy**:
  - Analyze existing architecture patterns
  - Match requirements to similar implementations
  - Generate component diagrams
  - Provide reasoning traces for decisions

#### 3.2.4 Reasoning Trace Generator / 推理轨迹生成器
- **Purpose**: Generate step-by-step reasoning processes
- **Functions**:
  - Trace code execution flow
  - Document decision points
  - Explain architectural choices
  - Link code to business logic

---

## 4. Data Diversity and Quality / 数据多样性和质量

### 4.1 Diversity Mechanisms / 多样性机制

#### 4.1.1 Code Coverage Diversity / 代码覆盖多样性
- Sample from different modules and packages
- Include various complexity levels (simple, medium, complex)
- Cover different programming paradigms (OOP, functional, procedural)

#### 4.1.2 Question Type Diversity / 问题类型多样性
- Mix of "what", "how", "why" questions
- Different abstraction levels (implementation, design, architecture)
- Various domains (API, business logic, data processing, UI)

#### 4.1.3 Language Diversity / 语言多样性
- Generate parallel Chinese and English versions
- Context-aware translation for technical terms
- Cultural adaptation for examples

### 4.2 Quality Assurance / 质量保证

#### 4.2.1 Validation Rules / 验证规则
- **Completeness**: All required fields are present
- **Consistency**: Code snippets match file paths
- **Accuracy**: Line numbers are correct
- **Relevance**: Answer addresses the question
- **Clarity**: Reasoning traces are logical

#### 4.2.2 Quality Metrics / 质量指标
- **Code Context Relevance**: Measure relevance of code snippet to Q&A
- **Reasoning Depth**: Number of reasoning steps and detail level
- **Answer Completeness**: Coverage of question aspects
- **Technical Accuracy**: Correctness of technical details

---

## 5. Metadata and Context / 元数据和上下文

### 5.1 Code Context Metadata / 代码上下文元数据
- File path and location in repository
- Function/class/module names
- Dependencies and imports
- Related design patterns
- Code complexity metrics

### 5.2 Business Rules Metadata / 业务规则元数据
- Extracted business constraints
- Validation logic
- Workflow steps
- Domain-specific terminology

### 5.3 Repository Metadata / 仓库元数据
- Repository URL and version
- Programming language
- Framework and libraries used
- Project domain and type

---

## 6. Extensibility / 可扩展性

### 6.1 Plugin Architecture / 插件架构
The system supports plugins for:
- New programming languages
- Additional analysis techniques
- Custom Q&A generation strategies
- Domain-specific processors

### 6.2 Configuration / 配置
```yaml
# config.yaml
analysis:
  languages: ["python", "javascript", "java"]
  max_depth: 3
  include_tests: false

generation:
  qa_pairs_per_file: 5
  min_complexity: "simple"
  include_reasoning: true
  
quality:
  min_code_lines: 5
  max_code_lines: 50
  diversity_threshold: 0.7

output:
  format: "json"
  bilingual: true
  split_train_test: true
  test_ratio: 0.2
```

### 6.3 Future Enhancements / 未来增强
- LLM integration for enhanced generation
- Interactive refinement of generated data
- Automatic model training pipeline integration
- Multi-repository analysis
- Version control awareness
- Incremental updates

---

## 7. Usage Workflow / 使用流程

### 7.1 Scenario 1 Workflow / 场景1工作流
```
1. Clone target repository
2. Analyze code structure
3. Extract business logic and patterns
4. Generate Q&A pairs with code context
5. Create reasoning traces
6. Validate and ensure diversity
7. Export bilingual dataset
```

### 7.2 Scenario 2 Workflow / 场景2工作流
```
1. Load requirements specification
2. Analyze existing repository architecture
3. Identify similar patterns and components
4. Generate design solution
5. Create reasoning traces for decisions
6. Link to relevant code examples
7. Validate and export
```

---

## 8. Example Use Cases / 示例用例

### 8.1 Example 1: Flask API Q&A / Flask API问答
**Repository**: flask/flask  
**Generated Q&A**:
- Q: "How does Flask handle routing?"
- A: "Flask uses the @app.route() decorator..."
- Code Context: app.py lines 50-75
- Reasoning Trace: [routing decorator -> url_map -> dispatch]

### 8.2 Example 2: Microservices Design / 微服务设计
**Requirement**: "Design a scalable e-commerce system"  
**Repository**: Similar e-commerce projects  
**Generated Solution**: Microservices architecture with...
- Reasoning Trace: [monolithic rejected -> microservices chosen -> service boundaries defined]

---

## 9. Evaluation Criteria / 评估标准

### 9.1 Dataset Coverage / 数据集覆盖度
- ✓ Both scenarios implemented
- ✓ All metadata fields populated
- ✓ Diverse code examples
- ✓ Multiple complexity levels

### 9.2 Quality Metrics / 质量指标
- ✓ Logical reasoning traces
- ✓ Accurate code references
- ✓ Complete Q&A pairs
- ✓ Valid design solutions

### 9.3 System Completeness / 系统完整性
- ✓ All components implemented
- ✓ Extensible architecture
- ✓ Configuration support
- ✓ Error handling

### 9.4 Innovation / 创新性
- ✓ Automated reasoning trace generation
- ✓ Bilingual support
- ✓ Context-aware generation
- ✓ Quality assurance mechanisms
