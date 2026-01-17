"""
Design Solution Generator for Scenario 2
场景2的设计方案生成器

Generates architectural design solutions based on requirements.
根据需求生成架构设计方案。
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..dataset_generator.models import (
    DesignSolution, Requirement, Architecture, Component, DesignSolutionContent,
    CodeReference, DesignReasoningTrace, DecisionPoint, AlternativeOption,
    ChosenSolution, ArchitectureEvolution, ImplementationPhase
)
from ..analyzers.code_analyzer import CodeAnalyzer, ClassInfo, FunctionInfo
import logging

logger = logging.getLogger(__name__)


class DesignSolutionGenerator:
    """Generates design solutions based on code analysis / 基于代码分析生成设计方案"""
    
    # Sample requirements templates
    REQUIREMENT_TEMPLATES = {
        "en": {
            "api": {
                "title": "RESTful API Development",
                "description": "Build a scalable RESTful API service with CRUD operations",
                "constraints": ["Must be stateless", "Support JSON format", "Handle authentication"],
                "functional": ["Create resources", "Read resources", "Update resources", "Delete resources"],
                "non_functional": ["High availability", "Low latency", "Secure communications"]
            },
            "data_processing": {
                "title": "Data Processing Pipeline",
                "description": "Implement a data processing pipeline for batch operations",
                "constraints": ["Handle large datasets", "Fault tolerance", "Idempotent operations"],
                "functional": ["Data ingestion", "Transformation", "Validation", "Output generation"],
                "non_functional": ["Scalability", "Monitoring", "Error recovery"]
            },
            "web_app": {
                "title": "Web Application",
                "description": "Develop a modern web application with user management",
                "constraints": ["Browser compatibility", "Responsive design", "Security"],
                "functional": ["User registration", "Authentication", "Dashboard", "Settings"],
                "non_functional": ["Performance", "Usability", "Accessibility"]
            }
        },
        "zh": {
            "api": {
                "title": "RESTful API 开发",
                "description": "构建可扩展的 RESTful API 服务，支持 CRUD 操作",
                "constraints": ["必须是无状态的", "支持 JSON 格式", "处理身份验证"],
                "functional": ["创建资源", "读取资源", "更新资源", "删除资源"],
                "non_functional": ["高可用性", "低延迟", "安全通信"]
            },
            "data_processing": {
                "title": "数据处理管道",
                "description": "实现批处理操作的数据处理管道",
                "constraints": ["处理大数据集", "容错能力", "幂等操作"],
                "functional": ["数据摄取", "转换", "验证", "输出生成"],
                "non_functional": ["可扩展性", "监控", "错误恢复"]
            },
            "web_app": {
                "title": "Web 应用程序",
                "description": "开发具有用户管理功能的现代 Web 应用程序",
                "constraints": ["浏览器兼容性", "响应式设计", "安全性"],
                "functional": ["用户注册", "身份验证", "仪表板", "设置"],
                "non_functional": ["性能", "可用性", "可访问性"]
            }
        }
    }
    
    def __init__(self, analyzer: CodeAnalyzer, repo_name: str):
        """Initialize generator with analyzer"""
        self.analyzer = analyzer
        self.repo_name = repo_name
        
    def generate_design_solutions(self, max_solutions: int = 10,
                                  languages: List[str] = ["en", "zh"]) -> List[DesignSolution]:
        """Generate design solutions / 生成设计方案"""
        logger.info(f"Generating design solutions for {self.repo_name}")
        
        solutions = []
        
        # Determine project type based on code structure
        project_type = self._determine_project_type()
        
        for lang in languages:
            # Generate solution for detected project type
            solution = self._generate_solution(project_type, lang)
            if solution:
                solutions.append(solution)
            
            if len(solutions) >= max_solutions:
                break
        
        logger.info(f"Generated {len(solutions)} design solutions")
        return solutions
    
    def _determine_project_type(self) -> str:
        """Determine project type from code / 从代码确定项目类型"""
        # Check imports and patterns
        all_imports = []
        for module in self.analyzer.modules:
            all_imports.extend(module.imports)
        
        imports_str = ' '.join(all_imports).lower()
        
        if any(web in imports_str for web in ['flask', 'django', 'fastapi', 'requests']):
            return "api"
        elif any(data in imports_str for data in ['pandas', 'numpy', 'csv', 'json']):
            return "data_processing"
        elif any(web in imports_str for web in ['react', 'vue', 'angular', 'html']):
            return "web_app"
        else:
            return "api"  # Default
    
    def _generate_solution(self, project_type: str, language: str) -> Optional[DesignSolution]:
        """Generate a design solution / 生成设计方案"""
        try:
            # Create requirement
            req_template = self.REQUIREMENT_TEMPLATES[language].get(project_type, 
                                                                     self.REQUIREMENT_TEMPLATES[language]["api"])
            
            requirement = Requirement(
                title=req_template["title"],
                description=req_template["description"],
                constraints=req_template["constraints"],
                functional_requirements=req_template["functional"],
                non_functional_requirements=req_template["non_functional"]
            )
            
            # Analyze existing architecture
            architecture = self._analyze_architecture(project_type, language)
            
            # Generate design solution content
            design_solution = DesignSolutionContent(
                overview=self._generate_overview(project_type, language),
                architecture=architecture,
                implementation_plan=self._generate_implementation_plan(project_type, language)
            )
            
            # Find code references
            code_references = self._find_code_references(project_type, language)
            
            # Generate reasoning trace
            reasoning_trace = self._generate_reasoning_trace(project_type, architecture, language)
            
            # Create metadata
            metadata = {
                "repository": self.repo_name,
                "generated_at": datetime.now().isoformat(),
                "complexity": "medium",
                "domain": project_type,
                "tags": [project_type, "architecture", "design"]
            }
            
            return DesignSolution(
                id=str(uuid.uuid4()),
                requirement=requirement,
                design_solution=design_solution,
                code_references=code_references,
                reasoning_trace=reasoning_trace,
                language=language,
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to generate design solution: {e}")
            return None
    
    def _analyze_architecture(self, project_type: str, language: str) -> Architecture:
        """Analyze and generate architecture / 分析并生成架构"""
        components = []
        
        if language == "en":
            if project_type == "api":
                components = [
                    Component(
                        name="API Gateway",
                        responsibility="Handle incoming HTTP requests and route to appropriate handlers",
                        interfaces=["REST endpoints", "Authentication middleware"],
                        dependencies=["Request Handler", "Authentication Service"]
                    ),
                    Component(
                        name="Request Handler",
                        responsibility="Process business logic for each endpoint",
                        interfaces=["CRUD operations", "Validation"],
                        dependencies=["Data Access Layer", "Business Logic"]
                    ),
                    Component(
                        name="Data Access Layer",
                        responsibility="Manage database operations and data persistence",
                        interfaces=["ORM/Database queries"],
                        dependencies=["Database"]
                    )
                ]
                style = "Layered Architecture"
                data_flow = "Client -> API Gateway -> Request Handler -> Data Access Layer -> Database"
                tech_stack = {
                    "languages": ["Python"],
                    "frameworks": ["Flask", "SQLAlchemy"],
                    "databases": ["PostgreSQL"],
                    "infrastructure": ["Docker", "Nginx"]
                }
            
            elif project_type == "data_processing":
                components = [
                    Component(
                        name="Data Ingestion",
                        responsibility="Collect data from various sources",
                        interfaces=["File readers", "API connectors"],
                        dependencies=["Data Source"]
                    ),
                    Component(
                        name="Processing Engine",
                        responsibility="Transform and validate data",
                        interfaces=["Transformation pipeline", "Validation rules"],
                        dependencies=["Data Ingestion", "Data Storage"]
                    ),
                    Component(
                        name="Data Storage",
                        responsibility="Store processed results",
                        interfaces=["Write operations"],
                        dependencies=["Storage System"]
                    )
                ]
                style = "Pipeline Architecture"
                data_flow = "Source -> Ingestion -> Processing -> Validation -> Storage"
                tech_stack = {
                    "languages": ["Python"],
                    "frameworks": ["Pandas", "NumPy"],
                    "databases": ["PostgreSQL", "Redis"],
                    "infrastructure": ["Apache Airflow"]
                }
            
            else:  # web_app
                components = [
                    Component(
                        name="Frontend",
                        responsibility="User interface and client-side logic",
                        interfaces=["UI components", "State management"],
                        dependencies=["Backend API"]
                    ),
                    Component(
                        name="Backend API",
                        responsibility="Server-side logic and data management",
                        interfaces=["REST/GraphQL API"],
                        dependencies=["Database", "Authentication"]
                    ),
                    Component(
                        name="Authentication",
                        responsibility="User authentication and authorization",
                        interfaces=["Login", "JWT tokens"],
                        dependencies=["User Database"]
                    )
                ]
                style = "Client-Server Architecture"
                data_flow = "User -> Frontend -> Backend API -> Database"
                tech_stack = {
                    "languages": ["JavaScript", "Python"],
                    "frameworks": ["React", "Flask"],
                    "databases": ["PostgreSQL"],
                    "infrastructure": ["Docker", "Kubernetes"]
                }
        
        else:  # zh
            if project_type == "api":
                components = [
                    Component(
                        name="API 网关",
                        responsibility="处理传入的 HTTP 请求并路由到适当的处理器",
                        interfaces=["REST 端点", "身份验证中间件"],
                        dependencies=["请求处理器", "身份验证服务"]
                    ),
                    Component(
                        name="请求处理器",
                        responsibility="处理每个端点的业务逻辑",
                        interfaces=["CRUD 操作", "验证"],
                        dependencies=["数据访问层", "业务逻辑"]
                    ),
                    Component(
                        name="数据访问层",
                        responsibility="管理数据库操作和数据持久化",
                        interfaces=["ORM/数据库查询"],
                        dependencies=["数据库"]
                    )
                ]
                style = "分层架构"
                data_flow = "客户端 -> API 网关 -> 请求处理器 -> 数据访问层 -> 数据库"
                tech_stack = {
                    "languages": ["Python"],
                    "frameworks": ["Flask", "SQLAlchemy"],
                    "databases": ["PostgreSQL"],
                    "infrastructure": ["Docker", "Nginx"]
                }
            
            elif project_type == "data_processing":
                components = [
                    Component(
                        name="数据摄取",
                        responsibility="从各种来源收集数据",
                        interfaces=["文件读取器", "API 连接器"],
                        dependencies=["数据源"]
                    ),
                    Component(
                        name="处理引擎",
                        responsibility="转换和验证数据",
                        interfaces=["转换管道", "验证规则"],
                        dependencies=["数据摄取", "数据存储"]
                    ),
                    Component(
                        name="数据存储",
                        responsibility="存储处理结果",
                        interfaces=["写操作"],
                        dependencies=["存储系统"]
                    )
                ]
                style = "管道架构"
                data_flow = "数据源 -> 摄取 -> 处理 -> 验证 -> 存储"
                tech_stack = {
                    "languages": ["Python"],
                    "frameworks": ["Pandas", "NumPy"],
                    "databases": ["PostgreSQL", "Redis"],
                    "infrastructure": ["Apache Airflow"]
                }
            
            else:  # web_app
                components = [
                    Component(
                        name="前端",
                        responsibility="用户界面和客户端逻辑",
                        interfaces=["UI 组件", "状态管理"],
                        dependencies=["后端 API"]
                    ),
                    Component(
                        name="后端 API",
                        responsibility="服务器端逻辑和数据管理",
                        interfaces=["REST/GraphQL API"],
                        dependencies=["数据库", "身份验证"]
                    ),
                    Component(
                        name="身份验证",
                        responsibility="用户身份验证和授权",
                        interfaces=["登录", "JWT 令牌"],
                        dependencies=["用户数据库"]
                    )
                ]
                style = "客户端-服务器架构"
                data_flow = "用户 -> 前端 -> 后端 API -> 数据库"
                tech_stack = {
                    "languages": ["JavaScript", "Python"],
                    "frameworks": ["React", "Flask"],
                    "databases": ["PostgreSQL"],
                    "infrastructure": ["Docker", "Kubernetes"]
                }
        
        return Architecture(
            style=style,
            components=components,
            data_flow=data_flow,
            technology_stack=tech_stack
        )
    
    def _generate_overview(self, project_type: str, language: str) -> str:
        """Generate solution overview / 生成方案概述"""
        if language == "en":
            overviews = {
                "api": "This design proposes a layered architecture for a RESTful API service that provides clear separation of concerns, scalability, and maintainability. The architecture follows industry best practices and can handle high-volume traffic.",
                "data_processing": "This design presents a pipeline-based architecture for data processing that ensures data quality, fault tolerance, and scalability. The pipeline approach allows for easy extension and monitoring of each processing stage.",
                "web_app": "This design describes a modern client-server architecture for a web application that provides excellent user experience, security, and performance. The architecture separates frontend and backend concerns while enabling seamless integration."
            }
        else:
            overviews = {
                "api": "此设计提出了 RESTful API 服务的分层架构，提供清晰的关注点分离、可扩展性和可维护性。该架构遵循行业最佳实践，可以处理大量流量。",
                "data_processing": "此设计提出了基于管道的数据处理架构，确保数据质量、容错能力和可扩展性。管道方法允许轻松扩展和监控每个处理阶段。",
                "web_app": "此设计描述了 Web 应用程序的现代客户端-服务器架构，提供出色的用户体验、安全性和性能。该架构分离了前端和后端关注点，同时实现无缝集成。"
            }
        
        return overviews.get(project_type, overviews["api"])
    
    def _generate_implementation_plan(self, project_type: str, language: str) -> List[ImplementationPhase]:
        """Generate implementation plan / 生成实施计划"""
        if language == "en":
            return [
                ImplementationPhase(
                    phase=1,
                    description="Setup and Infrastructure",
                    tasks=["Setup development environment", "Configure version control", "Setup CI/CD pipeline"],
                    estimated_effort="1-2 weeks"
                ),
                ImplementationPhase(
                    phase=2,
                    description="Core Implementation",
                    tasks=["Implement core components", "Setup database schema", "Create API endpoints"],
                    estimated_effort="3-4 weeks"
                ),
                ImplementationPhase(
                    phase=3,
                    description="Testing and Deployment",
                    tasks=["Write unit tests", "Integration testing", "Deploy to production"],
                    estimated_effort="2-3 weeks"
                )
            ]
        else:
            return [
                ImplementationPhase(
                    phase=1,
                    description="设置和基础设施",
                    tasks=["设置开发环境", "配置版本控制", "设置 CI/CD 管道"],
                    estimated_effort="1-2 周"
                ),
                ImplementationPhase(
                    phase=2,
                    description="核心实现",
                    tasks=["实现核心组件", "设置数据库架构", "创建 API 端点"],
                    estimated_effort="3-4 周"
                ),
                ImplementationPhase(
                    phase=3,
                    description="测试和部署",
                    tasks=["编写单元测试", "集成测试", "部署到生产环境"],
                    estimated_effort="2-3 周"
                )
            ]
    
    def _find_code_references(self, project_type: str, language: str) -> Dict[str, List[CodeReference]]:
        """Find similar code patterns / 查找相似代码模式"""
        references = {"similar_patterns": []}
        
        # Find relevant functions/classes
        for func in self.analyzer.all_functions[:3]:
            code_snippet = '\n'.join(func.body_lines[:10])  # First 10 lines
            
            if language == "en":
                explanation = f"This function demonstrates a common pattern used in {project_type} implementations."
            else:
                explanation = f"此函数展示了 {project_type} 实现中使用的常见模式。"
            
            references["similar_patterns"].append(
                CodeReference(
                    file_path=func.file_path,
                    pattern_name=f"{func.name} pattern",
                    code_snippet=code_snippet,
                    explanation=explanation
                )
            )
        
        return references
    
    def _generate_reasoning_trace(self, project_type: str, architecture: Architecture, 
                                  language: str) -> DesignReasoningTrace:
        """Generate design reasoning trace / 生成设计推理轨迹"""
        if language == "en":
            decision_points = [
                DecisionPoint(
                    decision=f"Choose {architecture.style} as the architectural pattern",
                    rationale=f"This pattern best fits the requirements for {project_type} because it provides the right balance of simplicity and scalability.",
                    alternatives_considered=[
                        AlternativeOption(
                            option="Microservices Architecture",
                            pros=["Better scalability", "Independent deployment"],
                            cons=["Higher complexity", "More infrastructure overhead"],
                            rejection_reason="Too complex for current requirements and team size"
                        ),
                        AlternativeOption(
                            option="Monolithic Architecture",
                            pros=["Simpler to develop", "Easier debugging"],
                            cons=["Harder to scale", "Tight coupling"],
                            rejection_reason="Does not meet scalability requirements"
                        )
                    ],
                    chosen_solution=ChosenSolution(
                        description=architecture.style,
                        justification=f"Provides the right balance between simplicity and scalability for {project_type}",
                        trade_offs=["Moderate complexity", "Good scalability", "Clear boundaries"]
                    )
                )
            ]
            
            evolution = [
                ArchitectureEvolution(
                    stage="Initial Design",
                    rationale="Start with simple architecture that meets current requirements"
                ),
                ArchitectureEvolution(
                    stage="Future Enhancement",
                    rationale="Can evolve to microservices if scalability demands increase"
                )
            ]
        else:
            decision_points = [
                DecisionPoint(
                    decision=f"选择 {architecture.style} 作为架构模式",
                    rationale=f"此模式最适合 {project_type} 的需求，因为它提供了简单性和可扩展性之间的正确平衡。",
                    alternatives_considered=[
                        AlternativeOption(
                            option="微服务架构",
                            pros=["更好的可扩展性", "独立部署"],
                            cons=["更高的复杂性", "更多的基础设施开销"],
                            rejection_reason="对于当前需求和团队规模来说太复杂"
                        ),
                        AlternativeOption(
                            option="单体架构",
                            pros=["开发更简单", "调试更容易"],
                            cons=["更难扩展", "紧耦合"],
                            rejection_reason="不满足可扩展性要求"
                        )
                    ],
                    chosen_solution=ChosenSolution(
                        description=architecture.style,
                        justification=f"为 {project_type} 提供简单性和可扩展性之间的正确平衡",
                        trade_offs=["中等复杂度", "良好的可扩展性", "清晰的边界"]
                    )
                )
            ]
            
            evolution = [
                ArchitectureEvolution(
                    stage="初始设计",
                    rationale="从满足当前需求的简单架构开始"
                ),
                ArchitectureEvolution(
                    stage="未来增强",
                    rationale="如果可扩展性需求增加，可以演进为微服务"
                )
            ]
        
        return DesignReasoningTrace(
            decision_points=decision_points,
            architecture_evolution=evolution
        )
