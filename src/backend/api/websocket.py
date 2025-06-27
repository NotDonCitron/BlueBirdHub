"""
WebSocket API endpoints for real-time collaboration
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json
from loguru import logger

from ..database import get_db
from ..services.websocket_manager import manager
from ..models.user import User
from ..models.workspace import Workspace
from ..dependencies.auth import get_current_user_from_token, verify_token

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/workspace/{workspace_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    workspace_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time collaboration in a workspace
    
    Connect with: ws://localhost:8000/ws/workspace/{workspace_id}?token={jwt_token}
    """
    
    # Authenticate user from token
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    try:
        # Verify token and get user
        payload = verify_token(token)
        username = payload.get("sub")
        if not username:
            await websocket.close(code=4001, reason="Invalid token")
            return
            
        # Get user from database
        user = db.query(User).filter(User.username == username).first()
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return
            
        # Check workspace access
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            await websocket.close(code=4004, reason="Workspace not found")
            return
            
        # TODO: Add proper workspace permission check here
        # For now, we'll allow access if user exists
        
        user_info = {
            "username": user.username,
            "email": user.email,
            "id": str(user.id)
        }
        
        # Connect to manager
        await manager.connect(websocket, workspace_id, str(user.id), user_info)
        
        logger.info(f"WebSocket connected: User {user.username} to workspace {workspace_id}")
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                message_data = message.get("data", {})
                
                # Handle different message types
                if message_type == "cursor_update":
                    await manager.handle_cursor_update(
                        workspace_id, 
                        str(user.id), 
                        message_data
                    )
                    
                elif message_type == "document_update":
                    await manager.handle_document_update(
                        workspace_id,
                        str(user.id),
                        message_data
                    )
                    
                elif message_type == "activity_update":
                    await manager.handle_activity_update(
                        workspace_id,
                        str(user.id),
                        message_data
                    )
                    
                elif message_type == "typing_indicator":
                    # Broadcast typing indicator
                    await manager.broadcast_to_workspace(
                        workspace_id,
                        {
                            "type": "user_typing",
                            "data": {
                                "user_id": str(user.id),
                                "username": user.username,
                                "is_typing": message_data.get("is_typing", False),
                                "location": message_data.get("location")
                            }
                        },
                        exclude_user=str(user.id)
                    )
                    
                elif message_type == "ping":
                    # Respond to ping
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": message_data.get("timestamp")}
                    })
                    
                elif message_type == "request_sync":
                    # Send current workspace state
                    active_users = await manager.get_workspace_presence(workspace_id)
                    await websocket.send_json({
                        "type": "sync_response",
                        "data": {
                            "active_users": active_users,
                            "workspace_id": workspace_id
                        }
                    })
                    
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: User {user.username} from workspace {workspace_id}")
            await manager.disconnect(workspace_id, str(user.id))
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            await websocket.close(code=4002, reason="Invalid message format")
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.close(code=4000, reason="Internal error")
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Connection error")
    finally:
        # Ensure cleanup
        if 'user' in locals():
            await manager.disconnect(workspace_id, str(user.id))


@router.websocket("/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for user notifications across all workspaces
    
    Connect with: ws://localhost:8000/ws/notifications?token={jwt_token}
    """
    
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    try:
        # Verify token and get user
        payload = verify_token(token)
        username = payload.get("sub")
        if not username:
            await websocket.close(code=4001, reason="Invalid token")
            return
            
        # Get user from database
        user = db.query(User).filter(User.username == username).first()
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return
        
        await websocket.accept()
        
        # Register this connection for notifications
        # This is a simplified implementation - in production, you'd want a separate
        # notification manager
        
        logger.info(f"Notification WebSocket connected: User {user.username}")
        
        try:
            while True:
                # Keep connection alive
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": message.get("data", {}).get("timestamp")}
                    })
                    
        except WebSocketDisconnect:
            logger.info(f"Notification WebSocket disconnected: User {user.username}")
            
    except Exception as e:
        logger.error(f"Notification WebSocket error: {e}")
        await websocket.close(code=4000, reason="Connection error")


# HTTP endpoints for WebSocket management

@router.get("/workspace/{workspace_id}/presence")
async def get_workspace_presence(
    workspace_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get list of active users in a workspace"""
    
    # Check workspace access
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # TODO: Add proper permission check
    
    active_users = await manager.get_workspace_presence(workspace_id)
    
    return {
        "workspace_id": workspace_id,
        "active_users": active_users,
        "total_count": len(active_users)
    }


@router.post("/broadcast/{workspace_id}")
async def broadcast_to_workspace(
    workspace_id: int,
    message: dict,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Broadcast a message to all users in a workspace (admin only)"""
    
    # Check if user is admin or workspace owner
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # TODO: Add proper admin/owner check
    
    await manager.broadcast_to_workspace(
        workspace_id,
        {
            "type": "system_broadcast",
            "data": {
                "message": message.get("message"),
                "sender": current_user.username,
                "priority": message.get("priority", "normal")
            }
        }
    )
    
    return {"success": True, "message": "Broadcast sent"}