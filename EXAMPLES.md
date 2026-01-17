# Sample Dataset Examples
# 数据集示例

This document showcases sample outputs from the training dataset generator.
本文档展示训练数据集生成器的示例输出。

## Scenario 1: Q&A Pair Example / 场景1：问答对示例

### English Example / 英文示例

```json
{
  "id": "qa-001",
  "type": "qa_pair",
  "language": "en",
  "question": "What does the function `analyze_repository` do?",
  "answer": "The function `analyze_repository` analyzes the code repository by parsing Python files, extracting functions, classes, and their metadata. It accepts an optional max_files parameter to limit the analysis scope. The function populates the analyzer's internal structures with discovered code elements.",
  "code_context": {
    "file_path": "src/dataset_generator/core.py",
    "function_name": "analyze_repository",
    "class_name": null,
    "code_snippet": "def analyze_repository(self, max_files: Optional[int] = None) -> None:\n    \"\"\"Analyze the repository\"\"\"\n    logger.info(\"Starting repository analysis...\")\n    self.analyzer.analyze(max_files=max_files)\n    self.qa_generator = QAGenerator(self.analyzer, self.repo_name)\n    self.design_generator = DesignSolutionGenerator(self.analyzer, self.repo_name)",
    "start_line": 45,
    "end_line": 58
  },
  "business_rules": [
    "Must initialize analyzer before calling this method",
    "Initializes generators after analysis completes",
    "Supports limiting analysis scope through max_files parameter"
  ],
  "reasoning_trace": {
    "steps": [
      {
        "step_number": 1,
        "description": "Analyze function signature",
        "code_reference": "def analyze_repository(self, max_files: Optional[int] = None)",
        "reasoning": "The function accepts an optional max_files parameter of type Optional[int], which allows callers to limit the number of files to analyze. This provides flexibility for large repositories."
      },
      {
        "step_number": 2,
        "description": "Review function documentation",
        "code_reference": "docstring",
        "reasoning": "The docstring states 'Analyze the repository', indicating this is the primary method for initiating code analysis."
      },
      {
        "step_number": 3,
        "description": "Examine implementation details",
        "code_reference": "lines 45-58",
        "reasoning": "The implementation calls analyzer.analyze() to perform the actual analysis, then initializes the QA and design generators with the results. This follows a two-phase pattern: analyze first, then prepare generators."
      },
      {
        "step_number": 4,
        "description": "Identify side effects",
        "code_reference": "self.qa_generator = ..., self.design_generator = ...",
        "reasoning": "The method has side effects by modifying instance variables. This state change enables subsequent dataset generation calls."
      }
    ],
    "conclusion": "The analyze_repository method serves as the initialization phase for dataset generation, performing code analysis and preparing the necessary generators for subsequent operations."
  },
  "metadata": {
    "repository": "local-training-dataset-generator",
    "generated_at": "2026-01-17T06:00:00.000000",
    "complexity": "medium",
    "tags": ["analysis", "initialization", "repository"]
  }
}
```

### Chinese Example / 中文示例

```json
{
  "id": "qa-002",
  "type": "qa_pair",
  "language": "zh",
  "question": "函数 `generate_qa_pairs` 的作用是什么？",
  "answer": "函数 `generate_qa_pairs` 用于生成问答对数据集。它接受 max_pairs（每种语言的最大问答对数）和 languages（语言列表）参数。该函数从分析的代码中提取函数和类信息，为每个语言生成相应的问答对，包括代码上下文、业务规则和推理轨迹。",
  "code_context": {
    "file_path": "src/generators/qa_generator.py",
    "function_name": "generate_qa_pairs",
    "class_name": "QAGenerator",
    "code_snippet": "def generate_qa_pairs(self, max_pairs: int = 50, \n                      languages: List[str] = [\"en\", \"zh\"]) -> List[QAPair]:\n    \"\"\"生成问答对\"\"\"\n    logger.info(f\"Generating Q&A pairs for {self.repo_name}\")\n    qa_pairs = []\n    for func in self.analyzer.all_functions[:max_pairs // 2]:\n        for lang in languages:\n            qa = self._generate_function_qa(func, lang)",
    "start_line": 40,
    "end_line": 68
  },
  "business_rules": [
    "为每种指定语言生成问答对",
    "从函数和类中提取信息",
    "包含完整的推理轨迹"
  ],
  "reasoning_trace": {
    "steps": [
      {
        "step_number": 1,
        "description": "分析函数签名",
        "code_reference": "def generate_qa_pairs(self, max_pairs: int = 50, languages: List[str] = [\"en\", \"zh\"])",
        "reasoning": "函数接受 max_pairs 和 languages 参数，允许调用者控制生成的数量和语言。"
      },
      {
        "step_number": 2,
        "description": "查看函数文档",
        "code_reference": "docstring",
        "reasoning": "文档字符串说明：'生成问答对'，明确了函数的主要目的。"
      },
      {
        "step_number": 3,
        "description": "检查实现细节",
        "code_reference": "第 40-68 行",
        "reasoning": "实现遍历分析器中的函数和类，为每种语言生成问答对。采用双重循环确保多语言支持。"
      }
    ],
    "conclusion": "generate_qa_pairs 是场景1数据集生成的核心方法，实现了从代码到问答对的自动化转换，并支持多语言输出。"
  },
  "metadata": {
    "repository": "local-training-dataset-generator",
    "generated_at": "2026-01-17T06:00:00.000000",
    "complexity": "medium",
    "tags": ["生成", "问答", "多语言"]
  }
}
```

## Scenario 2: Design Solution Example / 场景2：设计方案示例

### English Example / 英文示例

```json
{
  "id": "design-001",
  "type": "design_solution",
  "language": "en",
  "requirement": {
    "title": "RESTful API Development",
    "description": "Build a scalable RESTful API service with CRUD operations, authentication, and data validation",
    "constraints": [
      "Must be stateless",
      "Support JSON format",
      "Handle authentication and authorization",
      "Provide clear error messages"
    ],
    "functional_requirements": [
      "Create resources with validation",
      "Read resources with filtering and pagination",
      "Update resources atomically",
      "Delete resources with cascading effects",
      "User authentication and session management"
    ],
    "non_functional_requirements": [
      "High availability (99.9% uptime)",
      "Low latency (< 200ms response time)",
      "Secure communications (HTTPS, JWT)",
      "Horizontal scalability",
      "Comprehensive logging and monitoring"
    ]
  },
  "design_solution": {
    "overview": "This design proposes a layered architecture for a RESTful API service that provides clear separation of concerns, scalability, and maintainability. The architecture follows industry best practices and can handle high-volume traffic while maintaining security and data integrity.",
    "architecture": {
      "style": "Layered Architecture",
      "components": [
        {
          "name": "API Gateway",
          "responsibility": "Handle incoming HTTP requests, route to appropriate handlers, apply rate limiting, and manage CORS policies",
          "interfaces": [
            "REST endpoints (/api/v1/*)",
            "Authentication middleware",
            "Request validation middleware",
            "Rate limiting middleware"
          ],
          "dependencies": [
            "Request Handler",
            "Authentication Service",
            "Logging Service"
          ]
        },
        {
          "name": "Request Handler",
          "responsibility": "Process business logic for each endpoint, validate inputs, orchestrate data operations",
          "interfaces": [
            "CRUD operations interface",
            "Business validation interface",
            "Transaction management"
          ],
          "dependencies": [
            "Data Access Layer",
            "Business Logic Services",
            "Cache Service"
          ]
        },
        {
          "name": "Data Access Layer",
          "responsibility": "Manage database operations, implement repository pattern, handle transactions",
          "interfaces": [
            "ORM/Database queries",
            "Transaction boundaries",
            "Connection pooling"
          ],
          "dependencies": [
            "PostgreSQL Database",
            "Redis Cache"
          ]
        },
        {
          "name": "Authentication Service",
          "responsibility": "Handle user authentication, generate and validate JWT tokens, manage sessions",
          "interfaces": [
            "Login/logout endpoints",
            "Token validation",
            "Permission checks"
          ],
          "dependencies": [
            "User Database",
            "Token Store (Redis)"
          ]
        }
      ],
      "data_flow": "Client -> API Gateway (auth/validation) -> Request Handler (business logic) -> Data Access Layer (persistence) -> Database. Responses flow back through the same layers with appropriate transformations.",
      "technology_stack": {
        "languages": ["Python 3.9+"],
        "frameworks": ["Flask/FastAPI", "SQLAlchemy", "Pydantic"],
        "databases": ["PostgreSQL", "Redis"],
        "infrastructure": ["Docker", "Nginx", "Kubernetes"]
      }
    },
    "implementation_plan": [
      {
        "phase": 1,
        "description": "Setup and Infrastructure",
        "tasks": [
          "Setup development environment and tooling",
          "Configure version control and branching strategy",
          "Setup CI/CD pipeline with automated testing",
          "Create Docker containers and compose files",
          "Initialize database schema and migrations"
        ],
        "estimated_effort": "1-2 weeks"
      },
      {
        "phase": 2,
        "description": "Core Implementation",
        "tasks": [
          "Implement API Gateway with routing",
          "Develop authentication and authorization",
          "Create data models and ORM mappings",
          "Implement CRUD endpoints with validation",
          "Add business logic layer",
          "Integrate caching layer"
        ],
        "estimated_effort": "3-4 weeks"
      },
      {
        "phase": 3,
        "description": "Testing and Quality Assurance",
        "tasks": [
          "Write comprehensive unit tests (80%+ coverage)",
          "Implement integration tests",
          "Perform load testing and optimization",
          "Security audit and penetration testing",
          "Documentation and API specification"
        ],
        "estimated_effort": "2-3 weeks"
      },
      {
        "phase": 4,
        "description": "Deployment and Monitoring",
        "tasks": [
          "Deploy to staging environment",
          "Configure monitoring and alerting",
          "Setup log aggregation",
          "Perform production deployment",
          "Post-deployment validation"
        ],
        "estimated_effort": "1 week"
      }
    ]
  },
  "code_references": {
    "similar_patterns": [
      {
        "file_path": "src/dataset_generator/core.py",
        "pattern_name": "Repository pattern",
        "code_snippet": "class DatasetGenerator:\n    def __init__(self, repo_path: str, repo_name: Optional[str] = None):\n        self.repo_path = Path(repo_path)\n        self.repo_name = repo_name or self.repo_path.name\n        self.analyzer = CodeAnalyzer(str(self.repo_path))",
        "explanation": "Demonstrates initialization pattern with dependency injection, similar to how API services should be structured"
      }
    ],
    "reusable_components": [
      "Authentication middleware",
      "Request validation decorators",
      "Error handling utilities"
    ]
  },
  "reasoning_trace": {
    "decision_points": [
      {
        "decision": "Choose Layered Architecture as the architectural pattern",
        "rationale": "Layered architecture provides clear separation of concerns, makes testing easier, and allows each layer to be developed and maintained independently. It's well-understood by development teams and has proven scalability.",
        "alternatives_considered": [
          {
            "option": "Microservices Architecture",
            "pros": [
              "Better scalability for individual services",
              "Independent deployment of services",
              "Technology diversity",
              "Fault isolation"
            ],
            "cons": [
              "Higher operational complexity",
              "More infrastructure overhead",
              "Distributed system challenges",
              "Increased latency due to network calls"
            ],
            "rejection_reason": "Too complex for current requirements and team size. The added operational overhead outweighs benefits for a single API service."
          },
          {
            "option": "Monolithic Architecture",
            "pros": [
              "Simpler to develop initially",
              "Easier debugging",
              "Lower operational overhead",
              "No distributed system complexity"
            ],
            "cons": [
              "Harder to scale horizontally",
              "Tight coupling between components",
              "Longer deployment cycles",
              "Limited technology choices"
            ],
            "rejection_reason": "Does not meet scalability requirements. As the system grows, it would become increasingly difficult to maintain and scale."
          }
        ],
        "chosen_solution": {
          "description": "Layered Architecture with clear boundaries between API Gateway, Business Logic, and Data Access layers",
          "justification": "Provides the right balance between simplicity and scalability. Allows horizontal scaling while maintaining manageable complexity. Each layer can be optimized independently, and the architecture can evolve to microservices if needed.",
          "trade_offs": [
            "Moderate complexity compared to monolith",
            "Good scalability without microservices overhead",
            "Clear boundaries aid in testing and maintenance",
            "Can evolve to microservices incrementally"
          ]
        }
      },
      {
        "decision": "Use PostgreSQL as primary database",
        "rationale": "PostgreSQL provides robust ACID compliance, excellent JSON support for flexible schemas, strong performance, and mature ecosystem.",
        "alternatives_considered": [
          {
            "option": "MongoDB",
            "pros": ["Schema flexibility", "Horizontal scaling", "JSON-native"],
            "cons": ["Eventually consistent", "Less mature transactions", "Query complexity"],
            "rejection_reason": "ACID compliance is critical for data integrity in CRUD operations"
          }
        ],
        "chosen_solution": {
          "description": "PostgreSQL with Redis for caching",
          "justification": "Combines strong consistency with performance through caching layer",
          "trade_offs": ["More complex setup than NoSQL", "Excellent data integrity", "Proven at scale"]
        }
      }
    ],
    "architecture_evolution": [
      {
        "stage": "Initial Design (Current)",
        "rationale": "Start with layered architecture that meets current requirements while maintaining simplicity and manageable complexity"
      },
      {
        "stage": "Scale-out Phase",
        "rationale": "Add horizontal scaling by deploying multiple instances behind load balancer, utilize Redis for distributed caching"
      },
      {
        "stage": "Microservices Evolution (Future)",
        "rationale": "If scalability demands increase significantly, can extract high-traffic components into separate microservices while maintaining layered structure within each service"
      }
    ]
  },
  "metadata": {
    "repository": "local-training-dataset-generator",
    "generated_at": "2026-01-17T06:00:00.000000",
    "complexity": "medium",
    "domain": "api",
    "tags": ["api", "architecture", "design", "rest", "layered"]
  }
}
```

## Key Features Demonstrated / 展示的关键特性

1. **Complete Code Context / 完整代码上下文**
   - File paths and line numbers
   - Actual code snippets
   - Function and class names

2. **Business Rules / 业务规则**
   - Extracted validation logic
   - Constraints and requirements
   - Best practices

3. **Reasoning Traces / 推理轨迹**
   - Step-by-step analysis
   - Decision rationale
   - Alternative considerations

4. **Bilingual Support / 双语支持**
   - Parallel Chinese and English versions
   - Context-aware translations
   - Cultural adaptations

5. **Rich Metadata / 丰富元数据**
   - Complexity levels
   - Tags for categorization
   - Timestamps and versioning

## Usage Statistics / 使用统计

From the simple example generation:
- **Total Items**: 8 (6 Q&A pairs + 2 design solutions)
- **Languages**: English and Chinese
- **Validation Rate**: 100%
- **Diversity Score**: 74%
- **Complexity Distribution**: Simple, Medium, Complex

## Quality Metrics / 质量指标

- ✅ All required fields present
- ✅ Code references are accurate
- ✅ Reasoning traces are logical and complete
- ✅ Bilingual consistency maintained
- ✅ Metadata is comprehensive
