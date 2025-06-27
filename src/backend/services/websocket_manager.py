"""
WebSocket Manager for real-time collaboration features
Handles user presence, cursor tracking, live updates, and collaborative editing
"""

import asyncio
import json
from typing import Dict, Set, List, Optional, Any
from datetime import datetime
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from loguru import logger

from ..database import get_db
from ..models.user import User
from ..models.workspace import Workspace
from ..dependencies.auth import get_current_user_from_token


class ConnectionManager:
    """Manages WebSocket connections and real-time collaboration features"""
    
    def __init__(self):
        # Active connections mapped by workspace_id
        self.active_connections: Dict[int, Dict[str, WebSocket]] = defaultdict(dict)
        
        # User presence tracking
        self.user_presence: Dict[int, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        
        # Cursor positions for collaborative editing
        self.cursor_positions: Dict[int, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        
        # Document versions for conflict resolution
        self.document_versions: Dict[str, int] = defaultdict(int)
        
        # Message queue for offline users
        self.message_queue: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()

    async def connect(
        self, 
        websocket: WebSocket, 
        workspace_id: int, 
        user_id: str,
        user_info: Dict[str, Any]
    ):
        """Connect a user to a workspace"""
        await websocket.accept()
        
        async with self.lock:
            # Store connection
            self.active_connections[workspace_id][user_id] = websocket
            
            # Update user presence
            self.user_presence[workspace_id][user_id] = {
                "id": user_id,
                "username": user_info.get("username", "Unknown"),
                "email": user_info.get("email", ""),
                "status": "active",
                "connected_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "cursor_color": self._get_user_color(user_id)
            }
            
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection_established",
                "data": {
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                    "cursor_color": self.user_presence[workspace_id][user_id]["cursor_color"]
                }
            })
            
            # Notify other users in workspace
            await self.broadcast_to_workspace(
                workspace_id,
                {
                    "type": "user_joined",
                    "data": self.user_presence[workspace_id][user_id]
                },
                exclude_user=user_id
            )
            
            # Send current workspace state
            await self._send_workspace_state(websocket, workspace_id, user_id)
            
            # Send any queued messages
            await self._send_queued_messages(websocket, user_id)
            
        logger.info(f"User {user_id} connected to workspace {workspace_id}")

    async def disconnect(self, workspace_id: int, user_id: str):
        """Disconnect a user from a workspace"""
        async with self.lock:
            # Remove connection
            if workspace_id in self.active_connections:
                self.active_connections[workspace_id].pop(user_id, None)
                
                # Clean up empty workspaces
                if not self.active_connections[workspace_id]:
                    del self.active_connections[workspace_id]
            
            # Update user presence
            if workspace_id in self.user_presence and user_id in self.user_presence[workspace_id]:
                self.user_presence[workspace_id][user_id]["status"] = "offline"
                self.user_presence[workspace_id][user_id]["disconnected_at"] = datetime.utcnow().isoformat()
            
            # Remove cursor position
            if workspace_id in self.cursor_positions:
                self.cursor_positions[workspace_id].pop(user_id, None)
            
            # Notify other users
            await self.broadcast_to_workspace(
                workspace_id,
                {
                    "type": "user_left",
                    "data": {
                        "user_id": user_id,
                        "username": self.user_presence[workspace_id].get(user_id, {}).get("username", "Unknown")
                    }
                },
                exclude_user=user_id
            )
            
        logger.info(f"User {user_id} disconnected from workspace {workspace_id}")

    async def broadcast_to_workspace(
        self, 
        workspace_id: int, 
        message: Dict[str, Any], 
        exclude_user: Optional[str] = None
    ):
        """Broadcast a message to all users in a workspace"""
        if workspace_id not in self.active_connections:
            return
            
        disconnected_users = []
        
        for user_id, connection in self.active_connections[workspace_id].items():
            if user_id == exclude_user:
                continue
                
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                disconnected_users.append(user_id)
                # Queue message for offline user
                self.message_queue[user_id].append({
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(workspace_id, user_id)

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to a specific user across all their workspaces"""
        sent = False
        
        for workspace_id, connections in self.active_connections.items():
            if user_id in connections:
                try:
                    await connections[user_id].send_json(message)
                    sent = True
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
        
        if not sent:
            # Queue message for offline user
            self.message_queue[user_id].append({
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })

    async def handle_cursor_update(
        self, 
        workspace_id: int, 
        user_id: str, 
        cursor_data: Dict[str, Any]
    ):
        """Handle cursor position updates for collaborative editing"""
        async with self.lock:
            # Update cursor position
            self.cursor_positions[workspace_id][user_id] = {
                "user_id": user_id,
                "username": self.user_presence[workspace_id][user_id]["username"],
                "cursor_color": self.user_presence[workspace_id][user_id]["cursor_color"],
                "position": cursor_data.get("position"),
                "selection": cursor_data.get("selection"),
                "file_path": cursor_data.get("file_path"),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Broadcast cursor update
        await self.broadcast_to_workspace(
            workspace_id,
            {
                "type": "cursor_update",
                "data": self.cursor_positions[workspace_id][user_id]
            },
            exclude_user=user_id
        )

    async def handle_document_update(
        self, 
        workspace_id: int, 
        user_id: str, 
        update_data: Dict[str, Any]
    ):
        """Handle document updates with operational transformation"""
        document_id = update_data.get("document_id")
        
        async with self.lock:
            # Increment document version
            self.document_versions[document_id] += 1
            current_version = self.document_versions[document_id]
        
        # Create update message
        update_message = {
            "type": "document_update",
            "data": {
                "document_id": document_id,
                "user_id": user_id,
                "username": self.user_presence[workspace_id][user_id]["username"],
                "version": current_version,
                "operation": update_data.get("operation"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Broadcast to all users in workspace
        await self.broadcast_to_workspace(workspace_id, update_message, exclude_user=user_id)
        
        # Send acknowledgment to sender
        await self.send_to_user(
            user_id,
            {
                "type": "update_acknowledged",
                "data": {
                    "document_id": document_id,
                    "version": current_version
                }
            }
        )

    async def handle_activity_update(
        self, 
        workspace_id: int, 
        user_id: str, 
        activity_data: Dict[str, Any]
    ):
        """Handle user activity updates"""
        async with self.lock:
            if workspace_id in self.user_presence and user_id in self.user_presence[workspace_id]:
                self.user_presence[workspace_id][user_id]["last_activity"] = datetime.utcnow().isoformat()
                self.user_presence[workspace_id][user_id]["current_activity"] = activity_data.get("activity")
        
        # Broadcast activity update
        await self.broadcast_to_workspace(
            workspace_id,
            {
                "type": "activity_update",
                "data": {
                    "user_id": user_id,
                    "username": self.user_presence[workspace_id][user_id]["username"],
                    "activity": activity_data.get("activity"),
                    "details": activity_data.get("details"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            exclude_user=user_id
        )

    async def get_workspace_presence(self, workspace_id: int) -> List[Dict[str, Any]]:
        """Get all active users in a workspace"""
        if workspace_id not in self.user_presence:
            return []
        
        return [
            user_info 
            for user_info in self.user_presence[workspace_id].values()
            if user_info.get("status") == "active"
        ]

    async def _send_workspace_state(self, websocket: WebSocket, workspace_id: int, user_id: str):
        """Send current workspace state to newly connected user"""
        # Send active users
        active_users = await self.get_workspace_presence(workspace_id)
        await websocket.send_json({
            "type": "workspace_users",
            "data": active_users
        })
        
        # Send cursor positions
        if workspace_id in self.cursor_positions:
            await websocket.send_json({
                "type": "cursor_positions",
                "data": list(self.cursor_positions[workspace_id].values())
            })

    async def _send_queued_messages(self, websocket: WebSocket, user_id: str):
        """Send queued messages to reconnecting user"""
        if user_id in self.message_queue:
            messages = self.message_queue[user_id]
            self.message_queue[user_id] = []
            
            for queued in messages:
                try:
                    await websocket.send_json({
                        "type": "queued_message",
                        "data": queued
                    })
                except Exception as e:
                    logger.error(f"Error sending queued message: {e}")

    def _get_user_color(self, user_id: str) -> str:
        """Generate a consistent color for a user"""
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57",
            "#FF9FF3", "#54A0FF", "#48DBFB", "#0ABDE3", "#00D2D3",
            "#1DD1A1", "#10AC84", "#EE5A6F", "#F368E0", "#FF6348"
        ]
        
        # Use hash of user_id to consistently assign same color
        color_index = hash(user_id) % len(colors)
        return colors[color_index]

    async def cleanup_inactive_users(self):
        """Periodic cleanup of inactive users"""
        current_time = datetime.utcnow()
        inactive_threshold = 300  # 5 minutes
        
        async with self.lock:
            for workspace_id in list(self.user_presence.keys()):
                for user_id in list(self.user_presence[workspace_id].keys()):
                    user_info = self.user_presence[workspace_id][user_id]
                    
                    if user_info.get("status") == "active":
                        last_activity = datetime.fromisoformat(user_info.get("last_activity"))
                        if (current_time - last_activity).total_seconds() > inactive_threshold:
                            # Mark user as idle
                            user_info["status"] = "idle"
                            
                            await self.broadcast_to_workspace(
                                workspace_id,
                                {
                                    "type": "user_idle",
                                    "data": {
                                        "user_id": user_id,
                                        "username": user_info["username"]
                                    }
                                },
                                exclude_user=user_id
                            )


# Global connection manager instance
manager = ConnectionManager()


# Background task for cleanup
async def periodic_cleanup():
    """Run periodic cleanup tasks"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            await manager.cleanup_inactive_users()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")