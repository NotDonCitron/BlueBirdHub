"""
Plugin Security and Sandboxing System

Provides comprehensive security validation and sandboxing for plugins
to ensure system stability and prevent malicious code execution.
"""

import ast
import os
import sys
import hashlib
import logging
import tempfile
import subprocess
import importlib.util
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime, timedelta
import json
import psutil
import threading
import time
from dataclasses import dataclass
from contextlib import contextmanager

from .base import PluginMetadata, PluginException, PluginSecurityException


logger = logging.getLogger(__name__)


@dataclass
class SecurityPolicy:
    """Security policy configuration for plugins"""
    max_memory_mb: int = 256
    max_cpu_percent: int = 50
    max_disk_io_mb: int = 100
    max_network_requests: int = 100
    allowed_modules: Set[str] = None
    blocked_modules: Set[str] = None
    allowed_file_paths: Set[str] = None
    blocked_file_paths: Set[str] = None
    allow_network: bool = False
    allow_file_system: bool = False
    allow_subprocess: bool = False
    timeout_seconds: int = 300
    
    def __post_init__(self):
        if self.allowed_modules is None:
            self.allowed_modules = {
                'json', 'datetime', 'typing', 'dataclasses', 'enum',
                'logging', 'uuid', 'hashlib', 're', 'math', 'random',
                'collections', 'itertools', 'functools', 'operator'
            }
        
        if self.blocked_modules is None:
            self.blocked_modules = {
                'os', 'subprocess', 'sys', 'importlib', '__import__',
                'exec', 'eval', 'compile', 'open', 'file', 'input',
                'raw_input', 'execfile', 'reload', 'vars', 'dir',
                'globals', 'locals', 'delattr', 'setattr', 'getattr'
            }
        
        if self.allowed_file_paths is None:
            self.allowed_file_paths = set()
        
        if self.blocked_file_paths is None:
            self.blocked_file_paths = {
                '/etc', '/var', '/usr', '/bin', '/sbin', '/boot',
                '/dev', '/proc', '/sys', '/root', '/home'
            }


class PluginSandbox:
    """Sandboxed execution environment for plugins"""
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.start_time: Optional[datetime] = None
        self.process: Optional[psutil.Process] = None
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.network_requests: int = 0
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    @contextmanager
    def execute(self):
        """Context manager for sandboxed execution"""
        try:
            self.start_time = datetime.utcnow()
            self.process = psutil.Process()
            self._start_monitoring()
            yield self
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            raise PluginSecurityException(f"Sandbox execution failed: {e}")
        finally:
            self._stop_monitoring()
    
    def _start_monitoring(self):
        """Start resource monitoring"""
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitor_resources)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def _stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_resources(self):
        """Monitor plugin resource usage"""
        while self._monitoring_active and self.process:
            try:
                # Check timeout
                if self.start_time and datetime.utcnow() - self.start_time > timedelta(seconds=self.policy.timeout_seconds):
                    raise PluginSecurityException("Plugin execution timeout exceeded")
                
                # Monitor memory usage
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.memory_usage.append(memory_mb)
                
                if memory_mb > self.policy.max_memory_mb:
                    raise PluginSecurityException(f"Memory limit exceeded: {memory_mb}MB > {self.policy.max_memory_mb}MB")
                
                # Monitor CPU usage
                cpu_percent = self.process.cpu_percent()
                self.cpu_usage.append(cpu_percent)
                
                if cpu_percent > self.policy.max_cpu_percent:
                    raise PluginSecurityException(f"CPU limit exceeded: {cpu_percent}% > {self.policy.max_cpu_percent}%")
                
                time.sleep(1.0)
                
            except psutil.NoSuchProcess:
                break
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                break
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        return {
            "memory_usage_mb": self.memory_usage[-1] if self.memory_usage else 0,
            "cpu_usage_percent": self.cpu_usage[-1] if self.cpu_usage else 0,
            "network_requests": self.network_requests,
            "execution_time": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
            "memory_history": self.memory_usage[-60:],  # Last minute
            "cpu_history": self.cpu_usage[-60:]  # Last minute
        }


class SecurityValidator:
    """Validates plugin code for security vulnerabilities"""
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.dangerous_patterns = [
            'exec', 'eval', 'compile', '__import__', 'open', 'file',
            'subprocess', 'os.system', 'os.popen', 'os.spawn',
            'pickle.loads', 'marshal.loads', 'input', 'raw_input'
        ]
    
    def validate_code(self, code: str, filename: str = "<string>") -> List[str]:
        """Validate Python code for security issues"""
        violations = []
        
        try:
            # Parse the code into an AST
            tree = ast.parse(code, filename)
            
            # Analyze AST for security violations
            violations.extend(self._analyze_ast(tree))
            
            # Check for dangerous patterns
            violations.extend(self._check_dangerous_patterns(code))
            
            # Validate imports
            violations.extend(self._validate_imports(tree))
            
        except SyntaxError as e:
            violations.append(f"Syntax error: {e}")
        except Exception as e:
            violations.append(f"Code analysis error: {e}")
        
        return violations
    
    def _analyze_ast(self, tree: ast.AST) -> List[str]:
        """Analyze AST for security violations"""
        violations = []
        
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.dangerous_patterns:
                        violations.append(f"Dangerous function call: {node.func.id}")
                elif isinstance(node.func, ast.Attribute):
                    if f"{node.func.value.id if hasattr(node.func.value, 'id') else ''}.{node.func.attr}" in self.dangerous_patterns:
                        violations.append(f"Dangerous method call: {node.func.attr}")
            
            # Check for eval/exec usage
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id in ['eval', 'exec']:
                    violations.append(f"Dynamic code execution detected: {node.value.func.id}")
            
            # Check for file operations
            if isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        if isinstance(item.context_expr.func, ast.Name) and item.context_expr.func.id == 'open':
                            if not self.policy.allow_file_system:
                                violations.append("File system access not allowed")
        
        return violations
    
    def _check_dangerous_patterns(self, code: str) -> List[str]:
        """Check for dangerous code patterns using string analysis"""
        violations = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in self.dangerous_patterns:
                if pattern in line and not line.strip().startswith('#'):
                    violations.append(f"Dangerous pattern '{pattern}' found at line {i}")
        
        return violations
    
    def _validate_imports(self, tree: ast.AST) -> List[str]:
        """Validate import statements"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.policy.blocked_modules:
                        violations.append(f"Blocked module import: {alias.name}")
                    elif self.policy.allowed_modules and alias.name not in self.policy.allowed_modules:
                        violations.append(f"Unauthorized module import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.module in self.policy.blocked_modules:
                        violations.append(f"Blocked module import: {node.module}")
                    elif self.policy.allowed_modules and node.module not in self.policy.allowed_modules:
                        violations.append(f"Unauthorized module import: {node.module}")
        
        return violations


class PluginSecurity:
    """Main plugin security management system"""
    
    def __init__(self, data_dir: str = "/tmp/bluebirdhub_plugins"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.default_policy = SecurityPolicy()
        self.plugin_policies: Dict[str, SecurityPolicy] = {}
        self.sandboxes: Dict[str, PluginSandbox] = {}
        
    def set_plugin_policy(self, plugin_id: str, policy: SecurityPolicy):
        """Set security policy for a specific plugin"""
        self.plugin_policies[plugin_id] = policy
    
    def get_plugin_policy(self, plugin_id: str) -> SecurityPolicy:
        """Get security policy for a plugin"""
        return self.plugin_policies.get(plugin_id, self.default_policy)
    
    def validate_plugin_package(self, package_path: str) -> Dict[str, Any]:
        """Validate a plugin package for security"""
        results = {
            "valid": True,
            "violations": [],
            "warnings": [],
            "checksum": None,
            "manifest": None
        }
        
        try:
            package_path = Path(package_path)
            
            # Calculate checksum
            results["checksum"] = self._calculate_checksum(package_path)
            
            # Extract and validate manifest
            manifest_path = package_path / "plugin.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    results["manifest"] = json.load(f)
            else:
                results["violations"].append("Missing plugin.json manifest")
                results["valid"] = False
                return results
            
            # Validate Python files
            for py_file in package_path.glob("**/*.py"):
                violations = self._validate_python_file(py_file)
                if violations:
                    results["violations"].extend(violations)
                    results["valid"] = False
            
            # Check for suspicious files
            suspicious_files = self._check_suspicious_files(package_path)
            if suspicious_files:
                results["warnings"].extend(suspicious_files)
            
        except Exception as e:
            results["violations"].append(f"Package validation error: {e}")
            results["valid"] = False
        
        return results
    
    def _calculate_checksum(self, path: Path) -> str:
        """Calculate SHA256 checksum of a file or directory"""
        hasher = hashlib.sha256()
        
        if path.is_file():
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        else:
            # For directories, hash all files in sorted order
            for file_path in sorted(path.glob("**/*")):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def _validate_python_file(self, file_path: Path) -> List[str]:
        """Validate a single Python file"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            validator = SecurityValidator(self.default_policy)
            file_violations = validator.validate_code(code, str(file_path))
            
            for violation in file_violations:
                violations.append(f"{file_path.name}: {violation}")
                
        except Exception as e:
            violations.append(f"{file_path.name}: Error reading file - {e}")
        
        return violations
    
    def _check_suspicious_files(self, package_path: Path) -> List[str]:
        """Check for suspicious files in the package"""
        warnings = []
        
        suspicious_extensions = {'.exe', '.dll', '.so', '.dylib', '.bat', '.sh', '.ps1'}
        
        for file_path in package_path.glob("**/*"):
            if file_path.is_file():
                if file_path.suffix.lower() in suspicious_extensions:
                    warnings.append(f"Suspicious file: {file_path.name}")
                
                # Check for hidden files
                if file_path.name.startswith('.') and file_path.name not in {'.gitignore', '.env.example'}:
                    warnings.append(f"Hidden file: {file_path.name}")
        
        return warnings
    
    def create_sandbox(self, plugin_id: str) -> PluginSandbox:
        """Create a sandboxed execution environment for a plugin"""
        policy = self.get_plugin_policy(plugin_id)
        sandbox = PluginSandbox(policy)
        self.sandboxes[plugin_id] = sandbox
        return sandbox
    
    def get_sandbox(self, plugin_id: str) -> Optional[PluginSandbox]:
        """Get existing sandbox for a plugin"""
        return self.sandboxes.get(plugin_id)
    
    def remove_sandbox(self, plugin_id: str):
        """Remove sandbox for a plugin"""
        if plugin_id in self.sandboxes:
            del self.sandboxes[plugin_id]
    
    def verify_plugin_signature(self, package_path: str, signature: str, public_key: str) -> bool:
        """Verify plugin package digital signature"""
        # Implementation would use cryptographic libraries like cryptography
        # For now, return True (placeholder)
        return True
    
    def scan_for_malware(self, package_path: str) -> Dict[str, Any]:
        """Scan plugin package for malware"""
        # Implementation would integrate with antivirus engines
        # For now, return clean result (placeholder)
        return {
            "clean": True,
            "threats": [],
            "scan_time": datetime.utcnow().isoformat()
        }