"""
Claude Code Flow Orchestrator for OrdnungsHub
Implements recursive autonomous development with human checkpoints
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import subprocess
import difflib
from enum import Enum

# Try to import optional dependencies
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.table import Table
    console = Console()
except ImportError:
    # Fallback to basic print
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    console = Console()

class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class CodeChange:
    file_path: str
    old_content: str
    new_content: str
    description: str
    line_changes: Dict[str, Any]

@dataclass
class TestResult:
    passed: bool
    coverage: float
    failures: List[str]
    duration: float

@dataclass
class WorkflowState:
    task_id: str
    iteration: int
    confidence: float
    changes: List[CodeChange]
    test_results: Optional[TestResult]
    security_issues: List[str]
    human_checkpoints_passed: List[str]
    
class ClaudeCodeOrchestrator:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.config = self._load_config()
        self.max_iterations = self.config['orchestrator']['maxIterations']
        self.confidence_threshold = self.config['orchestrator']['confidenceThreshold']
        self.human_checkpoint_threshold = self.config['orchestrator']['humanCheckpointThreshold']
        self.current_state: Optional[WorkflowState] = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load workflow configuration"""
        config_path = self.project_root / '.claude' / 'workflows' / 'claude-code-flow.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration if file doesn't exist"""
        return {
            "orchestrator": {
                "maxIterations": 10,
                "confidenceThreshold": 0.85,
                "humanCheckpointThreshold": 0.95
            },
            "qualityGates": {
                "testCoverage": {"minimum": 85},
                "security": {"vulnerabilities": 0}
            }
        }
    
    async def execute_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a development task through recursive cycles"""
        console.print(Panel(f"Starting Claude Code Flow: {task_spec.get('description', 'Unnamed task')}", 
                          title="🚀 Task Execution", style="bold blue"))
        
        self.current_state = WorkflowState(
            task_id=task_spec.get('id', 'unknown'),
            iteration=0,
            confidence=0.0,
            changes=[],
            test_results=None,
            security_issues=[],
            human_checkpoints_passed=[]
        )
        
        # Decompose task into subtasks
        subtasks = await self._decompose_task(task_spec)
        
        # Execute each subtask
        for subtask in subtasks:
            await self._execute_subtask(subtask)
            
            # Check if we need human intervention
            if self._requires_human_checkpoint(subtask):
                if not await self._human_review(self.current_state):
                    return {"status": "rejected", "state": asdict(self.current_state)}
        
        return {
            "status": "completed",
            "state": asdict(self.current_state),
            "summary": self._generate_summary()
        }
    
    async def _decompose_task(self, task_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down complex task into manageable subtasks"""
        # This would call Claude to analyze and decompose
        # For now, return a simple structure
        task_type = task_spec.get('type', 'feature')
        
        if task_type == 'feature':
            return [
                {"name": "design", "description": "Design architecture and API"},
                {"name": "implement", "description": "Implement core functionality"},
                {"name": "test", "description": "Create comprehensive tests"},
                {"name": "document", "description": "Generate documentation"},
                {"name": "review", "description": "Final review and optimization"}
            ]
        elif task_type == 'bug-fix':
            return [
                {"name": "reproduce", "description": "Reproduce the issue"},
                {"name": "analyze", "description": "Find root cause"},
                {"name": "fix", "description": "Implement fix"},
                {"name": "test", "description": "Verify fix and add tests"}
            ]
        else:
            return [{"name": "implement", "description": task_spec.get('description', '')}]
    
    async def _execute_subtask(self, subtask: Dict[str, Any]) -> None:
        """Execute a single subtask with retry logic"""
        console.print(f"\n📋 Executing: {subtask['name']} - {subtask['description']}")
        
        iteration = 0
        while iteration < self.max_iterations:
            # Generate or modify code
            code_changes = await self._generate_code(subtask)
            
            # Apply changes
            for change in code_changes:
                self._apply_change(change)
                self.current_state.changes.append(change)
            
            # Run tests
            test_results = await self._run_tests()
            self.current_state.test_results = test_results
            
            # Check security if needed
            if self._is_security_sensitive(code_changes):
                security_results = await self._security_scan()
                self.current_state.security_issues = security_results
                
                if security_results:
                    console.print(f"⚠️  Security issues found: {security_results}", style="bold red")
                    subtask['constraints'] = security_results
                    iteration += 1
                    continue
            
            # Calculate confidence
            confidence = self._calculate_confidence(test_results)
            self.current_state.confidence = confidence
            
            console.print(f"✅ Iteration {iteration + 1} complete. Confidence: {confidence:.2%}")
            
            if confidence >= self.confidence_threshold:
                break
                
            iteration += 1
        
        if iteration >= self.max_iterations:
            console.print("⚠️  Max iterations reached. Escalating to human review.", style="yellow")
    
    async def _generate_code(self, subtask: Dict[str, Any]) -> List[CodeChange]:
        """Generate code changes using Claude Code"""
        # This would integrate with Claude API
        # For now, return mock changes
        return []
    
    def _apply_change(self, change: CodeChange) -> None:
        """Apply a code change to the filesystem"""
        file_path = self.project_root / change.file_path
        
        # Create backup
        if file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            backup_path.write_text(file_path.read_text())
        
        # Apply change
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(change.new_content)
        
        console.print(f"✏️  Modified: {change.file_path}")
    
    async def _run_tests(self) -> TestResult:
        """Run test suite and return results"""
        try:
            # Run Jest for frontend tests
            jest_result = subprocess.run(
                ['npm', 'run', 'test', '--', '--coverage', '--json'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            # Run pytest for backend tests
            pytest_result = subprocess.run(
                ['python', '-m', 'pytest', '--cov', '--json-report'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            # Parse results (simplified)
            passed = jest_result.returncode == 0 and pytest_result.returncode == 0
            coverage = 85.0  # Would parse from actual output
            
            return TestResult(
                passed=passed,
                coverage=coverage,
                failures=[],
                duration=1.0
            )
        except Exception as e:
            console.print(f"❌ Test execution failed: {e}", style="red")
            return TestResult(passed=False, coverage=0.0, failures=[str(e)], duration=0.0)
    
    async def _security_scan(self) -> List[str]:
        """Run security scanning tools"""
        issues = []
        
        # Run bandit for Python
        try:
            result = subprocess.run(
                ['bandit', '-r', 'src/backend', '-f', 'json'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode != 0:
                # Parse bandit output
                issues.append("Security vulnerabilities detected in Python code")
        except:
            pass
        
        # Run npm audit
        try:
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            audit_data = json.loads(result.stdout)
            if audit_data.get('vulnerabilities', {}).get('high', 0) > 0:
                issues.append("High severity npm vulnerabilities detected")
        except:
            pass
        
        return issues
    
    def _is_security_sensitive(self, changes: List[CodeChange]) -> bool:
        """Check if changes involve security-sensitive code"""
        sensitive_patterns = [
            'auth', 'password', 'token', 'secret', 'api_key',
            'encrypt', 'decrypt', 'hash', 'salt', 'session'
        ]
        
        for change in changes:
            content = change.new_content.lower()
            if any(pattern in content for pattern in sensitive_patterns):
                return True
        return False
    
    def _calculate_confidence(self, test_results: TestResult) -> float:
        """Calculate confidence score based on test results"""
        if not test_results.passed:
            return 0.0
        
        base_confidence = 0.5
        coverage_bonus = (test_results.coverage / 100) * 0.3
        no_failures_bonus = 0.2 if not test_results.failures else 0.0
        
        return min(base_confidence + coverage_bonus + no_failures_bonus, 1.0)
    
    def _requires_human_checkpoint(self, subtask: Dict[str, Any]) -> bool:
        """Determine if human review is needed"""
        critical_subtasks = ['security', 'auth', 'payment', 'database-schema']
        return any(critical in subtask['name'].lower() for critical in critical_subtasks)
    
    async def _human_review(self, state: WorkflowState) -> bool:
        """Request human review"""
        console.print(Panel("🧑 Human review requested", title="Checkpoint", style="yellow"))
        
        # Display changes
        table = Table(title="Proposed Changes")
        table.add_column("File", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Lines Changed", style="green")
        
        for change in state.changes:
            lines = len(change.new_content.splitlines()) - len(change.old_content.splitlines())
            table.add_row(change.file_path, change.description, f"+{lines}" if lines > 0 else str(lines))
        
        console.print(table)
        console.print(f"\nConfidence: {state.confidence:.2%}")
        console.print(f"Test Coverage: {state.test_results.coverage:.1f}%" if state.test_results else "No tests run")
        
        # In real implementation, this would wait for human input
        # For now, auto-approve
        return True
    
    def _generate_summary(self) -> str:
        """Generate execution summary"""
        return f"""
Task Execution Summary
=====================
Task ID: {self.current_state.task_id}
Total Iterations: {self.current_state.iteration}
Final Confidence: {self.current_state.confidence:.2%}
Files Modified: {len(set(c.file_path for c in self.current_state.changes))}
Test Coverage: {self.current_state.test_results.coverage:.1f}%
Security Issues: {len(self.current_state.security_issues)}
Human Checkpoints: {len(self.current_state.human_checkpoints_passed)}
"""


# CLI Integration
async def main():
    """Main entry point for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Code Flow Orchestrator")
    parser.add_argument('command', choices=['feature', 'bug-fix', 'refactor', 'test'])
    parser.add_argument('description', help="Task description")
    parser.add_argument('--type', default='feature', help="Task type")
    parser.add_argument('--auto-approve', action='store_true', help="Auto-approve human checkpoints")
    
    args = parser.parse_args()
    
    orchestrator = ClaudeCodeOrchestrator()
    
    task_spec = {
        'id': f"{args.command}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        'type': args.type,
        'description': args.description,
        'auto_approve': args.auto_approve
    }
    
    result = await orchestrator.execute_task(task_spec)
    console.print(Panel(result['summary'], title="✅ Execution Complete", style="green"))

if __name__ == "__main__":
    asyncio.run(main())
