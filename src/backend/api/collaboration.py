"""
Enhanced API endpoints for collaborative workspace and task management
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime

from ..database import get_db
from ..crud.crud_collaboration import collaboration_crud
from ..models.team import TeamRole, WorkspacePermission
from ..models.user import User
from ..dependencies.auth import get_current_active_user

router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])

# Pydantic Models for Request/Response
class TeamCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    max_members: int = 50
    is_public: bool = False

class TeamMemberInvite(BaseModel):
    user_id: Optional[int] = None
    email: Optional[EmailStr] = None
    role: TeamRole = TeamRole.MEMBER

class WorkspaceShareRequest(BaseModel):
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    permissions: List[WorkspacePermission] = [WorkspacePermission.READ, WorkspacePermission.WRITE]
    expires_in_days: Optional[int] = None

class TaskAssignmentRequest(BaseModel):
    assigned_to: int
    role: str = "collaborator"
    estimated_hours: Optional[int] = None

class TaskCommentRequest(BaseModel):
    content: str
    comment_type: str = "comment"
    parent_comment_id: Optional[int] = None
    mentions: Optional[List[int]] = None

class WorkspaceInviteRequest(BaseModel):
    invited_email: Optional[EmailStr] = None
    invited_user_id: Optional[int] = None
    permissions: List[WorkspacePermission] = [WorkspacePermission.READ, WorkspacePermission.WRITE]
    expires_in_days: int = 7
    message: Optional[str] = None

class TaskProgressUpdate(BaseModel):
    completion_percentage: int
    actual_hours: Optional[int] = None

# Team Management Endpoints
@router.post("/teams", response_model=dict)
async def create_team(
    team_data: TeamCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    try:
        team = collaboration_crud.create_team(
            db=db,
            team_data=team_data.dict(),
            creator_id=current_user.id
        )
        
        return {
            "success": True,
            "team": {
                "id": team.id,
                "name": team.name,
                "description": team.description,
                "invite_code": team.invite_code,
                "created_at": team.created_at
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create team: {str(e)}"
        )

@router.get("/teams", response_model=List[dict])
async def get_user_teams(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all teams the current user is a member of"""
    teams = collaboration_crud.get_user_teams(db=db, user_id=current_user.id)
    
    return [
        {
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "is_public": team.is_public,
            "created_at": team.created_at
        }
        for team in teams
    ]

@router.get("/teams/{team_id}/members", response_model=List[dict])
async def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all members of a team"""
    # TODO: Add permission check - user must be team member
    
    members = collaboration_crud.get_team_members(db=db, team_id=team_id)
    
    return [
        {
            "user_id": member["user"].id,
            "username": member["user"].username,
            "email": member["user"].email,
            "role": member["role"].value,
            "joined_at": member["joined_at"]
        }
        for member in members
    ]

@router.post("/teams/{team_id}/invite", response_model=dict)
async def invite_team_member(
    team_id: int,
    invite_data: TeamMemberInvite,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Invite a user to join a team"""
    try:
        if invite_data.user_id:
            membership = collaboration_crud.add_team_member(
                db=db,
                team_id=team_id,
                user_id=invite_data.user_id,
                role=invite_data.role,
                invited_by=current_user.id
            )
            
            return {
                "success": True,
                "message": "User added to team successfully",
                "membership_id": membership.id
            }
        else:
            # TODO: Implement email invitation system
            return {
                "success": False,
                "message": "Email invitations not yet implemented"
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to invite team member: {str(e)}"
        )

# Workspace Sharing Endpoints
@router.get("/workspaces", response_model=List[dict])
async def get_accessible_workspaces(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all workspaces the user has access to"""
    workspaces = collaboration_crud.get_user_accessible_workspaces(
        db=db, user_id=current_user.id
    )
    
    return [
        {
            "workspace": {
                "id": item["workspace"].id,
                "name": item["workspace"].name,
                "description": item["workspace"].description,
                "created_at": item["workspace"].created_at
            },
            "access_type": item["access_type"],
            "permissions": item["permissions"],
            "shared_at": item.get("shared_at")
        }
        for item in workspaces
    ]

@router.post("/workspaces/{workspace_id}/share", response_model=dict)
async def share_workspace(
    workspace_id: int,
    share_data: WorkspaceShareRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Share a workspace with a user or team"""
    try:
        share = collaboration_crud.share_workspace(
            db=db,
            workspace_id=workspace_id,
            shared_by=current_user.id,
            user_id=share_data.user_id,
            team_id=share_data.team_id,
            permissions=share_data.permissions,
            expires_in_days=share_data.expires_in_days
        )
        
        return {
            "success": True,
            "share_id": share.id,
            "message": "Workspace shared successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to share workspace: {str(e)}"
        )

@router.post("/workspaces/{workspace_id}/invite", response_model=dict)
async def create_workspace_invite(
    workspace_id: int,
    invite_data: WorkspaceInviteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a workspace invitation"""
    try:
        invite = collaboration_crud.create_workspace_invite(
            db=db,
            workspace_id=workspace_id,
            invited_by=current_user.id,
            invited_email=invite_data.invited_email,
            invited_user_id=invite_data.invited_user_id,
            permissions=invite_data.permissions,
            expires_in_days=invite_data.expires_in_days,
            message=invite_data.message
        )
        
        # TODO: Add background task to send email invitation
        # background_tasks.add_task(send_workspace_invite_email, invite)
        
        return {
            "success": True,
            "invite_code": invite.invite_code,
            "expires_at": invite.expires_at,
            "message": "Invitation created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create invitation: {str(e)}"
        )

@router.post("/invites/{invite_code}/accept", response_model=dict)
async def accept_workspace_invite(
    invite_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Accept a workspace invitation"""
    try:
        share = collaboration_crud.accept_workspace_invite(
            db=db,
            invite_code=invite_code,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "workspace_id": share.workspace_id,
            "message": "Invitation accepted successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept invitation: {str(e)}"
        )

# Task Assignment Endpoints
@router.post("/tasks/{task_id}/assign", response_model=dict)
async def assign_task(
    task_id: int,
    assignment_data: TaskAssignmentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign a task to a user"""
    try:
        assignment = collaboration_crud.assign_task(
            db=db,
            task_id=task_id,
            assigned_to=assignment_data.assigned_to,
            assigned_by=current_user.id,
            role=assignment_data.role,
            estimated_hours=assignment_data.estimated_hours
        )
        
        return {
            "success": True,
            "assignment_id": assignment.id,
            "message": "Task assigned successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign task: {str(e)}"
        )

@router.get("/tasks/assigned", response_model=List[dict])
async def get_assigned_tasks(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all tasks assigned to the current user"""
    assignments = collaboration_crud.get_user_assigned_tasks(
        db=db, user_id=current_user.id, status=status
    )
    
    return [
        {
            "task": {
                "id": item["task"].id,
                "title": item["task"].title,
                "description": item["task"].description,
                "status": item["task"].status,
                "priority": item["task"].priority,
                "workspace_id": item["task"].workspace_id
            },
            "assignment": {
                "role": item["role"],
                "assigned_at": item["assigned_at"],
                "completion_percentage": item["completion_percentage"]
            }
        }
        for item in assignments
    ]

@router.put("/tasks/{task_id}/progress", response_model=dict)
async def update_task_progress(
    task_id: int,
    progress_data: TaskProgressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update task completion progress"""
    try:
        assignment = collaboration_crud.update_task_progress(
            db=db,
            task_id=task_id,
            user_id=current_user.id,
            completion_percentage=progress_data.completion_percentage,
            actual_hours=progress_data.actual_hours
        )
        
        if assignment:
            return {
                "success": True,
                "completion_percentage": assignment.completion_percentage,
                "message": "Progress updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task assignment not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update progress: {str(e)}"
        )

# Task Comments Endpoints
@router.post("/tasks/{task_id}/comments", response_model=dict)
async def add_task_comment(
    task_id: int,
    comment_data: TaskCommentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a task"""
    try:
        comment = collaboration_crud.add_task_comment(
            db=db,
            task_id=task_id,
            user_id=current_user.id,
            content=comment_data.content,
            comment_type=comment_data.comment_type,
            parent_comment_id=comment_data.parent_comment_id,
            mentions=comment_data.mentions
        )
        
        return {
            "success": True,
            "comment_id": comment.id,
            "created_at": comment.created_at,
            "message": "Comment added successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add comment: {str(e)}"
        )

@router.get("/tasks/{task_id}/comments", response_model=List[dict])
async def get_task_comments(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all comments for a task"""
    comments = collaboration_crud.get_task_comments(db=db, task_id=task_id)
    
    return [
        {
            "id": item["comment"].id,
            "content": item["comment"].content,
            "comment_type": item["comment"].comment_type,
            "created_at": item["comment"].created_at,
            "user": {
                "id": item["user"].id,
                "username": item["user"].username
            },
            "parent_comment_id": item["comment"].parent_comment_id,
            "mentions": item["mentions"]
        }
        for item in comments
    ]

# Analytics Endpoints
@router.get("/workspaces/{workspace_id}/analytics", response_model=dict)
async def get_workspace_analytics(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive workspace analytics"""
    try:
        analytics = collaboration_crud.get_workspace_analytics(
            db=db, workspace_id=workspace_id
        )
        
        return {
            "success": True,
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get analytics: {str(e)}"
        )

@router.get("/workspaces/{workspace_id}/activity", response_model=List[dict])
async def get_workspace_activity(
    workspace_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent workspace activity"""
    activities = collaboration_crud.get_workspace_activity(
        db=db, workspace_id=workspace_id, limit=limit
    )
    
    return [
        {
            "id": item["activity"].id,
            "action_type": item["activity"].action_type,
            "description": item["activity"].action_description,
            "created_at": item["activity"].created_at,
            "user": {
                "id": item["user"].id,
                "username": item["user"].username
            },
            "entity_type": item["activity"].entity_type,
            "entity_id": item["activity"].entity_id,
            "metadata": item["metadata"]
        }
        for item in activities
    ]