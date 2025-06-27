"""
Workflow Collaboration and Sharing Service

This service handles workflow sharing, collaboration features, permissions,
and team-based workflow management.
"""

import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger

from src.backend.database.database import SessionLocal
from src.backend.crud.crud_workflow import crud_workflow
from src.backend.models.workflow import (
    Workflow, WorkflowShare, WorkflowExecution, WorkflowVersion
)
from src.backend.models.user import User
from src.backend.models.team import Team, TeamMembership
from src.backend.schemas.workflow import WorkflowShareCreate, WorkflowShareUpdate


class WorkflowCollaborationService:
    """Service for workflow collaboration and sharing"""
    
    def __init__(self):
        self.share_cache: Dict[str, Dict] = {}
    
    def share_workflow(
        self,
        workflow_id: int,
        shared_by: int,
        share_data: WorkflowShareCreate,
        db: Session
    ) -> WorkflowShare:
        """Share a workflow with users or teams"""
        # Validate workflow ownership/permissions
        workflow = crud_workflow.get(db, id=workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")
        
        # Check if sharer has permission to share
        if not self._can_share_workflow(workflow, shared_by, db):
            raise PermissionError("User does not have permission to share this workflow")
        
        # Create share record
        share_data_dict = share_data.dict()
        share_data_dict.update({
            "workflow_id": workflow_id,
            "shared_by": shared_by
        })
        
        # Generate public token if public link
        if share_data.is_public_link:
            share_data_dict["public_token"] = str(uuid.uuid4())
        
        share = WorkflowShare(**share_data_dict)
        db.add(share)
        db.commit()
        db.refresh(share)
        
        # Send notification to recipient
        if share_data.shared_with:
            self._send_share_notification(
                workflow, share, shared_by, share_data.shared_with, db
            )
        
        logger.info(f"Workflow {workflow_id} shared by user {shared_by}")
        return share
    
    def update_share_permissions(
        self,
        share_id: int,
        updates: WorkflowShareUpdate,
        user_id: int,
        db: Session
    ) -> WorkflowShare:
        """Update sharing permissions"""
        share = db.query(WorkflowShare).filter(WorkflowShare.id == share_id).first()
        if not share:
            raise ValueError("Share not found")
        
        # Check if user can modify this share
        if share.shared_by != user_id and not self._is_workflow_owner(share.workflow_id, user_id, db):
            raise PermissionError("User cannot modify this share")
        
        # Update share
        for field, value in updates.dict(exclude_unset=True).items():
            setattr(share, field, value)
        
        db.commit()
        db.refresh(share)
        
        logger.info(f"Share {share_id} permissions updated by user {user_id}")
        return share
    
    def revoke_share(
        self,
        share_id: int,
        user_id: int,
        db: Session
    ) -> bool:
        """Revoke workflow sharing"""
        share = db.query(WorkflowShare).filter(WorkflowShare.id == share_id).first()
        if not share:
            return False
        
        # Check if user can revoke this share
        if (share.shared_by != user_id and 
            share.shared_with != user_id and 
            not self._is_workflow_owner(share.workflow_id, user_id, db)):
            raise PermissionError("User cannot revoke this share")
        
        db.delete(share)
        db.commit()
        
        logger.info(f"Share {share_id} revoked by user {user_id}")
        return True
    
    def get_shared_workflows(
        self,
        user_id: int,
        db: Session,
        include_public: bool = False
    ) -> List[Dict]:
        """Get workflows shared with a user"""
        # Direct shares
        direct_shares = db.query(WorkflowShare).filter(
            or_(
                WorkflowShare.shared_with == user_id,
                and_(
                    WorkflowShare.is_public_link == True,
                    include_public
                )
            )
        ).all()
        
        # Team shares
        user_teams = db.query(TeamMembership).filter(
            TeamMembership.user_id == user_id
        ).all()
        
        team_shares = []
        if user_teams:
            team_ids = [tm.team_id for tm in user_teams]
            team_shares = db.query(WorkflowShare).filter(
                WorkflowShare.team_id.in_(team_ids)
            ).all()
        
        # Combine and format results
        all_shares = direct_shares + team_shares
        shared_workflows = []
        
        for share in all_shares:
            workflow = crud_workflow.get(db, id=share.workflow_id)
            if workflow:
                shared_workflows.append({
                    "share_id": share.id,
                    "workflow": {
                        "id": workflow.id,
                        "name": workflow.name,
                        "description": workflow.description,
                        "status": workflow.status.value
                    },
                    "permissions": {
                        "can_view": share.can_view,
                        "can_edit": share.can_edit,
                        "can_execute": share.can_execute,
                        "can_share": share.can_share
                    },
                    "shared_by": share.shared_by,
                    "shared_at": share.created_at,
                    "expires_at": share.expires_at,
                    "is_public_link": share.is_public_link,
                    "message": share.message
                })
        
        return shared_workflows
    
    def get_workflow_shares(
        self,
        workflow_id: int,
        user_id: int,
        db: Session
    ) -> List[Dict]:
        """Get all shares for a workflow"""
        # Check if user has permission to view shares
        if not self._can_view_workflow_shares(workflow_id, user_id, db):
            raise PermissionError("User cannot view shares for this workflow")
        
        shares = db.query(WorkflowShare).filter(
            WorkflowShare.workflow_id == workflow_id
        ).all()
        
        share_list = []
        for share in shares:
            share_info = {
                "id": share.id,
                "shared_with": None,
                "team_id": share.team_id,
                "permissions": {
                    "can_view": share.can_view,
                    "can_edit": share.can_edit,
                    "can_execute": share.can_execute,
                    "can_share": share.can_share
                },
                "shared_by": share.shared_by,
                "shared_at": share.created_at,
                "expires_at": share.expires_at,
                "is_public_link": share.is_public_link,
                "public_token": share.public_token if share.is_public_link else None,
                "message": share.message
            }
            
            # Add recipient info
            if share.shared_with:
                user = db.query(User).filter(User.id == share.shared_with).first()
                share_info["shared_with"] = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                } if user else None
            
            if share.team_id:
                team = db.query(Team).filter(Team.id == share.team_id).first()
                share_info["team"] = {
                    "id": team.id,
                    "name": team.name
                } if team else None
            
            share_list.append(share_info)
        
        return share_list
    
    def check_workflow_permissions(
        self,
        workflow_id: int,
        user_id: int,
        db: Session
    ) -> Dict[str, bool]:
        """Check user's permissions for a workflow"""
        # Check if user is owner
        workflow = crud_workflow.get(db, id=workflow_id)
        if not workflow:
            return {"can_view": False, "can_edit": False, "can_execute": False, "can_share": False}
        
        if workflow.created_by == user_id:
            return {"can_view": True, "can_edit": True, "can_execute": True, "can_share": True}
        
        # Check workspace access
        if self._has_workspace_access(workflow.workspace_id, user_id, db):
            return {"can_view": True, "can_edit": True, "can_execute": True, "can_share": True}
        
        # Check shares
        share = db.query(WorkflowShare).filter(
            and_(
                WorkflowShare.workflow_id == workflow_id,
                or_(
                    WorkflowShare.shared_with == user_id,
                    WorkflowShare.team_id.in_(
                        db.query(TeamMembership.team_id).filter(
                            TeamMembership.user_id == user_id
                        ).subquery()
                    )
                )
            )
        ).first()
        
        if share:
            return {
                "can_view": share.can_view,
                "can_edit": share.can_edit,
                "can_execute": share.can_execute,
                "can_share": share.can_share
            }
        
        return {"can_view": False, "can_edit": False, "can_execute": False, "can_share": False}
    
    def get_workflow_by_public_token(
        self,
        public_token: str,
        db: Session
    ) -> Optional[Dict]:
        """Get workflow by public sharing token"""
        share = db.query(WorkflowShare).filter(
            and_(
                WorkflowShare.public_token == public_token,
                WorkflowShare.is_public_link == True
            )
        ).first()
        
        if not share:
            return None
        
        # Check if share is expired
        if share.expires_at and share.expires_at < datetime.utcnow():
            return None
        
        workflow = crud_workflow.get(db, id=share.workflow_id)
        if not workflow:
            return None
        
        return {
            "workflow": {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "status": workflow.status.value
            },
            "permissions": {
                "can_view": share.can_view,
                "can_edit": share.can_edit,
                "can_execute": share.can_execute,
                "can_share": share.can_share
            },
            "share_info": {
                "shared_by": share.shared_by,
                "message": share.message,
                "expires_at": share.expires_at
            }
        }
    
    def create_workflow_collaboration_space(
        self,
        workflow_id: int,
        creator_id: int,
        team_members: List[int],
        db: Session
    ) -> Dict:
        """Create a collaboration space for a workflow"""
        workflow = crud_workflow.get(db, id=workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")
        
        if workflow.created_by != creator_id:
            raise PermissionError("Only workflow owner can create collaboration space")
        
        # Create team for collaboration
        from src.backend.models.team import Team, TeamMembership
        
        team = Team(
            name=f"Workflow Collaboration - {workflow.name}",
            description=f"Collaboration team for workflow: {workflow.name}",
            created_by=creator_id,
            workspace_id=workflow.workspace_id
        )
        db.add(team)
        db.flush()
        
        # Add team members
        memberships = []
        for member_id in team_members:
            membership = TeamMembership(
                team_id=team.id,
                user_id=member_id,
                role="collaborator",
                joined_at=datetime.utcnow()
            )
            db.add(membership)
            memberships.append(membership)
        
        # Share workflow with team
        team_share = WorkflowShare(
            workflow_id=workflow_id,
            shared_by=creator_id,
            team_id=team.id,
            can_view=True,
            can_edit=True,
            can_execute=True,
            can_share=False,
            message="Collaboration space created"
        )
        db.add(team_share)
        
        db.commit()
        db.refresh(team)
        
        logger.info(f"Collaboration space created for workflow {workflow_id}")
        
        return {
            "team_id": team.id,
            "team_name": team.name,
            "member_count": len(team_members),
            "share_id": team_share.id
        }
    
    def get_workflow_activity_feed(
        self,
        workflow_id: int,
        user_id: int,
        db: Session,
        limit: int = 50
    ) -> List[Dict]:
        """Get activity feed for a workflow"""
        # Check permissions
        permissions = self.check_workflow_permissions(workflow_id, user_id, db)
        if not permissions["can_view"]:
            raise PermissionError("User cannot view this workflow")
        
        activities = []
        
        # Get recent executions
        recent_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        ).order_by(WorkflowExecution.started_at.desc()).limit(limit).all()
        
        for execution in recent_executions:
            starter = db.query(User).filter(User.id == execution.started_by).first()
            
            activities.append({
                "type": "execution",
                "timestamp": execution.started_at,
                "user": {
                    "id": starter.id,
                    "username": starter.username
                } if starter else None,
                "data": {
                    "execution_id": execution.id,
                    "status": execution.status.value,
                    "completed_at": execution.completed_at
                }
            })
        
        # Get recent versions
        recent_versions = db.query(WorkflowVersion).filter(
            WorkflowVersion.workflow_id == workflow_id
        ).order_by(WorkflowVersion.created_at.desc()).limit(10).all()
        
        for version in recent_versions:
            creator = db.query(User).filter(User.id == version.created_by).first()
            
            activities.append({
                "type": "version",
                "timestamp": version.created_at,
                "user": {
                    "id": creator.id,
                    "username": creator.username
                } if creator else None,
                "data": {
                    "version_number": version.version_number,
                    "change_description": version.change_description
                }
            })
        
        # Get recent shares
        recent_shares = db.query(WorkflowShare).filter(
            WorkflowShare.workflow_id == workflow_id
        ).order_by(WorkflowShare.created_at.desc()).limit(10).all()
        
        for share in recent_shares:
            sharer = db.query(User).filter(User.id == share.shared_by).first()
            
            activities.append({
                "type": "share",
                "timestamp": share.created_at,
                "user": {
                    "id": sharer.id,
                    "username": sharer.username
                } if sharer else None,
                "data": {
                    "share_type": "public" if share.is_public_link else "private",
                    "permissions": {
                        "can_view": share.can_view,
                        "can_edit": share.can_edit,
                        "can_execute": share.can_execute
                    }
                }
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return activities[:limit]
    
    def get_collaboration_metrics(
        self,
        workflow_id: int,
        user_id: int,
        db: Session,
        days: int = 30
    ) -> Dict:
        """Get collaboration metrics for a workflow"""
        # Check permissions
        permissions = self.check_workflow_permissions(workflow_id, user_id, db)
        if not permissions["can_view"]:
            raise PermissionError("User cannot view this workflow")
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Count shares
        total_shares = db.query(WorkflowShare).filter(
            WorkflowShare.workflow_id == workflow_id
        ).count()
        
        # Count unique collaborators
        collaborator_ids = set()
        
        # From shares
        shares = db.query(WorkflowShare).filter(
            WorkflowShare.workflow_id == workflow_id
        ).all()
        
        for share in shares:
            if share.shared_with:
                collaborator_ids.add(share.shared_with)
            if share.team_id:
                team_members = db.query(TeamMembership).filter(
                    TeamMembership.team_id == share.team_id
                ).all()
                collaborator_ids.update(tm.user_id for tm in team_members)
        
        # From executions
        recent_executions = db.query(WorkflowExecution).filter(
            and_(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.started_at >= start_date
            )
        ).all()
        
        execution_users = set(e.started_by for e in recent_executions if e.started_by)
        
        return {
            "total_shares": total_shares,
            "unique_collaborators": len(collaborator_ids),
            "recent_executions": len(recent_executions),
            "unique_executors": len(execution_users),
            "public_shares": len([s for s in shares if s.is_public_link]),
            "team_shares": len([s for s in shares if s.team_id]),
            "analysis_period_days": days
        }
    
    # Helper methods
    def _can_share_workflow(self, workflow: Workflow, user_id: int, db: Session) -> bool:
        """Check if user can share a workflow"""
        # Owner can always share
        if workflow.created_by == user_id:
            return True
        
        # Check if user has share permission through existing share
        share = db.query(WorkflowShare).filter(
            and_(
                WorkflowShare.workflow_id == workflow.id,
                or_(
                    WorkflowShare.shared_with == user_id,
                    WorkflowShare.team_id.in_(
                        db.query(TeamMembership.team_id).filter(
                            TeamMembership.user_id == user_id
                        ).subquery()
                    )
                ),
                WorkflowShare.can_share == True
            )
        ).first()
        
        return share is not None
    
    def _is_workflow_owner(self, workflow_id: int, user_id: int, db: Session) -> bool:
        """Check if user is workflow owner"""
        workflow = crud_workflow.get(db, id=workflow_id)
        return workflow and workflow.created_by == user_id
    
    def _can_view_workflow_shares(self, workflow_id: int, user_id: int, db: Session) -> bool:
        """Check if user can view workflow shares"""
        # Owner can always view shares
        if self._is_workflow_owner(workflow_id, user_id, db):
            return True
        
        # Check if user has any share for this workflow
        share = db.query(WorkflowShare).filter(
            and_(
                WorkflowShare.workflow_id == workflow_id,
                or_(
                    WorkflowShare.shared_with == user_id,
                    WorkflowShare.team_id.in_(
                        db.query(TeamMembership.team_id).filter(
                            TeamMembership.user_id == user_id
                        ).subquery()
                    )
                )
            )
        ).first()
        
        return share is not None
    
    def _has_workspace_access(self, workspace_id: int, user_id: int, db: Session) -> bool:
        """Check if user has access to workspace"""
        from src.backend.models.workspace import Workspace
        from src.backend.models.team import WorkspaceShare as WSShare
        
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            return False
        
        # Owner has access
        if workspace.owner_id == user_id:
            return True
        
        # Check workspace shares
        ws_share = db.query(WSShare).filter(
            and_(
                WSShare.workspace_id == workspace_id,
                WSShare.user_id == user_id
            )
        ).first()
        
        return ws_share is not None
    
    def _send_share_notification(
        self,
        workflow: Workflow,
        share: WorkflowShare,
        shared_by: int,
        shared_with: int,
        db: Session
    ) -> None:
        """Send notification about workflow share"""
        # This would integrate with notification system
        logger.info(f"Workflow share notification sent: workflow {workflow.id} shared with user {shared_with}")


# Global collaboration service instance
workflow_collaboration = WorkflowCollaborationService()