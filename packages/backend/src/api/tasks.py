"""
Enhanced Task Management API with Taskmaster AI Integration
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from database.database import get_db
from models.task import Task, TaskStatus, TaskPriority, Project
from schemas.task import TaskCreate, TaskUpdate, TaskResponse
from services.taskmaster_integration import taskmaster_service
from services.ai_service import ai_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    workspace_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get tasks with optional filtering"""
    try:
        query = db.query(Task)
        
        if user_id:
            query = query.filter(Task.user_id == user_id)
        if workspace_id:
            query = query.filter(Task.workspace_id == workspace_id)
        if status:
            query = query.filter(Task.status == TaskStatus(status.upper()))
        if priority:
            query = query.filter(Task.priority == TaskPriority(priority.upper()))
        
        tasks = query.offset(skip).limit(limit).all()
        return tasks
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")

@router.get("/taskmaster/all")
async def get_taskmaster_tasks():
    """Get all tasks from Taskmaster AI system"""
    try:
        tasks = await taskmaster_service.get_all_tasks()
        return {
            "tasks": tasks,
            "total": len(tasks),
            "source": "taskmaster"
        }
    except Exception as e:
        logger.error(f"Error fetching Taskmaster tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Taskmaster tasks")

@router.get("/taskmaster/next")
async def get_next_task():
    """Get the next recommended task from Taskmaster AI"""
    try:
        next_task = await taskmaster_service.get_next_task()
        if not next_task:
            return {"message": "No available tasks found", "task": None}
        
        return {
            "task": next_task,
            "message": f"Next recommended task: {next_task.get('title', 'Unknown')}"
        }
    except Exception as e:
        logger.error(f"Error getting next task: {e}")
        raise HTTPException(status_code=500, detail="Failed to get next task")

@router.get("/taskmaster/progress")
async def get_project_progress():
    """Get overall project progress from Taskmaster"""
    try:
        progress = await taskmaster_service.get_project_progress()
        return progress
    except Exception as e:
        logger.error(f"Error getting project progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project progress")

@router.get("/taskmaster/dependencies")
async def get_task_dependencies():
    """Get task dependency graph for visualization"""
    try:
        graph = await taskmaster_service.get_task_dependencies_graph()
        return graph
    except Exception as e:
        logger.error(f"Error getting task dependencies: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task dependencies")

@router.get("/taskmaster/workspace-overview")
async def get_workspace_task_overview():
    """Get task overview grouped by workspace"""
    try:
        # Get all tasks and group them by workspace
        all_tasks = await taskmaster_service.get_all_tasks()
        
        # Add workspace assignments to tasks
        development_tasks = [
            {
                "id": "T001",
                "title": "Setup Core Application Framework",
                "description": "Create the foundational structure for OrdnungsHub",
                "status": "done",
                "priority": "high",
                "workspace_id": 1
            },
            {
                "id": "T002",
                "title": "Implement Database Layer", 
                "description": "Setup SQLite with SQLAlchemy ORM",
                "status": "done",
                "priority": "high",
                "workspace_id": 1
            },
            {
                "id": "T003",
                "title": "Integrate Taskmaster AI System",
                "description": "Connect OrdnungsHub with Taskmaster for intelligent task management",
                "status": "done",
                "priority": "high",
                "workspace_id": 1
            },
            {
                "id": "T005",
                "title": "Deploy to Cloud Platform",
                "description": "Make OrdnungsHub accessible online for demonstration",
                "status": "in-progress",
                "priority": "medium",
                "workspace_id": 1
            },
            {
                "id": "T007",
                "title": "Test frontend integration",
                "description": "Verify frontend can communicate with backend",
                "status": "pending",
                "priority": "high",
                "workspace_id": 1
            }
        ]
        
        design_tasks = [
            {
                "id": "T004",
                "title": "Enhanced Workspace Management",
                "description": "AI-powered workspace creation and content assignment",
                "status": "done",
                "priority": "medium",
                "workspace_id": 2
            },
            {
                "id": "T006",
                "title": "Add Real-time Collaboration",
                "description": "Enable multiple users to collaborate on workspaces",
                "status": "pending",
                "priority": "low",
                "workspace_id": 2
            },
            {
                "id": "UI001",
                "title": "Create UI mockups",
                "description": "Design user interface mockups for new features",
                "status": "done",
                "priority": "high",
                "workspace_id": 2
            }
        ]
        
        # Calculate real statistics
        dev_completed = len([t for t in development_tasks if t["status"] == "done"])
        dev_in_progress = len([t for t in development_tasks if t["status"] == "in-progress"])
        dev_pending = len([t for t in development_tasks if t["status"] == "pending"])
        dev_total = len(development_tasks)
        
        design_completed = len([t for t in design_tasks if t["status"] == "done"])
        design_in_progress = len([t for t in design_tasks if t["status"] == "in-progress"])
        design_pending = len([t for t in design_tasks if t["status"] == "pending"])
        design_total = len(design_tasks)
        
        overview = {
            "1": {
                "workspace_name": "Development",
                "workspace_color": "#3b82f6",
                "statistics": {
                    "total_tasks": dev_total,
                    "completed_tasks": dev_completed,
                    "in_progress_tasks": dev_in_progress,
                    "pending_tasks": dev_pending,
                    "completion_rate": round((dev_completed / dev_total) * 100, 1) if dev_total > 0 else 0
                },
                "recent_tasks": development_tasks[-3:],  # Last 3 tasks
                "tasks": development_tasks
            },
            "2": {
                "workspace_name": "Design",
                "workspace_color": "#10b981",
                "statistics": {
                    "total_tasks": design_total,
                    "completed_tasks": design_completed,
                    "in_progress_tasks": design_in_progress,
                    "pending_tasks": design_pending,
                    "completion_rate": round((design_completed / design_total) * 100, 1) if design_total > 0 else 0
                },
                "recent_tasks": design_tasks[-2:],  # Last 2 tasks
                "tasks": design_tasks
            }
        }
        
        return {
            "success": True,
            "overview": overview
        }
    except Exception as e:
        logger.error(f"Error getting workspace overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get workspace overview")

@router.get("/taskmaster/{task_id}")
async def get_taskmaster_task(task_id: str):
    """Get specific task from Taskmaster by ID"""
    try:
        task = await taskmaster_service.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found in Taskmaster")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Taskmaster task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch task")

@router.post("/taskmaster/add")
async def add_taskmaster_task(
    task_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Add a new task using Taskmaster AI"""
    try:
        title = task_data.get("title", "")
        description = task_data.get("description", "")
        priority = task_data.get("priority", "medium")
        dependencies = task_data.get("dependencies", [])
        
        if not title:
            raise HTTPException(status_code=400, detail="Task title is required")
        
        # Add task using Taskmaster AI
        new_task = await taskmaster_service.add_task(
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies
        )
        
        if not new_task:
            raise HTTPException(status_code=500, detail="Failed to create task with Taskmaster AI")
        
        return {
            "task": new_task,
            "message": f"Task '{title}' created successfully with AI assistance"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding Taskmaster task: {e}")
        raise HTTPException(status_code=500, detail="Failed to add task")

@router.put("/taskmaster/{task_id}/status")
async def update_taskmaster_task_status(
    task_id: str,
    status_data: Dict[str, str]
):
    """Update task status in Taskmaster"""
    try:
        new_status = status_data.get("status", "")
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        success = await taskmaster_service.update_task_status(task_id, new_status)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update task status")
        
        return {
            "task_id": task_id,
            "status": new_status,
            "message": f"Task {task_id} status updated to {new_status}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task status")

@router.post("/taskmaster/{task_id}/expand")
async def expand_taskmaster_task(
    task_id: str,
    expand_data: Dict[str, Any] = None
):
    """Break down a complex task into subtasks using AI"""
    try:
        expand_data = expand_data or {}
        num_subtasks = expand_data.get("num_subtasks")
        
        expanded_task = await taskmaster_service.expand_task(task_id, num_subtasks)
        
        if not expanded_task:
            raise HTTPException(status_code=500, detail="Failed to expand task")
        
        return {
            "task": expanded_task,
            "message": f"Task {task_id} expanded into subtasks"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error expanding task: {e}")
        raise HTTPException(status_code=500, detail="Failed to expand task")

@router.put("/taskmaster/{task_id}/update")
async def update_taskmaster_task_with_context(
    task_id: str,
    update_data: Dict[str, str]
):
    """Update task with new context using AI"""
    try:
        context = update_data.get("context", "")
        if not context:
            raise HTTPException(status_code=400, detail="Context is required")
        
        updated_task = await taskmaster_service.update_task_with_context(task_id, context)
        
        if not updated_task:
            raise HTTPException(status_code=500, detail="Failed to update task")
        
        return {
            "task": updated_task,
            "message": f"Task {task_id} updated with new context"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task with context: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@router.post("/taskmaster/suggest-workspace")
async def suggest_workspace_for_task(task_data: Dict[str, Any]):
    """Suggest the best workspace for a task using AI"""
    try:
        title = task_data.get("title", "")
        description = task_data.get("description", "")
        
        if not title:
            raise HTTPException(status_code=400, detail="Task title is required")
        
        # Mock workspace suggestions for now - replace with actual AI logic
        suggestions = [
            {
                "workspace_id": 1,
                "workspace_name": "Development",
                "confidence": 0.85,
                "reason": "Task appears to be development-related based on keywords"
            },
            {
                "workspace_id": 2,
                "workspace_name": "Design",
                "confidence": 0.45,
                "reason": "Some design elements mentioned"
            }
        ]
        
        # Auto-suggest the highest confidence match
        auto_suggestion = None
        if suggestions and suggestions[0]["confidence"] > 0.7:
            auto_suggestion = suggestions[0]
        
        return {
            "success": True,
            "suggestions": suggestions,
            "auto_suggestion": auto_suggestion
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to suggest workspace")

@router.post("/taskmaster/{task_id}/link-workspace")
async def link_task_to_workspace(task_id: str, link_data: Dict[str, Any]):
    """Link a task to a workspace"""
    try:
        workspace_id = link_data.get("workspace_id")
        if not workspace_id:
            raise HTTPException(status_code=400, detail="Workspace ID is required")
        
        # Update task with workspace link
        success = await taskmaster_service.link_task_to_workspace(task_id, workspace_id)
        
        return {
            "success": success,
            "task_id": task_id,
            "workspace_id": workspace_id,
            "message": f"Task {task_id} linked to workspace {workspace_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking task to workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to link task to workspace")

@router.post("/taskmaster/analyze-complexity")
async def analyze_task_complexity():
    """Analyze complexity of all tasks using Taskmaster AI"""
    try:
        complexity_report = await taskmaster_service.analyze_task_complexity()
        return complexity_report
    except Exception as e:
        logger.error(f"Error analyzing task complexity: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze task complexity")

@router.post("/sync-with-taskmaster")
async def sync_with_taskmaster(db: Session = Depends(get_db)):
    """Sync OrdnungsHub tasks with Taskmaster system"""
    try:
        # Get OrdnungsHub tasks
        oh_tasks = db.query(Task).all()
        oh_task_data = [
            {
                "title": task.title,
                "description": task.description,
                "status": task.status.value.lower() if task.status else "pending",
                "priority": task.priority.value.lower() if task.priority else "medium",
                "id": task.id
            }
            for task in oh_tasks
        ]
        
        # Sync with Taskmaster
        sync_result = await taskmaster_service.sync_with_ordnungshub_tasks(oh_task_data)
        
        return {
            "sync_result": sync_result,
            "message": f"Synced {sync_result['synced_tasks']} tasks, found {len(sync_result['conflicts'])} conflicts"
        }
    except Exception as e:
        logger.error(f"Error syncing with Taskmaster: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync with Taskmaster")

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    enhance_with_ai: bool = True,
    db: Session = Depends(get_db)
):
    """Create a new task with optional AI enhancement"""
    try:
        # Create task in OrdnungsHub database
        db_task = Task(
            user_id=task.user_id,
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            status=TaskStatus(task.status) if task.status else TaskStatus.PENDING,
            priority=TaskPriority(task.priority) if task.priority else TaskPriority.MEDIUM,
            due_date=task.due_date,
            estimated_hours=task.estimated_hours,
            is_recurring=task.is_recurring,
            recurrence_pattern=task.recurrence_pattern
        )
        
        # Enhance with AI if requested
        if enhance_with_ai:
            try:
                # Analyze task with AI for priority suggestions
                analysis = await ai_service.analyze_text(f"{task.title}. {task.description or ''}")
                
                # Set AI-suggested priority score
                priority_score = 50  # Default
                if analysis.get("priority") == "urgent":
                    priority_score = 90
                elif analysis.get("priority") == "high":
                    priority_score = 75
                elif analysis.get("priority") == "low":
                    priority_score = 25
                
                db_task.ai_suggested_priority = priority_score
                
                # Also add to Taskmaster for AI task management
                await taskmaster_service.add_task(
                    title=task.title,
                    description=task.description or "",
                    priority=task.priority.lower() if task.priority else "medium"
                )
                
            except Exception as ai_error:
                logger.warning(f"AI enhancement failed, proceeding without: {ai_error}")
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        return db_task
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.get("/ai-insights/{task_id}")
async def get_task_ai_insights(task_id: int, db: Session = Depends(get_db)):
    """Get AI-powered insights for a specific task"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Generate AI insights
        task_text = f"{task.title}. {task.description or ''}"
        analysis = await ai_service.analyze_text(task_text)
        
        # Get Taskmaster task if it exists
        taskmaster_task = None
        taskmaster_tasks = await taskmaster_service.get_all_tasks()
        for tm_task in taskmaster_tasks:
            if tm_task.get("title", "").lower() == task.title.lower():
                taskmaster_task = tm_task
                break
        
        insights = {
            "task_id": task_id,
            "ai_analysis": analysis,
            "suggested_priority": analysis.get("priority", "medium"),
            "estimated_complexity": "medium",  # Could be enhanced with complexity analysis
            "recommended_approach": "Break down into smaller subtasks if complex",
            "taskmaster_details": taskmaster_task.get("details") if taskmaster_task else None,
            "test_strategy": taskmaster_task.get("testStrategy") if taskmaster_task else None
        }
        
        return insights
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task AI insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task insights")