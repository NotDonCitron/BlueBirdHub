"""
Smart Automation Engine for OrdnungsHub
Advanced AI-powered automation with learning capabilities and intelligent rule generation
"""
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re
from collections import defaultdict, Counter
import statistics
from loguru import logger

class ActionType(Enum):
    MOVE = "move"
    COPY = "copy"
    TAG = "tag"
    ORGANIZE = "organize"
    NOTIFY = "notify"
    COMPRESS = "compress"
    DELETE = "delete"
    ANALYZE = "analyze"

class ConditionType(Enum):
    FILE_EXTENSION = "file_extension"
    FILE_SIZE = "file_size"
    FILE_NAME_PATTERN = "file_name_pattern"
    CONTENT_KEYWORDS = "content_keywords"
    FILE_AGE = "file_age"
    WORKSPACE = "workspace"
    TAG_CONTAINS = "tag_contains"
    USER_BEHAVIOR = "user_behavior"

@dataclass
class AutomationCondition:
    type: ConditionType
    operator: str  # "equals", "contains", "greater_than", "less_than", "regex", "in"
    value: Any
    weight: float = 1.0  # Importance weight for this condition

@dataclass
class AutomationAction:
    type: ActionType
    parameters: Dict[str, Any]
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class AutomationRule:
    id: str
    name: str
    description: str
    conditions: List[AutomationCondition]
    actions: List[AutomationAction]
    enabled: bool = True
    confidence_threshold: float = 0.7
    created_at: datetime = None
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    success_rate: float = 1.0
    learning_data: Dict[str, Any] = None

@dataclass
class UserBehaviorPattern:
    user_id: int
    action_type: str
    file_patterns: List[str]
    frequency: int
    success_rate: float
    last_seen: datetime
    context: Dict[str, Any]

class SmartAutomationEngine:
    """
    Advanced automation engine with AI-powered rule generation and learning
    """
    
    def __init__(self):
        self.rules: Dict[str, AutomationRule] = {}
        self.user_patterns: Dict[int, List[UserBehaviorPattern]] = defaultdict(list)
        self.execution_history: List[Dict[str, Any]] = []
        self.learning_enabled = True
        self.confidence_threshold = 0.7
        
    def add_rule(self, rule: AutomationRule) -> bool:
        """Add a new automation rule"""
        try:
            if rule.created_at is None:
                rule.created_at = datetime.now()
            
            if rule.learning_data is None:
                rule.learning_data = {
                    "pattern_matches": [],
                    "user_feedback": [],
                    "performance_metrics": {}
                }
            
            self.rules[rule.id] = rule
            logger.info(f"Added automation rule: {rule.name} ({rule.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add rule {rule.id}: {e}")
            return False
    
    def evaluate_file(self, file_info: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
        """
        Evaluate a file against all automation rules and return matching actions
        """
        matching_actions = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
                
            confidence = self._calculate_rule_confidence(rule, file_info)
            
            if confidence >= rule.confidence_threshold:
                # Record this match for learning
                self._record_rule_match(rule, file_info, confidence)
                
                # Prepare actions
                for action in rule.actions:
                    matching_actions.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "action": action,
                        "confidence": confidence,
                        "explanation": self._generate_explanation(rule, file_info),
                        "user_id": user_id
                    })
        
        # Sort by confidence and priority
        matching_actions.sort(key=lambda x: (x["confidence"], -x["action"].priority), reverse=True)
        return matching_actions
    
    def _calculate_rule_confidence(self, rule: AutomationRule, file_info: Dict[str, Any]) -> float:
        """Calculate confidence score for a rule matching a file"""
        if not rule.conditions:
            return 0.0
        
        total_weight = sum(condition.weight for condition in rule.conditions)
        if total_weight == 0:
            return 0.0
        
        matched_weight = 0.0
        
        for condition in rule.conditions:
            if self._evaluate_condition(condition, file_info):
                matched_weight += condition.weight
        
        base_confidence = matched_weight / total_weight
        
        # Adjust confidence based on rule performance history
        performance_factor = rule.success_rate
        
        # Consider execution frequency (rules that execute more often get slight boost)
        frequency_factor = min(1.1, 1.0 + (rule.execution_count / 1000))
        
        final_confidence = base_confidence * performance_factor * frequency_factor
        return min(1.0, final_confidence)
    
    def _evaluate_condition(self, condition: AutomationCondition, file_info: Dict[str, Any]) -> bool:
        """Evaluate a single condition against file information"""
        try:
            if condition.type == ConditionType.FILE_EXTENSION:
                file_ext = file_info.get("file_extension", "").lower()
                if condition.operator == "equals":
                    return file_ext == condition.value.lower()
                elif condition.operator == "in":
                    return file_ext in [ext.lower() for ext in condition.value]
                    
            elif condition.type == ConditionType.FILE_SIZE:
                file_size = file_info.get("file_size", 0)
                if condition.operator == "greater_than":
                    return file_size > condition.value
                elif condition.operator == "less_than":
                    return file_size < condition.value
                elif condition.operator == "equals":
                    return file_size == condition.value
                    
            elif condition.type == ConditionType.FILE_NAME_PATTERN:
                filename = file_info.get("file_name", "").lower()
                if condition.operator == "contains":
                    return condition.value.lower() in filename
                elif condition.operator == "regex":
                    return bool(re.search(condition.value, filename, re.IGNORECASE))
                elif condition.operator == "equals":
                    return filename == condition.value.lower()
                    
            elif condition.type == ConditionType.CONTENT_KEYWORDS:
                content = file_info.get("content", "").lower()
                if condition.operator == "contains":
                    keywords = condition.value if isinstance(condition.value, list) else [condition.value]
                    return any(keyword.lower() in content for keyword in keywords)
                    
            elif condition.type == ConditionType.FILE_AGE:
                file_date = file_info.get("created_at") or file_info.get("modified_at")
                if file_date:
                    if isinstance(file_date, str):
                        file_date = datetime.fromisoformat(file_date)
                    age_days = (datetime.now() - file_date).days
                    
                    if condition.operator == "greater_than":
                        return age_days > condition.value
                    elif condition.operator == "less_than":
                        return age_days < condition.value
                        
            elif condition.type == ConditionType.WORKSPACE:
                workspace_id = file_info.get("workspace_id")
                if condition.operator == "equals":
                    return workspace_id == condition.value
                elif condition.operator == "in":
                    return workspace_id in condition.value
                    
            elif condition.type == ConditionType.TAG_CONTAINS:
                tags = file_info.get("tags", [])
                if condition.operator == "contains":
                    search_tags = condition.value if isinstance(condition.value, list) else [condition.value]
                    return any(tag in tags for tag in search_tags)
                    
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating condition {condition.type}: {e}")
            return False
    
    def learn_from_user_behavior(self, user_id: int, action_data: Dict[str, Any]) -> None:
        """Learn from user actions to improve automation rules"""
        if not self.learning_enabled:
            return
        
        try:
            # Extract patterns from user behavior
            action_type = action_data.get("action_type")
            file_info = action_data.get("file_info", {})
            success = action_data.get("success", True)
            
            # Update user behavior patterns
            self._update_user_patterns(user_id, action_type, file_info, success)
            
            # Check if we should suggest new rules
            if self._should_suggest_new_rule(user_id, action_type):
                new_rule = self._generate_rule_from_patterns(user_id, action_type)
                if new_rule:
                    logger.info(f"Generated new rule suggestion for user {user_id}: {new_rule.name}")
                    # In practice, this would be saved as a suggestion for user approval
            
        except Exception as e:
            logger.error(f"Failed to learn from user behavior: {e}")
    
    def _update_user_patterns(self, user_id: int, action_type: str, file_info: Dict[str, Any], success: bool):
        """Update user behavior patterns"""
        # Find existing pattern or create new one
        existing_pattern = None
        for pattern in self.user_patterns[user_id]:
            if (pattern.action_type == action_type and 
                self._files_match_pattern(file_info, pattern.file_patterns)):
                existing_pattern = pattern
                break
        
        if existing_pattern:
            # Update existing pattern
            existing_pattern.frequency += 1
            existing_pattern.last_seen = datetime.now()
            if success:
                existing_pattern.success_rate = (
                    existing_pattern.success_rate * (existing_pattern.frequency - 1) + 1
                ) / existing_pattern.frequency
            else:
                existing_pattern.success_rate = (
                    existing_pattern.success_rate * (existing_pattern.frequency - 1)
                ) / existing_pattern.frequency
        else:
            # Create new pattern
            file_patterns = self._extract_file_patterns(file_info)
            new_pattern = UserBehaviorPattern(
                user_id=user_id,
                action_type=action_type,
                file_patterns=file_patterns,
                frequency=1,
                success_rate=1.0 if success else 0.0,
                last_seen=datetime.now(),
                context={"workspace_id": file_info.get("workspace_id")}
            )
            self.user_patterns[user_id].append(new_pattern)
    
    def _generate_rule_from_patterns(self, user_id: int, action_type: str) -> Optional[AutomationRule]:
        """Generate automation rule from user behavior patterns"""
        relevant_patterns = [
            p for p in self.user_patterns[user_id] 
            if p.action_type == action_type and p.frequency >= 3 and p.success_rate > 0.8
        ]
        
        if not relevant_patterns:
            return None
        
        # Analyze patterns to create conditions
        conditions = []
        
        # File extension patterns
        extensions = []
        for pattern in relevant_patterns:
            for file_pattern in pattern.file_patterns:
                if file_pattern.startswith("ext:"):
                    extensions.append(file_pattern[4:])
        
        if extensions:
            common_extensions = [ext for ext, count in Counter(extensions).items() if count >= 2]
            if common_extensions:
                conditions.append(AutomationCondition(
                    type=ConditionType.FILE_EXTENSION,
                    operator="in",
                    value=common_extensions,
                    weight=1.0
                ))
        
        # Workspace patterns
        workspaces = [p.context.get("workspace_id") for p in relevant_patterns if p.context.get("workspace_id")]
        if workspaces:
            common_workspace = Counter(workspaces).most_common(1)[0][0]
            conditions.append(AutomationCondition(
                type=ConditionType.WORKSPACE,
                operator="equals",
                value=common_workspace,
                weight=0.8
            ))
        
        if not conditions:
            return None
        
        # Create action based on action type
        actions = []
        if action_type == "move":
            # Analyze most common destination
            actions.append(AutomationAction(
                type=ActionType.MOVE,
                parameters={"destination": "auto-detected"},
                priority=1
            ))
        elif action_type == "tag":
            actions.append(AutomationAction(
                type=ActionType.TAG,
                parameters={"tags": ["auto-suggested"]},
                priority=2
            ))
        
        if not actions:
            return None
        
        # Generate rule
        rule_id = f"auto_{user_id}_{action_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return AutomationRule(
            id=rule_id,
            name=f"Auto-learned: {action_type.title()} files",
            description=f"Rule generated from user behavior patterns for {action_type}",
            conditions=conditions,
            actions=actions,
            confidence_threshold=0.6,  # Lower threshold for learned rules
            created_at=datetime.now()
        )
    
    def get_smart_suggestions(self, file_info: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
        """Get AI-powered suggestions for file handling"""
        suggestions = []
        
        # Get rule-based suggestions
        rule_suggestions = self.evaluate_file(file_info, user_id)
        suggestions.extend(rule_suggestions)
        
        # Get pattern-based suggestions
        pattern_suggestions = self._get_pattern_suggestions(file_info, user_id)
        suggestions.extend(pattern_suggestions)
        
        # Get content-based suggestions
        content_suggestions = self._get_content_suggestions(file_info)
        suggestions.extend(content_suggestions)
        
        # Remove duplicates and sort by confidence
        unique_suggestions = []
        seen_actions = set()
        
        for suggestion in sorted(suggestions, key=lambda x: x["confidence"], reverse=True):
            action_key = f"{suggestion['action'].type}_{suggestion['action'].parameters}"
            if action_key not in seen_actions:
                unique_suggestions.append(suggestion)
                seen_actions.add(action_key)
        
        return unique_suggestions[:5]  # Return top 5 suggestions
    
    def _get_pattern_suggestions(self, file_info: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
        """Get suggestions based on user behavior patterns"""
        suggestions = []
        
        file_patterns = self._extract_file_patterns(file_info)
        
        for pattern in self.user_patterns[user_id]:
            if (pattern.success_rate > 0.7 and 
                pattern.frequency >= 2 and
                self._files_match_pattern(file_info, pattern.file_patterns)):
                
                suggestions.append({
                    "rule_id": f"pattern_{pattern.action_type}",
                    "rule_name": f"Pattern-based {pattern.action_type}",
                    "action": AutomationAction(
                        type=ActionType(pattern.action_type),
                        parameters={"pattern_based": True}
                    ),
                    "confidence": pattern.success_rate * 0.8,  # Slightly lower than rule-based
                    "explanation": f"Based on your {pattern.frequency} similar actions with {pattern.success_rate:.1%} success",
                    "user_id": user_id
                })
        
        return suggestions
    
    def _get_content_suggestions(self, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get suggestions based on file content analysis"""
        suggestions = []
        
        content = file_info.get("content", "").lower()
        filename = file_info.get("file_name", "").lower()
        
        # Detect document types and suggest organization
        if any(word in content for word in ["invoice", "bill", "payment", "amount", "total"]):
            suggestions.append({
                "rule_id": "content_finance",
                "rule_name": "Content Analysis: Finance Document",
                "action": AutomationAction(
                    type=ActionType.TAG,
                    parameters={"tags": ["finance", "invoice", "auto-detected"]}
                ),
                "confidence": 0.85,
                "explanation": "Document appears to be financial based on content analysis",
                "user_id": None
            })
        
        if any(word in content for word in ["contract", "agreement", "terms", "conditions"]):
            suggestions.append({
                "rule_id": "content_legal",
                "rule_name": "Content Analysis: Legal Document",
                "action": AutomationAction(
                    type=ActionType.TAG,
                    parameters={"tags": ["legal", "contract", "auto-detected"]}
                ),
                "confidence": 0.82,
                "explanation": "Document appears to be legal based on content analysis",
                "user_id": None
            })
        
        if any(word in filename for word in ["screenshot", "screen", "capture"]):
            suggestions.append({
                "rule_id": "content_screenshot",
                "rule_name": "Content Analysis: Screenshot",
                "action": AutomationAction(
                    type=ActionType.ORGANIZE,
                    parameters={"folder": "Screenshots"}
                ),
                "confidence": 0.9,
                "explanation": "File appears to be a screenshot based on filename",
                "user_id": None
            })
        
        return suggestions
    
    def get_automation_analytics(self) -> Dict[str, Any]:
        """Get comprehensive automation analytics"""
        total_rules = len(self.rules)
        enabled_rules = sum(1 for rule in self.rules.values() if rule.enabled)
        total_executions = sum(rule.execution_count for rule in self.rules.values())
        
        # Calculate average success rate
        success_rates = [rule.success_rate for rule in self.rules.values() if rule.execution_count > 0]
        avg_success_rate = statistics.mean(success_rates) if success_rates else 0.0
        
        # Most active rules
        active_rules = sorted(
            [(rule.name, rule.execution_count) for rule in self.rules.values()],
            key=lambda x: x[1], reverse=True
        )[:5]
        
        # User behavior insights
        total_users = len(self.user_patterns)
        total_patterns = sum(len(patterns) for patterns in self.user_patterns.values())
        
        return {
            "rules": {
                "total": total_rules,
                "enabled": enabled_rules,
                "total_executions": total_executions,
                "average_success_rate": avg_success_rate
            },
            "most_active_rules": active_rules,
            "user_patterns": {
                "total_users": total_users,
                "total_patterns": total_patterns
            },
            "learning_enabled": self.learning_enabled,
            "confidence_threshold": self.confidence_threshold
        }
    
    # Helper methods
    def _extract_file_patterns(self, file_info: Dict[str, Any]) -> List[str]:
        """Extract searchable patterns from file info"""
        patterns = []
        
        if "file_extension" in file_info:
            patterns.append(f"ext:{file_info['file_extension']}")
        
        if "file_size" in file_info:
            size = file_info["file_size"]
            if size < 1024 * 1024:  # < 1MB
                patterns.append("size:small")
            elif size < 10 * 1024 * 1024:  # < 10MB
                patterns.append("size:medium")
            else:
                patterns.append("size:large")
        
        return patterns
    
    def _files_match_pattern(self, file_info: Dict[str, Any], patterns: List[str]) -> bool:
        """Check if file matches any of the given patterns"""
        file_patterns = self._extract_file_patterns(file_info)
        return any(pattern in file_patterns for pattern in patterns)
    
    def _should_suggest_new_rule(self, user_id: int, action_type: str) -> bool:
        """Determine if we should suggest a new rule based on user patterns"""
        relevant_patterns = [
            p for p in self.user_patterns[user_id]
            if p.action_type == action_type and p.frequency >= 3
        ]
        return len(relevant_patterns) > 0
    
    def _record_rule_match(self, rule: AutomationRule, file_info: Dict[str, Any], confidence: float):
        """Record that a rule matched for learning purposes"""
        if rule.learning_data is None:
            rule.learning_data = {"pattern_matches": []}
        
        rule.learning_data["pattern_matches"].append({
            "timestamp": datetime.now().isoformat(),
            "file_pattern": self._extract_file_patterns(file_info),
            "confidence": confidence
        })
        
        # Keep only recent matches (last 100)
        if len(rule.learning_data["pattern_matches"]) > 100:
            rule.learning_data["pattern_matches"] = rule.learning_data["pattern_matches"][-100:]
    
    def _generate_explanation(self, rule: AutomationRule, file_info: Dict[str, Any]) -> str:
        """Generate human-readable explanation for why a rule matched"""
        explanations = []
        
        for condition in rule.conditions:
            if self._evaluate_condition(condition, file_info):
                if condition.type == ConditionType.FILE_EXTENSION:
                    explanations.append(f"file extension is {file_info.get('file_extension', 'unknown')}")
                elif condition.type == ConditionType.FILE_NAME_PATTERN:
                    explanations.append(f"filename contains '{condition.value}'")
                elif condition.type == ConditionType.FILE_SIZE:
                    explanations.append(f"file size {condition.operator} {condition.value}")
        
        if explanations:
            return f"Rule matched because: {', '.join(explanations)}"
        else:
            return "Rule matched based on configured conditions"

# Global automation engine instance
automation_engine = SmartAutomationEngine()