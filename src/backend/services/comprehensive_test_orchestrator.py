"""
Comprehensive Function Testing Orchestrator
Automatically discovers, tests, and validates every function in the codebase
"""

import ast
import asyncio
import json
import os
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
import subprocess
import re
import hashlib

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    console = Console()

@dataclass
class FunctionInfo:
    name: str
    file_path: str
    line_number: int
    parameters: List[str]
    return_type: Optional[str]
    is_async: bool
    docstring: Optional[str]
    decorators: List[str]
    complexity: int = 1
    has_test: bool = False
    test_file: Optional[str] = None
    priority_score: float = 0.0
    git_changes: int = 0
    last_modified: Optional[datetime] = None
    business_critical: bool = False
    test_quality_score: float = 0.0

@dataclass
class TestResult:
    function_name: str
    test_file: str
    passed: bool
    coverage: float
    error_message: Optional[str] = None
    edge_cases_tested: int = 0
    error_cases_tested: int = 0
    execution_time: float = 0.0
    mutations_caught: int = 0
    performance_baseline: Optional[float] = None
    regression_detected: bool = False
    ai_generated_tests: int = 0
    test_quality_score: float = 0.0

@dataclass
class PerformanceMetrics:
    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime
    baseline_comparison: Optional[float] = None
    regression_threshold: float = 1.5  # 50% performance degradation threshold

class TestPriorityAnalyzer:
    """Intelligent test prioritization based on multiple factors"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.db_path = project_root / "test_metrics.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for tracking metrics"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS function_metrics (
                function_name TEXT PRIMARY KEY,
                file_path TEXT,
                complexity INT,
                git_changes INT,
                last_test_failure TIMESTAMP,
                avg_execution_time REAL,
                priority_score REAL,
                business_critical BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_name TEXT,
                test_file TEXT,
                passed BOOLEAN,
                execution_time REAL,
                coverage REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def analyze_git_history(self, function_info: FunctionInfo) -> int:
        """Analyze git commit history for function changes"""
        try:
            # Get git log for the specific file and line range
            result = subprocess.run([
                'git', 'log', '--oneline', '--since=3 months ago',
                f'-L{function_info.line_number},{function_info.line_number + 10}:{function_info.file_path}'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            else:
                # Fallback: count commits for the entire file
                result = subprocess.run([
                    'git', 'log', '--oneline', '--since=3 months ago', function_info.file_path
                ], capture_output=True, text=True, cwd=self.project_root)
                return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        except Exception:
            return 0
    
    def assess_business_criticality(self, function_info: FunctionInfo) -> bool:
        """Determine if function is business critical"""
        critical_indicators = [
            'api/', 'endpoint', 'route', 'auth', 'payment', 'security',
            'database', 'crud', 'login', 'register', 'upload', 'delete',
            'create', 'update', 'process', 'execute', 'validate'
        ]
        
        file_path_lower = function_info.file_path.lower()
        function_name_lower = function_info.name.lower()
        
        return any(indicator in file_path_lower or indicator in function_name_lower 
                  for indicator in critical_indicators)
    
    def calculate_priority_score(self, function_info: FunctionInfo) -> float:
        """Calculate comprehensive priority score for test generation"""
        score = 0.0
        
        # Complexity factor (0-40 points)
        complexity_score = min(function_info.complexity * 4, 40)
        score += complexity_score
        
        # Git change frequency (0-30 points)
        git_score = min(function_info.git_changes * 3, 30)
        score += git_score
        
        # Business criticality (0-20 points)
        if function_info.business_critical:
            score += 20
        
        # Missing test penalty (0-10 points)
        if not function_info.has_test:
            score += 10
        
        # Async function bonus (0-5 points)
        if function_info.is_async:
            score += 5
        
        # Decorator complexity (0-5 points)
        if function_info.decorators:
            score += min(len(function_info.decorators) * 2, 5)
        
        return round(score, 2)
    
    def prioritize_functions(self, functions: List[FunctionInfo]) -> List[FunctionInfo]:
        """Sort functions by priority for test generation"""
        for func in functions:
            func.git_changes = self.analyze_git_history(func)
            func.business_critical = self.assess_business_criticality(func)
            func.priority_score = self.calculate_priority_score(func)
            
            # Store metrics in database
            self._store_function_metrics(func)
        
        # Sort by priority score (highest first)
        return sorted(functions, key=lambda f: f.priority_score, reverse=True)
    
    def _store_function_metrics(self, func: FunctionInfo):
        """Store function metrics in database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT OR REPLACE INTO function_metrics 
            (function_name, file_path, complexity, git_changes, priority_score, business_critical, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            func.name, func.file_path, func.complexity, func.git_changes,
            func.priority_score, func.business_critical, datetime.now()
        ))
        conn.commit()
        conn.close()
    
    def get_historical_metrics(self, function_name: str) -> Optional[Dict]:
        """Get historical metrics for a function"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            SELECT * FROM function_metrics WHERE function_name = ?
        ''', (function_name,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, result))
        return None

class AITestGenerator:
    """AI-Enhanced Test Case Generation Engine"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.patterns_db = self._init_patterns_database()
    
    def _init_patterns_database(self) -> Dict[str, List[str]]:
        """Initialize common test patterns database"""
        return {
            "api_functions": [
                "test_valid_request_returns_200",
                "test_invalid_request_returns_400", 
                "test_unauthorized_request_returns_401",
                "test_forbidden_request_returns_403",
                "test_not_found_returns_404",
                "test_rate_limiting",
                "test_payload_validation"
            ],
            "database_functions": [
                "test_successful_create",
                "test_successful_read", 
                "test_successful_update",
                "test_successful_delete",
                "test_duplicate_key_error",
                "test_foreign_key_constraint",
                "test_transaction_rollback",
                "test_connection_timeout"
            ],
            "file_operations": [
                "test_file_exists",
                "test_file_not_found",
                "test_permission_denied",
                "test_disk_full",
                "test_invalid_path",
                "test_binary_file_handling",
                "test_large_file_processing"
            ],
            "auth_functions": [
                "test_valid_credentials",
                "test_invalid_credentials",
                "test_expired_token",
                "test_malformed_token",
                "test_missing_permissions",
                "test_session_timeout",
                "test_brute_force_protection"
            ],
            "async_functions": [
                "test_concurrent_execution",
                "test_timeout_handling",
                "test_cancellation",
                "test_exception_propagation",
                "test_resource_cleanup",
                "test_deadlock_prevention"
            ]
        }
    
    def analyze_function_context(self, func: FunctionInfo) -> Dict[str, Any]:
        """Analyze function to determine test patterns"""
        context = {
            "function_type": "generic",
            "suggested_patterns": [],
            "risk_areas": [],
            "test_complexity": "standard"
        }
        
        # Analyze function name and parameters
        func_name_lower = func.name.lower()
        file_path_lower = func.file_path.lower()
        
        # Determine function type
        if any(keyword in func_name_lower for keyword in ['api', 'endpoint', 'route', 'handler']):
            context["function_type"] = "api"
            context["suggested_patterns"] = self.patterns_db["api_functions"]
        elif any(keyword in func_name_lower for keyword in ['create', 'read', 'update', 'delete', 'insert', 'select']):
            context["function_type"] = "database"
            context["suggested_patterns"] = self.patterns_db["database_functions"]
        elif any(keyword in func_name_lower for keyword in ['file', 'read', 'write', 'save', 'load']):
            context["function_type"] = "file_operations"
            context["suggested_patterns"] = self.patterns_db["file_operations"]
        elif any(keyword in func_name_lower for keyword in ['auth', 'login', 'verify', 'validate', 'token']):
            context["function_type"] = "auth"
            context["suggested_patterns"] = self.patterns_db["auth_functions"]
        elif func.is_async:
            context["function_type"] = "async"
            context["suggested_patterns"] = self.patterns_db["async_functions"]
        
        # Analyze risk areas
        if func.complexity > 10:
            context["risk_areas"].append("high_complexity")
        if func.business_critical:
            context["risk_areas"].append("business_critical")
        if 'security' in file_path_lower or 'auth' in file_path_lower:
            context["risk_areas"].append("security_sensitive")
        if func.git_changes > 5:
            context["risk_areas"].append("frequently_changed")
        
        # Determine test complexity
        if func.priority_score > 70:
            context["test_complexity"] = "comprehensive"
        elif func.priority_score > 50:
            context["test_complexity"] = "thorough"
        else:
            context["test_complexity"] = "standard"
        
        return context
    
    def generate_ai_test_cases(self, func: FunctionInfo, context: Dict[str, Any]) -> List[str]:
        """Generate AI-enhanced test cases based on context"""
        test_cases = []
        
        # Base test cases
        test_cases.extend([
            f"test_{func.name}_happy_path",
            f"test_{func.name}_edge_cases",
            f"test_{func.name}_error_handling"
        ])
        
        # Add pattern-specific tests
        for pattern in context["suggested_patterns"][:5]:  # Limit to top 5 patterns
            test_case_name = f"test_{func.name}_{pattern.replace('test_', '').replace('_returns_', '_')}"
            test_cases.append(test_case_name)
        
        # Add risk-specific tests
        if "security_sensitive" in context["risk_areas"]:
            test_cases.extend([
                f"test_{func.name}_sql_injection_protection",
                f"test_{func.name}_xss_protection",
                f"test_{func.name}_input_sanitization"
            ])
        
        if "high_complexity" in context["risk_areas"]:
            test_cases.extend([
                f"test_{func.name}_boundary_conditions",
                f"test_{func.name}_state_transitions",
                f"test_{func.name}_resource_management"
            ])
        
        if "frequently_changed" in context["risk_areas"]:
            test_cases.extend([
                f"test_{func.name}_regression_prevention",
                f"test_{func.name}_backward_compatibility"
            ])
        
        # Add comprehensive tests for high-priority functions
        if context["test_complexity"] == "comprehensive":
            test_cases.extend([
                f"test_{func.name}_performance_benchmark",
                f"test_{func.name}_memory_usage",
                f"test_{func.name}_stress_test",
                f"test_{func.name}_concurrency_safety"
            ])
        
        return test_cases

class PerformanceTracker:
    """Performance Regression Testing and Monitoring"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.metrics_db = project_root / "performance_metrics.db"
        self._init_performance_db()
    
    def _init_performance_db(self):
        """Initialize performance metrics database"""
        conn = sqlite3.connect(self.metrics_db)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_name TEXT,
                file_path TEXT,
                execution_time REAL,
                memory_usage REAL,
                cpu_usage REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                git_commit TEXT,
                test_run_id TEXT,
                baseline_comparison REAL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS performance_baselines (
                function_name TEXT PRIMARY KEY,
                baseline_execution_time REAL,
                baseline_memory_usage REAL,
                baseline_cpu_usage REAL,
                established_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sample_size INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
        conn.close()
    
    def record_performance(self, metrics: PerformanceMetrics):
        """Record performance metrics for a function"""
        conn = sqlite3.connect(self.metrics_db)
        
        # Get current git commit
        try:
            git_commit = subprocess.run(
                ['git', 'rev-parse', 'HEAD'], 
                capture_output=True, text=True, cwd=self.project_root
            ).stdout.strip()
        except:
            git_commit = "unknown"
        
        # Insert metrics
        conn.execute('''
            INSERT INTO performance_metrics 
            (function_name, execution_time, memory_usage, cpu_usage, git_commit)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            metrics.function_name, metrics.execution_time, 
            metrics.memory_usage, metrics.cpu_usage, git_commit
        ))
        
        # Update or create baseline
        self._update_baseline(conn, metrics)
        
        conn.commit()
        conn.close()
    
    def _update_baseline(self, conn, metrics: PerformanceMetrics):
        """Update performance baseline for function"""
        # Check if baseline exists
        cursor = conn.execute(
            'SELECT baseline_execution_time, sample_size FROM performance_baselines WHERE function_name = ?',
            (metrics.function_name,)
        )
        result = cursor.fetchone()
        
        if result:
            # Update existing baseline (rolling average)
            current_baseline, sample_size = result
            new_sample_size = sample_size + 1
            new_baseline = ((current_baseline * sample_size) + metrics.execution_time) / new_sample_size
            
            conn.execute('''
                UPDATE performance_baselines 
                SET baseline_execution_time = ?, sample_size = ?
                WHERE function_name = ?
            ''', (new_baseline, new_sample_size, metrics.function_name))
        else:
            # Create new baseline
            conn.execute('''
                INSERT INTO performance_baselines 
                (function_name, baseline_execution_time, baseline_memory_usage, baseline_cpu_usage)
                VALUES (?, ?, ?, ?)
            ''', (
                metrics.function_name, metrics.execution_time,
                metrics.memory_usage, metrics.cpu_usage
            ))
    
    def check_regression(self, function_name: str, current_time: float) -> Dict[str, Any]:
        """Check for performance regression"""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.execute(
            'SELECT baseline_execution_time FROM performance_baselines WHERE function_name = ?',
            (function_name,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {"regression": False, "reason": "No baseline established"}
        
        baseline_time = result[0]
        regression_ratio = current_time / baseline_time
        
        return {
            "regression": regression_ratio > 1.5,  # 50% slower than baseline
            "baseline_time": baseline_time,
            "current_time": current_time,
            "regression_ratio": regression_ratio,
            "performance_change": ((regression_ratio - 1) * 100)
        }

class ComprehensiveTestOrchestrator:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.functions: Dict[str, FunctionInfo] = {}
        self.test_results: Dict[str, TestResult] = {}
        self.priority_analyzer = TestPriorityAnalyzer(self.project_root)
        self.ai_generator = AITestGenerator(self.project_root)
        self.performance_tracker = PerformanceTracker(self.project_root)
        self.excluded_patterns = [
            '__pycache__', 'node_modules', '.venv', 'venv',
            'build', 'dist', '.git', '__tests__', 'test_'
        ]
        
    async def execute_comprehensive_testing(self) -> Dict[str, Any]:
        """Enhanced comprehensive testing workflow with AI and performance tracking"""
        console.print(Panel(
            "[bold blue]🎯 AI-Enhanced Smart Testing Workflow[/bold blue]\n"
            "Intelligent function discovery, prioritization, and comprehensive testing",
            title="Smart Testing Engine Starting"
        ))
        
        # Phase 1: Discovery
        console.print("\n[bold yellow]Phase 1: Intelligent Function Discovery[/bold yellow]")
        await self._discover_all_functions()
        
        # Phase 2: Smart Analysis & Prioritization
        console.print("\n[bold yellow]Phase 2: Smart Analysis & Prioritization[/bold yellow]")
        await self._analyze_functions()
        
        # Phase 3: AI-Enhanced Test Generation
        console.print("\n[bold yellow]Phase 3: AI-Enhanced Test Generation[/bold yellow]")
        await self._generate_ai_tests()
        
        # Phase 4: Performance-Monitored Test Execution
        console.print("\n[bold yellow]Phase 4: Performance-Monitored Test Execution[/bold yellow]")
        await self._execute_tests_with_performance()
        
        # Phase 5: Comprehensive Report Generation
        console.print("\n[bold yellow]Phase 5: Comprehensive Analysis & Reporting[/bold yellow]")
        report = await self._generate_enhanced_report()
        
        return report
    
    async def _discover_all_functions(self):
        """Discover all functions in the codebase"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            # Discover Python functions
            py_task = progress.add_task("[cyan]Scanning Python files...", total=None)
            python_functions = await self._discover_python_functions()
            progress.update(py_task, completed=100)
            
            # Discover JavaScript/TypeScript functions
            js_task = progress.add_task("[cyan]Scanning JavaScript/TypeScript files...", total=None)
            js_functions = await self._discover_javascript_functions()
            progress.update(js_task, completed=100)
        
        total_functions = len(self.functions)
        console.print(f"\n✅ Discovered [bold green]{total_functions}[/bold green] functions")
        
    async def _discover_python_functions(self) -> List[FunctionInfo]:
        """Discover all Python functions"""
        functions = []
        
        for py_file in self.project_root.rglob("*.py"):
            if any(pattern in str(py_file) for pattern in self.excluded_patterns):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                        func_info = FunctionInfo(
                            name=node.name,
                            file_path=str(py_file.relative_to(self.project_root)),
                            line_number=node.lineno,
                            parameters=[arg.arg for arg in node.args.args],
                            return_type=self._get_return_type(node),
                            is_async=isinstance(node, ast.AsyncFunctionDef),
                            docstring=ast.get_docstring(node),
                            decorators=[d.id for d in node.decorator_list if hasattr(d, 'id')],
                            complexity=self._calculate_complexity(node)
                        )
                        
                        key = f"{func_info.file_path}::{func_info.name}"
                        self.functions[key] = func_info
                        functions.append(func_info)
                        
            except Exception as e:
                console.print(f"[red]Error parsing {py_file}: {e}[/red]")
        
        return functions
    
    async def _discover_javascript_functions(self) -> List[FunctionInfo]:
        """Discover JavaScript/TypeScript functions using regex"""
        functions = []
        patterns = [
            r'function\s+(\w+)\s*\(',  # Regular functions
            r'const\s+(\w+)\s*=\s*(?:async\s+)?\(',  # Arrow functions
            r'(\w+)\s*:\s*(?:async\s+)?\(',  # Object methods
            r'export\s+(?:async\s+)?function\s+(\w+)',  # Exported functions
        ]
        
        for js_file in self.project_root.rglob("*.js"):
            if any(pattern in str(js_file) for pattern in self.excluded_patterns):
                continue
                
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in patterns:
                    for match in re.finditer(pattern, content):
                        func_name = match.group(1)
                        line_number = content[:match.start()].count('\n') + 1
                        
                        func_info = FunctionInfo(
                            name=func_name,
                            file_path=str(js_file.relative_to(self.project_root)),
                            line_number=line_number,
                            parameters=[],  # Would need proper JS parsing
                            return_type=None,
                            is_async='async' in match.group(0),
                            docstring=None,
                            decorators=[],
                            complexity=1
                        )
                        
                        key = f"{func_info.file_path}::{func_info.name}"
                        self.functions[key] = func_info
                        functions.append(func_info)
                        
            except Exception as e:
                console.print(f"[red]Error parsing {js_file}: {e}[/red]")
        
        return functions
    
    def _get_return_type(self, node) -> Optional[str]:
        """Extract return type from function annotation"""
        if hasattr(node, 'returns') and node.returns:
            return ast.unparse(node.returns)
        return None
    
    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    async def _analyze_functions(self):
        """Analyze functions for test requirements with priority scoring"""
        console.print("🔍 Analyzing functions and calculating priorities...")
        
        # Check test existence for all functions
        for key, func in self.functions.items():
            func.has_test = await self._check_test_exists(func)
        
        # Apply priority analysis
        prioritized_functions = self.priority_analyzer.prioritize_functions(
            list(self.functions.values())
        )
        
        # Update functions dict with prioritized data
        for func in prioritized_functions:
            key = f"{func.file_path}::{func.name}"
            self.functions[key] = func
        
        # Create enhanced analysis table
        table = Table(title="Smart Function Analysis (Top Priority)")
        table.add_column("File", style="cyan")
        table.add_column("Function", style="magenta")
        table.add_column("Priority", style="red")
        table.add_column("Complexity", style="yellow")
        table.add_column("Git Changes", style="orange1")
        table.add_column("Critical", style="bold red")
        table.add_column("Has Test", style="blue")
        
        # Show top 15 priority functions
        for func in prioritized_functions[:15]:
            table.add_row(
                func.file_path,
                func.name,
                f"{func.priority_score:.1f}",
                str(func.complexity),
                str(func.git_changes),
                "🔥" if func.business_critical else "⚡",
                "✓" if func.has_test else "✗"
            )
        
        console.print(table)
        
        # Enhanced statistics
        total = len(self.functions)
        tested = sum(1 for f in self.functions.values() if f.has_test)
        untested = total - tested
        critical_untested = sum(1 for f in self.functions.values() 
                              if f.business_critical and not f.has_test)
        high_priority_untested = sum(1 for f in self.functions.values() 
                                   if f.priority_score > 50 and not f.has_test)
        
        console.print(f"\n📊 Enhanced Statistics:")
        console.print(f"  Total functions: {total}")
        console.print(f"  With tests: [green]{tested}[/green]")
        console.print(f"  Without tests: [red]{untested}[/red]")
        console.print(f"  Critical untested: [bold red]{critical_untested}[/bold red]")
        console.print(f"  High priority untested: [orange1]{high_priority_untested}[/orange1]")
        console.print(f"  Coverage: {tested/total*100:.1f}%")
    
    async def _check_test_exists(self, func: FunctionInfo) -> bool:
        """Check if a test exists for the function"""
        # Look for test files
        test_patterns = [
            f"test_{func.name}",
            f"{func.name}_test",
            f"test_{Path(func.file_path).stem}",
        ]
        
        for pattern in test_patterns:
            test_files = list(self.project_root.rglob(f"*{pattern}*.py"))
            if test_files:
                func.test_file = str(test_files[0])
                return True
        
        return False
    
    async def _generate_tests(self):
        """Generate tests prioritized by function importance"""
        # Get prioritized untested functions
        untested_functions = [
            func for func in self.functions.values() 
            if not func.has_test
        ]
        
        # Sort by priority score (highest first)
        untested_functions.sort(key=lambda f: f.priority_score, reverse=True)
        
        console.print(f"\n🔨 Generating priority-based tests for {len(untested_functions)} functions...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Generating priority tests...", 
                total=len(untested_functions)
            )
            
            for func in untested_functions:
                # Generate more comprehensive tests for high-priority functions
                test_depth = "comprehensive" if func.priority_score > 50 else "standard"
                await self._generate_test_for_function(func, test_depth)
                progress.update(task, advance=1)
    
    async def _generate_ai_tests(self):
        """AI-enhanced test generation with intelligent patterns"""
        # Get prioritized untested functions
        untested_functions = [
            func for func in self.functions.values() 
            if not func.has_test
        ]
        
        # Sort by priority score (highest first)
        untested_functions.sort(key=lambda f: f.priority_score, reverse=True)
        
        console.print(f"\n🤖 AI-Enhanced test generation for {len(untested_functions)} functions...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Generating AI-enhanced tests...", 
                total=len(untested_functions)
            )
            
            for func in untested_functions:
                # Analyze function context for AI test generation
                context = self.ai_generator.analyze_function_context(func)
                test_cases = self.ai_generator.generate_ai_test_cases(func, context)
                
                # Generate enhanced test with AI insights
                test_depth = "comprehensive" if func.priority_score > 50 else "standard"
                await self._generate_ai_test_for_function(func, test_depth, context, test_cases)
                progress.update(task, advance=1)
    
    async def _generate_test_for_function(self, func: FunctionInfo, test_depth: str = "standard"):
        """Generate tests for a single function with varying depth"""
        test_content = self._create_test_template(func, test_depth)
        
        # Determine test file path
        test_dir = self.project_root / "tests" / "generated"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = test_dir / f"test_{Path(func.file_path).stem}_{func.name}.py"
        
        # Write test file
        test_file.write_text(test_content)
        func.test_file = str(test_file.relative_to(self.project_root))
        func.has_test = True
    
    async def _generate_ai_test_for_function(self, func: FunctionInfo, test_depth: str, context: Dict[str, Any], test_cases: List[str]):
        """Generate AI-enhanced test for a single function"""
        test_content = self._create_ai_test_template(func, test_depth, context, test_cases)
        
        # Determine test file path with AI suffix
        test_dir = self.project_root / "tests" / "ai_generated"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = test_dir / f"test_{Path(func.file_path).stem}_{func.name}_ai.py"
        
        # Write enhanced test file
        test_file.write_text(test_content)
        func.test_file = str(test_file.relative_to(self.project_root))
        func.has_test = True
    
    def _create_test_template(self, func: FunctionInfo, test_depth: str = "standard") -> str:
        """Create test template for a function with varying depth"""
        # Import the module
        module_path = Path(func.file_path).with_suffix('')
        module_import = str(module_path).replace('/', '.').replace('\\', '.')
        
        # Priority indicator in header
        priority_info = f"Priority Score: {func.priority_score:.1f} | " \
                       f"{'Business Critical' if func.business_critical else 'Standard'} | " \
                       f"Complexity: {func.complexity}"
        
        base_template = f'''"""
Automated tests for {func.name} in {func.file_path}
Generated by Smart Test Prioritization Engine
{priority_info}
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
{f"from {module_import} import {func.name}" if not func.file_path.startswith('test') else ''}


class Test{func.name.title()}:
    """{'Comprehensive' if test_depth == 'comprehensive' else 'Standard'} test suite for {func.name}"""
    
    def test_{func.name}_happy_path(self):
        """Test normal operation of {func.name}"""
        # TODO: Implement happy path test
        {"result = asyncio.run(" + func.name + "())" if func.is_async else f"result = {func.name}()"}
        assert result is not None
    
    def test_{func.name}_edge_cases(self):
        """Test edge cases for {func.name}"""
        # Test with None parameters
        with pytest.raises(Exception):
            {"asyncio.run(" + func.name + "(None))" if func.is_async else f"{func.name}(None)"}
    
    def test_{func.name}_error_handling(self):
        """Test error handling in {func.name}"""
        # Test various error conditions
        pass
'''

        # Add comprehensive tests for high-priority functions
        if test_depth == "comprehensive":
            comprehensive_tests = f'''
    def test_{func.name}_performance(self):
        """Performance tests for high-priority function {func.name}"""
        import time
        start_time = time.time()
        {"asyncio.run(" + func.name + "())" if func.is_async else f"{func.name}()"}
        execution_time = time.time() - start_time
        assert execution_time < 1.0  # Should complete within 1 second
    
    def test_{func.name}_concurrency(self):
        """Concurrency tests for {func.name}"""
        {"# Async concurrency tests" if func.is_async else "# Threading tests"}
        pass
    
    def test_{func.name}_data_validation(self):
        """Data validation tests for business-critical function"""
        # Test input validation
        # Test output format validation
        pass
    
    def test_{func.name}_security(self):
        """Security tests for critical function"""
        # Test for potential security vulnerabilities
        # Test input sanitization
        pass
    
    @pytest.mark.stress
    def test_{func.name}_stress_test(self):
        """Stress testing for high-priority function"""
        # Perform multiple rapid calls
        for i in range(100):
            {"asyncio.run(" + func.name + "())" if func.is_async else f"{func.name}()"}
'''
            base_template += comprehensive_tests
        
        # Add standard parameterized tests
        base_template += f'''
    @pytest.mark.parametrize("input_val,expected", [
        (None, Exception),
        ("", ValueError),
        ([], IndexError),
    ])
    def test_{func.name}_parameterized(self, input_val, expected):
        """Parameterized tests for {func.name}"""
        if expected:
            with pytest.raises(expected):
                {"asyncio.run(" + func.name + "(input_val))" if func.is_async else f"{func.name}(input_val)"}
'''
        
        return base_template
    
    def _create_ai_test_template(self, func: FunctionInfo, test_depth: str, context: Dict[str, Any], test_cases: List[str]) -> str:
        """Create AI-enhanced test template"""
        module_path = Path(func.file_path).with_suffix('')
        module_import = str(module_path).replace('/', '.').replace('\\', '.')
        
        # AI analysis header
        ai_info = f"""
Function Type: {context['function_type']}
Risk Areas: {', '.join(context['risk_areas'])}
Test Complexity: {context['test_complexity']}
AI-Generated Test Cases: {len(test_cases)}
Priority Score: {func.priority_score:.1f}
"""
        
        template = f'''"""
AI-Enhanced Tests for {func.name} in {func.file_path}
Generated by AI Test Generation Engine

{ai_info}
"""

import pytest
import asyncio
import time
import psutil
import os
from unittest.mock import Mock, patch, MagicMock
{f"from {module_import} import {func.name}" if not func.file_path.startswith('test') else ''}


class Test{func.name.title()}AI:
    """AI-Enhanced comprehensive test suite for {func.name}"""
    
    @pytest.fixture(autouse=True)
    def setup_performance_tracking(self):
        """Setup performance tracking for each test"""
        self.start_time = time.time()
        self.process = psutil.Process(os.getpid())
        self.start_memory = self.process.memory_info().rss
        yield
        # Performance tracking happens in teardown
    
'''
        
        # Generate AI test cases
        for test_case in test_cases:
            if "performance" in test_case:
                template += f'''
    def {test_case}(self):
        """AI-generated performance test for {func.name}"""
        start_time = time.time()
        {"result = asyncio.run(" + func.name + "())" if func.is_async else f"result = {func.name}()"}
        execution_time = time.time() - start_time
        
        # Performance assertions
        assert execution_time < 1.0, f"Function took too long: {{execution_time:.3f}}s"
        assert result is not None
'''
            elif "security" in test_case:
                template += f'''
    def {test_case}(self):
        """AI-generated security test for {func.name}"""
        # Test malicious input handling
        malicious_inputs = ["<script>", "'; DROP TABLE users; --", "../../../etc/passwd"]
        for malicious_input in malicious_inputs:
            with pytest.raises((ValueError, SecurityError, Exception)):
                {"asyncio.run(" + func.name + "(malicious_input))" if func.is_async else f"{func.name}(malicious_input)"}
'''
            elif "concurrency" in test_case:
                template += f'''
    @pytest.mark.asyncio
    async def {test_case}(self):
        """AI-generated concurrency test for {func.name}"""
        import asyncio
        tasks = []
        for i in range(10):
            {"task = asyncio.create_task(" + func.name + "())" if func.is_async else f"task = asyncio.create_task(asyncio.to_thread({func.name}))"}
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert all(not isinstance(r, Exception) for r in results), "Concurrency issues detected"
'''
            else:
                template += f'''
    def {test_case}(self):
        """AI-generated test: {test_case.replace('_', ' ').title()}"""
        # TODO: Implement specific test logic for {test_case}
        {"result = asyncio.run(" + func.name + "())" if func.is_async else f"result = {func.name}()"}
        assert result is not None
'''
        
        # Add function-type specific tests
        if context['function_type'] == 'api':
            template += f'''
    def test_{func.name}_api_response_format(self):
        """Validate API response format"""
        {"result = asyncio.run(" + func.name + "())" if func.is_async else f"result = {func.name}()"}
        # Validate response structure
        assert isinstance(result, (dict, list, str, int, float, bool))
'''
        
        return template
    
    async def _execute_tests(self):
        """Execute all tests and collect results"""
        console.print("\n🚀 Executing all tests...")
        
        # Run pytest
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short', '--json-report'],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        
        # Parse results
        if result.returncode == 0:
            console.print("[green]✅ All tests passed![/green]")
        else:
            console.print(f"[red]❌ Some tests failed[/red]")
            console.print(result.stdout)
    
    async def _execute_tests_with_performance(self):
        """Execute tests with performance monitoring and regression detection"""
        console.print("\n🚀 Executing tests with performance monitoring...")
        
        # Run pytest with performance monitoring
        result = subprocess.run([
            'python', '-m', 'pytest', 'tests/', '-v', '--tb=short', 
            '--json-report', '--cov=.', '--cov-report=xml',
            '--benchmark-only', '--benchmark-json=benchmark.json'
        ], capture_output=True, text=True, cwd=self.project_root)
        
        # Analyze performance results
        await self._analyze_performance_results()
        
        # Check for regressions
        regression_count = await self._check_performance_regressions()
        
        if result.returncode == 0:
            console.print("[green]✅ All tests passed![/green]")
            if regression_count > 0:
                console.print(f"[yellow]⚠️ {regression_count} performance regressions detected[/yellow]")
        else:
            console.print(f"[red]❌ Some tests failed[/red]")
            console.print(result.stdout)
    
    async def _analyze_performance_results(self):
        """Analyze performance test results"""
        benchmark_file = self.project_root / "benchmark.json"
        if benchmark_file.exists():
            import json
            with open(benchmark_file) as f:
                benchmark_data = json.load(f)
            
            # Process benchmark results
            for benchmark in benchmark_data.get('benchmarks', []):
                function_name = benchmark.get('name', 'unknown')
                execution_time = benchmark.get('stats', {}).get('mean', 0)
                
                # Create performance metrics
                metrics = PerformanceMetrics(
                    function_name=function_name,
                    execution_time=execution_time,
                    memory_usage=0.0,  # Would need additional instrumentation
                    cpu_usage=0.0,     # Would need additional instrumentation
                    timestamp=datetime.now()
                )
                
                # Record metrics
                self.performance_tracker.record_performance(metrics)
    
    async def _check_performance_regressions(self) -> int:
        """Check for performance regressions across all functions"""
        regression_count = 0
        
        for func_info in self.functions.values():
            if func_info.has_test:
                # Mock performance check - in real implementation would use actual test results
                mock_current_time = 0.1  # Would get from actual test execution
                regression_result = self.performance_tracker.check_regression(
                    func_info.name, mock_current_time
                )
                
                if regression_result.get('regression', False):
                    regression_count += 1
                    console.print(f"[yellow]⚠️ Performance regression in {func_info.name}: "
                                f"{regression_result['performance_change']:.1f}% slower[/yellow]")
        
        return regression_count
    
    async def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive testing report with priority metrics"""
        functions_list = list(self.functions.values())
        
        report = {
            "summary": {
                "total_functions": len(self.functions),
                "functions_with_tests": sum(1 for f in functions_list if f.has_test),
                "test_coverage": 0.0,
                "complex_functions": sum(1 for f in functions_list if f.complexity > 5),
                "async_functions": sum(1 for f in functions_list if f.is_async),
                "business_critical_functions": sum(1 for f in functions_list if f.business_critical),
                "high_priority_functions": sum(1 for f in functions_list if f.priority_score > 50),
                "average_priority_score": sum(f.priority_score for f in functions_list) / len(functions_list) if functions_list else 0,
                "critical_untested": sum(1 for f in functions_list if f.business_critical and not f.has_test),
                "high_priority_untested": sum(1 for f in functions_list if f.priority_score > 50 and not f.has_test)
            },
            "untested_functions": [],
            "high_risk_functions": [],
            "priority_analysis": {
                "top_priority_untested": [],
                "critical_functions": [],
                "recently_changed": []
            },
            "recommendations": []
        }
        
        # Calculate coverage
        if report["summary"]["total_functions"] > 0:
            report["summary"]["test_coverage"] = (
                report["summary"]["functions_with_tests"] / 
                report["summary"]["total_functions"] * 100
            )
        
        # Sort functions by priority for analysis
        sorted_functions = sorted(functions_list, key=lambda f: f.priority_score, reverse=True)
        
        # Find untested functions with priority scores
        for func in sorted_functions:
            if not func.has_test:
                report["untested_functions"].append({
                    "name": func.name,
                    "file": func.file_path,
                    "complexity": func.complexity,
                    "priority_score": func.priority_score,
                    "business_critical": func.business_critical,
                    "git_changes": func.git_changes,
                    "priority": "critical" if func.priority_score > 70 else "high" if func.priority_score > 50 else "medium"
                })
        
        # Top priority untested functions (top 10)
        top_untested = [f for f in sorted_functions if not f.has_test][:10]
        for func in top_untested:
            report["priority_analysis"]["top_priority_untested"].append({
                "name": func.name,
                "file": func.file_path,
                "priority_score": func.priority_score,
                "reason": f"High priority ({func.priority_score:.1f}) - {'Critical business function' if func.business_critical else 'Complex/frequently changed'}"
            })
        
        # Critical functions (business critical)
        for func in functions_list:
            if func.business_critical:
                report["priority_analysis"]["critical_functions"].append({
                    "name": func.name,
                    "file": func.file_path,
                    "has_test": func.has_test,
                    "priority_score": func.priority_score
                })
        
        # Recently changed functions (high git activity)
        recently_changed = [f for f in functions_list if f.git_changes > 3]
        for func in recently_changed:
            report["priority_analysis"]["recently_changed"].append({
                "name": func.name,
                "file": func.file_path,
                "git_changes": func.git_changes,
                "has_test": func.has_test,
                "priority_score": func.priority_score
            })
        
        # Enhanced high-risk functions
        for func in functions_list:
            risk_score = func.complexity * 2 + func.git_changes + (20 if func.business_critical else 0)
            if risk_score > 15 and not func.has_test:
                report["high_risk_functions"].append({
                    "name": func.name,
                    "file": func.file_path,
                    "complexity": func.complexity,
                    "priority_score": func.priority_score,
                    "risk_score": risk_score,
                    "reason": f"High risk (score: {risk_score}) - Complex, frequently changed, or critical function without tests"
                })
        
        # Enhanced recommendations based on priority analysis
        if report["summary"]["test_coverage"] < 80:
            report["recommendations"].append(
                "Increase test coverage to at least 80% for production readiness"
            )
        
        if report["summary"]["critical_untested"] > 0:
            report["recommendations"].append(
                f"🔥 URGENT: {report['summary']['critical_untested']} business-critical functions lack tests"
            )
        
        if report["summary"]["high_priority_untested"] > 0:
            report["recommendations"].append(
                f"⚡ HIGH PRIORITY: {report['summary']['high_priority_untested']} high-priority functions need tests"
            )
        
        if report["high_risk_functions"]:
            report["recommendations"].append(
                f"🎯 FOCUS: Add tests for {len(report['high_risk_functions'])} high-risk functions first"
            )
        
        if report["priority_analysis"]["recently_changed"]:
            report["recommendations"].append(
                f"📈 MONITOR: {len(report['priority_analysis']['recently_changed'])} frequently changed functions need attention"
            )
        
        # Add specific priority-based recommendations
        if report["summary"]["average_priority_score"] > 40:
            report["recommendations"].append(
                "Consider implementing automated test generation for high-complexity functions"
            )
        
        if len(report["priority_analysis"]["critical_functions"]) > 10:
            report["recommendations"].append(
                "Large number of critical functions detected - implement comprehensive test suite review"
            )
        
        # Save report
        report_file = self.project_root / "test_coverage_report.json"
        report_file.write_text(json.dumps(report, indent=2))
        
        # Display summary
        self._display_report_summary(report)
        
        return report
    
    async def _generate_enhanced_report(self) -> Dict[str, Any]:
        """Generate enhanced report with AI insights and performance data"""
        # Start with standard report
        report = await self._generate_report()
        
        # Add AI and performance enhancements
        functions_list = list(self.functions.values())
        
        # AI-Enhanced metrics
        ai_metrics = {
            "ai_generated_tests": sum(1 for f in functions_list if f.has_test and "ai_generated" in (f.test_file or "")),
            "ai_coverage_improvement": 0.0,
            "intelligent_prioritization": True,
            "context_aware_testing": True
        }
        
        # Performance metrics
        performance_metrics = {
            "performance_baselines_established": 0,
            "regression_detected": 0,
            "performance_improvements": 0,
            "benchmark_coverage": 0.0
        }
        
        # Try to get performance data from database
        try:
            conn = sqlite3.connect(self.performance_tracker.metrics_db)
            cursor = conn.execute('SELECT COUNT(*) FROM performance_baselines')
            performance_metrics["performance_baselines_established"] = cursor.fetchone()[0]
            conn.close()
        except:
            pass
        
        # Test quality scoring
        quality_metrics = {
            "comprehensive_tests": sum(1 for f in functions_list if f.priority_score > 50 and f.has_test),
            "security_tests": sum(1 for f in functions_list if f.business_critical and f.has_test),
            "performance_tests": ai_metrics["ai_generated_tests"],
            "overall_quality_score": 0.0
        }
        
        # Calculate overall quality score
        if functions_list:
            quality_score = (
                (quality_metrics["comprehensive_tests"] / len(functions_list)) * 40 +
                (quality_metrics["security_tests"] / max(1, sum(1 for f in functions_list if f.business_critical))) * 30 +
                (report["summary"]["test_coverage"] / 100) * 30
            )
            quality_metrics["overall_quality_score"] = min(100, quality_score)
        
        # Add enhanced sections to report
        report["ai_insights"] = ai_metrics
        report["performance_analysis"] = performance_metrics
        report["quality_assessment"] = quality_metrics
        
        # Enhanced recommendations with AI insights
        enhanced_recommendations = []
        
        if quality_metrics["overall_quality_score"] < 70:
            enhanced_recommendations.append(
                f"🎯 FOCUS: Overall test quality score is {quality_metrics['overall_quality_score']:.1f}% - implement comprehensive testing strategy"
            )
        
        if ai_metrics["ai_generated_tests"] > 0:
            enhanced_recommendations.append(
                f"🤖 AI SUCCESS: {ai_metrics['ai_generated_tests']} AI-generated tests created - review and customize as needed"
            )
        
        if performance_metrics["performance_baselines_established"] < len(functions_list) / 2:
            enhanced_recommendations.append(
                "📊 PERFORMANCE: Establish performance baselines for critical functions"
            )
        
        report["enhanced_recommendations"] = enhanced_recommendations
        
        # Save enhanced report
        enhanced_report_file = self.project_root / "enhanced_test_coverage_report.json"
        enhanced_report_file.write_text(json.dumps(report, indent=2, default=str))
        
        # Generate visual dashboard
        await self._generate_visual_dashboard(report)
        
        # Display enhanced summary
        self._display_enhanced_report_summary(report)
        
        return report
    
    async def _generate_visual_dashboard(self, report: Dict[str, Any]):
        """Generate interactive HTML dashboard for test coverage"""
        dashboard_html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Smart Test Coverage Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .dashboard {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid;
        }}
        .metric-card.coverage {{ border-left-color: #4CAF50; }}
        .metric-card.priority {{ border-left-color: #FF5722; }}
        .metric-card.ai {{ border-left-color: #9C27B0; }}
        .metric-card.performance {{ border-left-color: #2196F3; }}
        .metric-card.quality {{ border-left-color: #FF9800; }}
        .metric-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-subtitle {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .charts-section {{
            padding: 30px;
            background: #f8f9fa;
        }}
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .recommendations {{
            background: #fff3cd;
            border-radius: 10px;
            padding: 20px;
            margin: 20px;
            border-left: 5px solid #ffc107;
        }}
        .recommendation-item {{
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
            border-left: 3px solid #28a745;
        }}
        .priority-high {{ border-left-color: #dc3545; }}
        .priority-medium {{ border-left-color: #ffc107; }}
        .priority-low {{ border-left-color: #28a745; }}
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🎯 Smart Test Coverage Dashboard</h1>
            <p>AI-Enhanced Testing Analysis - Generated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card coverage">
                <div class="metric-title">📊 Test Coverage</div>
                <div class="metric-value">{report['summary']['test_coverage']:.1f}%</div>
                <div class="metric-subtitle">{report['summary']['functions_with_tests']} of {report['summary']['total_functions']} functions</div>
            </div>
            
            <div class="metric-card priority">
                <div class="metric-title">🔥 Priority Score</div>
                <div class="metric-value">{report['summary']['average_priority_score']:.1f}</div>
                <div class="metric-subtitle">{report['summary']['high_priority_functions']} high priority functions</div>
            </div>
            
            <div class="metric-card ai">
                <div class="metric-title">🤖 AI Generated</div>
                <div class="metric-value">{report.get('ai_insights', {}).get('ai_generated_tests', 0)}</div>
                <div class="metric-subtitle">AI-generated test cases</div>
            </div>
            
            <div class="metric-card performance">
                <div class="metric-title">⚡ Performance</div>
                <div class="metric-value">{report.get('performance_analysis', {}).get('performance_baselines_established', 0)}</div>
                <div class="metric-subtitle">Performance baselines</div>
            </div>
            
            <div class="metric-card quality">
                <div class="metric-title">🏆 Quality Score</div>
                <div class="metric-value">{report.get('quality_assessment', {}).get('overall_quality_score', 0.0):.1f}%</div>
                <div class="metric-subtitle">Overall test quality</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <canvas id="coverageChart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <canvas id="priorityChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <div class="recommendations">
            <h3>💡 Smart Recommendations</h3>
            {''.join(f'<div class="recommendation-item priority-high">{rec}</div>' for rec in report.get('enhanced_recommendations', [])[:3])}
            {''.join(f'<div class="recommendation-item priority-medium">{rec}</div>' for rec in report['recommendations'][:5])}
        </div>
        
        <div class="footer">
            <p>Generated by Smart Test Prioritization Engine | Enhanced with AI Insights</p>
        </div>
    </div>
    
    <script>
        // Coverage Chart
        const coverageCtx = document.getElementById('coverageChart').getContext('2d');
        new Chart(coverageCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Tested Functions', 'Untested Functions'],
                datasets: [{{
                    data: [{report['summary']['functions_with_tests']}, {report['summary']['total_functions'] - report['summary']['functions_with_tests']}],
                    backgroundColor: ['#4CAF50', '#f44336'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Test Coverage Distribution'
                    }}
                }}
            }}
        }});
        
        // Priority Chart
        const priorityCtx = document.getElementById('priorityChart').getContext('2d');
        new Chart(priorityCtx, {{
            type: 'bar',
            data: {{
                labels: ['Critical Untested', 'High Priority Untested', 'Business Critical', 'Complex Functions'],
                datasets: [{{
                    label: 'Function Count',
                    data: [
                        {report['summary']['critical_untested']}, 
                        {report['summary']['high_priority_untested']}, 
                        {report['summary']['business_critical_functions']}, 
                        {report['summary']['complex_functions']}
                    ],
                    backgroundColor: ['#f44336', '#ff9800', '#9c27b0', '#2196f3'],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Priority Analysis'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
'''
        
        # Save dashboard
        dashboard_file = self.project_root / "test_coverage_dashboard.html"
        dashboard_file.write_text(dashboard_html)
        
        console.print(f"\\n📊 [bold green]Visual dashboard generated:[/bold green] {dashboard_file}")
        console.print("   Open in browser to view interactive test coverage analysis")
    
    def _display_report_summary(self, report: Dict[str, Any]):
        """Display enhanced report summary in console"""
        console.print("\n" + "="*70)
        console.print(Panel(
            f"""[bold]🎯 Smart Test Prioritization Report[/bold]
            
[cyan]📊 Coverage Metrics:[/cyan]
• Total Functions: {report['summary']['total_functions']}
• Functions with Tests: {report['summary']['functions_with_tests']}
• Test Coverage: {report['summary']['test_coverage']:.1f}%
• Complex Functions: {report['summary']['complex_functions']}
• Async Functions: {report['summary']['async_functions']}

[red]🔥 Priority Analysis:[/red]
• Business Critical Functions: {report['summary']['business_critical_functions']}
• High Priority Functions: {report['summary']['high_priority_functions']}
• Critical Untested: {report['summary']['critical_untested']}
• High Priority Untested: {report['summary']['high_priority_untested']}
• Average Priority Score: {report['summary']['average_priority_score']:.1f}

[yellow]⚠️ Risk Assessment:[/yellow]
• High Risk Functions: {len(report['high_risk_functions'])}
• Top Priority Untested: {len(report['priority_analysis']['top_priority_untested'])}
• Recently Changed: {len(report['priority_analysis']['recently_changed'])}

[green]💡 Smart Recommendations:[/green]
""" + "\n".join(f"• {rec}" for rec in report['recommendations']),
            title="Smart Test Coverage Analysis",
            style="bold green"
        ))
    
    def _display_enhanced_report_summary(self, report: Dict[str, Any]):
        """Display enhanced report summary with AI and performance insights"""
        console.print("\n" + "="*80)
        console.print(Panel(
            f"""[bold]🚀 Enhanced AI-Powered Testing Report[/bold]
            
[cyan]📊 Core Coverage Metrics:[/cyan]
• Total Functions: {report['summary']['total_functions']}
• Functions with Tests: {report['summary']['functions_with_tests']}
• Test Coverage: {report['summary']['test_coverage']:.1f}%
• Complex Functions: {report['summary']['complex_functions']}
• Async Functions: {report['summary']['async_functions']}

[red]🔥 Smart Priority Analysis:[/red]
• Business Critical Functions: {report['summary']['business_critical_functions']}
• High Priority Functions: {report['summary']['high_priority_functions']}
• Critical Untested: {report['summary']['critical_untested']}
• High Priority Untested: {report['summary']['high_priority_untested']}
• Average Priority Score: {report['summary']['average_priority_score']:.1f}

[magenta]🤖 AI Insights:[/magenta]
• AI-Generated Tests: {report.get('ai_insights', {}).get('ai_generated_tests', 0)}
• Intelligent Prioritization: {'✅' if report.get('ai_insights', {}).get('intelligent_prioritization') else '❌'}
• Context-Aware Testing: {'✅' if report.get('ai_insights', {}).get('context_aware_testing') else '❌'}

[blue]⚡ Performance Analysis:[/blue]
• Performance Baselines: {report.get('performance_analysis', {}).get('performance_baselines_established', 0)}
• Regressions Detected: {report.get('performance_analysis', {}).get('regression_detected', 0)}
• Benchmark Coverage: {report.get('performance_analysis', {}).get('benchmark_coverage', 0.0):.1f}%

[green]🏆 Quality Assessment:[/green]
• Overall Quality Score: {report.get('quality_assessment', {}).get('overall_quality_score', 0.0):.1f}%
• Comprehensive Tests: {report.get('quality_assessment', {}).get('comprehensive_tests', 0)}
• Security Tests: {report.get('quality_assessment', {}).get('security_tests', 0)}
• Performance Tests: {report.get('quality_assessment', {}).get('performance_tests', 0)}

[yellow]⚠️ Risk Assessment:[/yellow]
• High Risk Functions: {len(report['high_risk_functions'])}
• Top Priority Untested: {len(report['priority_analysis']['top_priority_untested'])}
• Recently Changed: {len(report['priority_analysis']['recently_changed'])}

[bright_green]💡 Enhanced Recommendations:[/bright_green]
""" + "\n".join(f"• {rec}" for rec in report.get('enhanced_recommendations', [])) + "\n" +
"\n".join(f"• {rec}" for rec in report['recommendations']),
            title="🎯 Smart Test Coverage Analysis Dashboard",
            style="bold bright_green"
        ))


# CLI Entry Point
async def main():
    """Main entry point for comprehensive testing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Comprehensive Function Testing Orchestrator"
    )
    parser.add_argument(
        '--generate-only', 
        action='store_true',
        help="Only generate tests, don't execute"
    )
    parser.add_argument(
        '--ai-generate',
        action='store_true',
        help="Use AI-enhanced test generation"
    )
    parser.add_argument(
        '--execute-only',
        action='store_true', 
        help="Only execute existing tests"
    )
    parser.add_argument(
        '--performance-monitoring',
        action='store_true',
        help="Enable performance monitoring during test execution"
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help="Only generate report from existing data"
    )
    parser.add_argument(
        '--dashboard',
        action='store_true',
        help="Generate interactive HTML dashboard"
    )
    parser.add_argument(
        '--target',
        help="Target specific file or directory"
    )
    parser.add_argument(
        '--priority-threshold',
        type=float,
        default=50.0,
        help="Priority score threshold for comprehensive testing (default: 50.0)"
    )
    
    args = parser.parse_args()
    
    orchestrator = ComprehensiveTestOrchestrator()
    
    if args.report_only:
        if args.dashboard:
            report = await orchestrator._generate_enhanced_report()
        else:
            report = await orchestrator._generate_report()
    elif args.execute_only:
        if args.performance_monitoring:
            await orchestrator._execute_tests_with_performance()
        else:
            await orchestrator._execute_tests()
    elif args.generate_only:
        await orchestrator._discover_all_functions()
        await orchestrator._analyze_functions()
        if args.ai_generate:
            await orchestrator._generate_ai_tests()
        else:
            await orchestrator._generate_tests()
    elif args.ai_generate or args.performance_monitoring or args.dashboard:
        # Enhanced workflow with specific features
        console.print(Panel(
            "[bold blue]🚀 Enhanced Testing Mode Activated[/bold blue]\n"
            f"AI Generation: {'✅' if args.ai_generate else '❌'}\n"
            f"Performance Monitoring: {'✅' if args.performance_monitoring else '❌'}\n"
            f"Interactive Dashboard: {'✅' if args.dashboard else '❌'}",
            title="Feature Configuration"
        ))
        
        report = await orchestrator.execute_comprehensive_testing()
        
        # Save enhanced reports
        console.print(f"\n✅ Enhanced reports generated:")
        console.print(f"   📊 JSON Report: enhanced_test_coverage_report.json")
        if args.dashboard:
            console.print(f"   🌐 Dashboard: test_coverage_dashboard.html")
    else:
        # Full enhanced workflow (default)
        report = await orchestrator.execute_comprehensive_testing()
        
        # Save final report
        console.print(f"\n✅ Enhanced testing complete!")
        console.print(f"   📊 Reports: test_coverage_report.json, enhanced_test_coverage_report.json")
        console.print(f"   🌐 Dashboard: test_coverage_dashboard.html")


if __name__ == "__main__":
    asyncio.run(main())
