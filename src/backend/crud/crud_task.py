from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, timezone
from src.backend.crud.base import CRUDBase
from src.backend.models.task import Task, Project, TaskStatus, TaskPriority
from src.backend.schemas.task import TaskCreate, TaskUpdate, ProjectCreate, ProjectUpdate

class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks for a specific user with eager loading"""
        return (
            db.query(Task)
            .options(
                joinedload(Task.workspace),
                joinedload(Task.project),
                joinedload(Task.subtasks)
            )
            .filter(Task.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_workspace(
        self, db: Session, *, workspace_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks for a specific workspace"""
        return db.query(Task).filter(Task.workspace_id == workspace_id).offset(skip).limit(limit).all()

    def get_by_project(
        self, db: Session, *, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks for a specific project"""
        return db.query(Task).filter(Task.project_id == project_id).offset(skip).limit(limit).all()

    def get_by_status(
        self, db: Session, *, user_id: int, status: TaskStatus, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks by status"""
        return db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == status
        ).offset(skip).limit(limit).all()

    def get_by_priority(
        self, db: Session, *, user_id: int, priority: TaskPriority, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks by priority"""
        return db.query(Task).filter(
            Task.user_id == user_id,
            Task.priority == priority
        ).offset(skip).limit(limit).all()

    def get_due_soon(
        self, db: Session, *, user_id: int, days: int = 7
    ) -> List[Task]:
        """Get tasks due within specified days"""
        due_date = datetime.now(timezone.utc) + timedelta(days=days)
        return db.query(Task).filter(
            Task.user_id == user_id,
            Task.due_date <= due_date,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        ).all()

    def get_overdue(self, db: Session, *, user_id: int) -> List[Task]:
        """Get overdue tasks"""
        now = datetime.now(timezone.utc)
        return db.query(Task).filter(
            Task.user_id == user_id,
            Task.due_date < now,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        ).all()

    def complete_task(self, db: Session, *, task_id: int) -> Optional[Task]:
        """Mark a task as completed"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(task)
        return task

    def search_tasks(
        self, db: Session, *, user_id: int, query: str, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Search tasks by title and description"""
        return db.query(Task).filter(
            Task.user_id == user_id,
            or_(
                Task.title.contains(query),
                Task.description.contains(query)
            )
        ).offset(skip).limit(limit).all()

class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """Get projects for a specific user"""
        return db.query(Project).filter(Project.user_id == user_id).offset(skip).limit(limit).all()

    def get_active_projects(
        self, db: Session, *, user_id: int
    ) -> List[Project]:
        """Get active projects for a user"""
        return db.query(Project).filter(
            Project.user_id == user_id,
            Project.is_active == True
        ).all()

    def get_project_with_tasks(self, db: Session, *, project_id: int) -> Optional[Project]:
        """Get project with all its tasks"""
        return db.query(Project).filter(Project.id == project_id).first()

task = CRUDTask(Task)
project = CRUDProject(Project)