"""
Enhanced CRUD operations for collaborative workspace and task management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
import json
import secrets
import string

from ..models.team import (
    Team, TeamMembership, WorkspaceShare, TaskAssignment, 
    WorkspaceActivity, TaskComment, WorkspaceInvite,
    TeamRole, WorkspacePermission
)
from ..models.workspace import Workspace
from ..models.task import Task
from ..models.user import User

class CollaborationCRUD:
    """Enhanced CRUD operations for collaborative features"""
    
    # Team Management
    def create_team(self, db: Session, team_data: dict, creator_id: int) -> Team:
        """Create a new team"""
        invite_code = self._generate_invite_code()
        
        team = Team(
            name=team_data["name"],
            description=team_data.get("description"),
            created_by=creator_id,
            max_members=team_data.get("max_members", 50),
            is_public=team_data.get("is_public", False),
            invite_code=invite_code
        )
        
        db.add(team)
        db.flush()
        
        # Add creator as owner
        membership = TeamMembership(
            team_id=team.id,
            user_id=creator_id,
            role=TeamRole.OWNER
        )
        db.add(membership)
        db.commit()
        
        return team
    
    def add_team_member(self, db: Session, team_id: int, user_id: int, 
                       role: TeamRole = TeamRole.MEMBER, invited_by: int = None) -> TeamMembership:
        """Add a user to a team"""
        # Check if user is already a member
        existing = db.query(TeamMembership).filter(
            and_(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == user_id,
                TeamMembership.is_active == True
            )
        ).first()
        
        if existing:
            return existing
        
        membership = TeamMembership(
            team_id=team_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by
        )
        
        db.add(membership)
        db.commit()
        
        return membership
    
    def get_user_teams(self, db: Session, user_id: int) -> List[Team]:
        """Get all teams a user is a member of"""
        return db.query(Team).join(TeamMembership).filter(
            and_(
                TeamMembership.user_id == user_id,
                TeamMembership.is_active == True,
                Team.is_active == True
            )
        ).all()
    
    def get_team_members(self, db: Session, team_id: int) -> List[Dict[str, Any]]:
        """Get all members of a team with their roles"""
        members = db.query(User, TeamMembership).join(TeamMembership).filter(
            and_(
                TeamMembership.team_id == team_id,
                TeamMembership.is_active == True
            )
        ).all()
        
        return [
            {
                "user": user,
                "role": membership.role,
                "joined_at": membership.joined_at,
                "invited_by": membership.invited_by
            }
            for user, membership in members
        ]
    
    # Workspace Sharing
    def share_workspace(self, db: Session, workspace_id: int, shared_by: int,
                       user_id: int = None, team_id: int = None,
                       permissions: List[WorkspacePermission] = None,
                       expires_in_days: int = None) -> WorkspaceShare:
        """Share a workspace with a user or team"""
        if not permissions:
            permissions = [WorkspacePermission.READ, WorkspacePermission.WRITE]
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        share = WorkspaceShare(
            workspace_id=workspace_id,
            shared_with_user_id=user_id,
            shared_with_team_id=team_id,
            permissions=json.dumps([p.value for p in permissions]),
            shared_by=shared_by,
            expires_at=expires_at
        )
        
        db.add(share)
        db.commit()
        
        # Log activity
        self._log_workspace_activity(
            db, workspace_id, shared_by, 
            "shared", f"Workspace shared with {'user' if user_id else 'team'}"
        )
        
        return share
    
    def get_user_accessible_workspaces(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get all workspaces a user has access to (owned or shared)"""
        # Owned workspaces
        owned = db.query(Workspace).filter(Workspace.user_id == user_id).all()
        
        # Directly shared workspaces
        direct_shares = db.query(Workspace, WorkspaceShare).join(WorkspaceShare).filter(
            and_(
                WorkspaceShare.shared_with_user_id == user_id,
                WorkspaceShare.is_active == True,
                or_(
                    WorkspaceShare.expires_at.is_(None),
                    WorkspaceShare.expires_at > datetime.utcnow()
                )
            )
        ).all()
        
        # Team shared workspaces
        user_teams = self.get_user_teams(db, user_id)
        team_ids = [team.id for team in user_teams]
        
        team_shares = []
        if team_ids:
            team_shares = db.query(Workspace, WorkspaceShare).join(WorkspaceShare).filter(
                and_(
                    WorkspaceShare.shared_with_team_id.in_(team_ids),
                    WorkspaceShare.is_active == True,
                    or_(
                        WorkspaceShare.expires_at.is_(None),
                        WorkspaceShare.expires_at > datetime.utcnow()
                    )
                )
            ).all()
        
        result = []
        
        # Add owned workspaces
        for workspace in owned:
            result.append({
                "workspace": workspace,
                "access_type": "owner",
                "permissions": ["read", "write", "delete", "share", "admin"]
            })
        
        # Add shared workspaces
        for workspace, share in direct_shares + team_shares:
            result.append({
                "workspace": workspace,
                "access_type": "shared",
                "permissions": json.loads(share.permissions),
                "shared_by": share.shared_by,
                "shared_at": share.shared_at
            })
        
        return result
    
    # Task Assignment
    def assign_task(self, db: Session, task_id: int, assigned_to: int, 
                   assigned_by: int, role: str = "collaborator",
                   estimated_hours: int = None) -> TaskAssignment:
        """Assign a task to a user"""
        # Check if already assigned
        existing = db.query(TaskAssignment).filter(
            and_(
                TaskAssignment.task_id == task_id,
                TaskAssignment.assigned_to == assigned_to,
                TaskAssignment.is_active == True
            )
        ).first()
        
        if existing:
            return existing
        
        assignment = TaskAssignment(
            task_id=task_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            role=role,
            estimated_hours=estimated_hours
        )
        
        db.add(assignment)
        db.commit()
        
        # Log activity
        task = db.query(Task).filter(Task.id == task_id).first()
        if task and task.workspace_id:
            self._log_workspace_activity(
                db, task.workspace_id, assigned_by,
                "task_assigned", f"Task assigned to user {assigned_to}"
            )
        
        return assignment
    
    def get_user_assigned_tasks(self, db: Session, user_id: int, 
                              status: str = None) -> List[Dict[str, Any]]:
        """Get all tasks assigned to a user"""
        query = db.query(Task, TaskAssignment).join(TaskAssignment).filter(
            and_(
                TaskAssignment.assigned_to == user_id,
                TaskAssignment.is_active == True
            )
        )
        
        if status:
            query = query.filter(Task.status == status)
        
        assignments = query.all()
        
        return [
            {
                "task": task,
                "assignment": assignment,
                "role": assignment.role,
                "assigned_at": assignment.assigned_at,
                "completion_percentage": assignment.completion_percentage
            }
            for task, assignment in assignments
        ]
    
    def update_task_progress(self, db: Session, task_id: int, user_id: int,
                           completion_percentage: int, actual_hours: int = None) -> TaskAssignment:
        """Update task completion progress"""
        assignment = db.query(TaskAssignment).filter(
            and_(
                TaskAssignment.task_id == task_id,
                TaskAssignment.assigned_to == user_id,
                TaskAssignment.is_active == True
            )
        ).first()
        
        if assignment:
            assignment.completion_percentage = completion_percentage
            if actual_hours:
                assignment.actual_hours = actual_hours
            if completion_percentage == 100:
                assignment.completed_at = datetime.utcnow()
            
            db.commit()
        
        return assignment
    
    # Comments and Collaboration
    def add_task_comment(self, db: Session, task_id: int, user_id: int,
                        content: str, comment_type: str = "comment",
                        parent_comment_id: int = None,
                        mentions: List[int] = None) -> TaskComment:
        """Add a comment to a task"""
        comment = TaskComment(
            task_id=task_id,
            user_id=user_id,
            content=content,
            comment_type=comment_type,
            parent_comment_id=parent_comment_id,
            mentions=json.dumps(mentions) if mentions else None
        )
        
        db.add(comment)
        db.commit()
        
        # Log activity
        task = db.query(Task).filter(Task.id == task_id).first()
        if task and task.workspace_id:
            self._log_workspace_activity(
                db, task.workspace_id, user_id,
                "task_commented", f"Comment added to task {task_id}"
            )
        
        return comment
    
    def get_task_comments(self, db: Session, task_id: int) -> List[Dict[str, Any]]:
        """Get all comments for a task with user information"""
        comments = db.query(TaskComment, User).join(User).filter(
            and_(
                TaskComment.task_id == task_id,
                TaskComment.is_deleted == False
            )
        ).order_by(TaskComment.created_at).all()
        
        return [
            {
                "comment": comment,
                "user": user,
                "mentions": json.loads(comment.mentions) if comment.mentions else []
            }
            for comment, user in comments
        ]
    
    # Workspace Invitations
    def create_workspace_invite(self, db: Session, workspace_id: int, invited_by: int,
                              invited_email: str = None, invited_user_id: int = None,
                              permissions: List[WorkspacePermission] = None,
                              expires_in_days: int = 7, message: str = None) -> WorkspaceInvite:
        """Create a workspace invitation"""
        if not permissions:
            permissions = [WorkspacePermission.READ, WorkspacePermission.WRITE]
        
        invite_code = self._generate_invite_code(length=32)
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        invite = WorkspaceInvite(
            workspace_id=workspace_id,
            invited_by=invited_by,
            invited_user_id=invited_user_id,
            invited_email=invited_email,
            permissions=json.dumps([p.value for p in permissions]),
            invite_code=invite_code,
            expires_at=expires_at,
            message=message
        )
        
        db.add(invite)
        db.commit()
        
        return invite
    
    def accept_workspace_invite(self, db: Session, invite_code: str, user_id: int) -> WorkspaceShare:
        """Accept a workspace invitation"""
        invite = db.query(WorkspaceInvite).filter(
            and_(
                WorkspaceInvite.invite_code == invite_code,
                WorkspaceInvite.status == "pending",
                WorkspaceInvite.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not invite:
            raise ValueError("Invalid or expired invitation")
        
        # Create workspace share
        share = WorkspaceShare(
            workspace_id=invite.workspace_id,
            shared_with_user_id=user_id,
            permissions=invite.permissions,
            shared_by=invite.invited_by
        )
        
        db.add(share)
        
        # Update invite status
        invite.status = "accepted"
        invite.accepted_at = datetime.utcnow()
        
        db.commit()
        
        return share
    
    # Activity Logging
    def _log_workspace_activity(self, db: Session, workspace_id: int, user_id: int,
                               action_type: str, description: str,
                               entity_type: str = None, entity_id: int = None,
                               metadata: dict = None):
        """Log workspace activity"""
        activity = WorkspaceActivity(
            workspace_id=workspace_id,
            user_id=user_id,
            action_type=action_type,
            action_description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        db.add(activity)
        db.commit()
    
    def get_workspace_activity(self, db: Session, workspace_id: int, 
                             limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent workspace activity"""
        activities = db.query(WorkspaceActivity, User).join(User).filter(
            WorkspaceActivity.workspace_id == workspace_id
        ).order_by(desc(WorkspaceActivity.created_at)).limit(limit).all()
        
        return [
            {
                "activity": activity,
                "user": user,
                "metadata": json.loads(activity.metadata) if activity.metadata else {}
            }
            for activity, user in activities
        ]
    
    # Analytics and Insights
    def get_workspace_analytics(self, db: Session, workspace_id: int) -> Dict[str, Any]:
        """Get comprehensive workspace analytics"""
        # Basic counts
        total_tasks = db.query(Task).filter(Task.workspace_id == workspace_id).count()
        completed_tasks = db.query(Task).filter(
            and_(Task.workspace_id == workspace_id, Task.status == "completed")
        ).count()
        
        # User participation
        active_users = db.query(func.count(func.distinct(WorkspaceActivity.user_id))).filter(
            and_(
                WorkspaceActivity.workspace_id == workspace_id,
                WorkspaceActivity.created_at > datetime.utcnow() - timedelta(days=30)
            )
        ).scalar()
        
        # Task assignments
        total_assignments = db.query(TaskAssignment).join(Task).filter(
            and_(
                Task.workspace_id == workspace_id,
                TaskAssignment.is_active == True
            )
        ).count()
        
        # Recent activity
        recent_activities = self.get_workspace_activity(db, workspace_id, 10)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "active_users": active_users,
            "total_assignments": total_assignments,
            "recent_activity": recent_activities
        }
    
    # Utility functions
    def _generate_invite_code(self, length: int = 12) -> str:
        """Generate a secure invite code"""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

# Create singleton instance
collaboration_crud = CollaborationCRUD()