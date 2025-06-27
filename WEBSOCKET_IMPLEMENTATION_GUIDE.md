# WebSocket Real-time Collaboration Implementation Guide

## Overview

This implementation adds comprehensive WebSocket support for real-time collaboration features to the BlueBirdHub project. The system enables multiple users to collaborate simultaneously with live updates, cursor tracking, user presence indicators, and collaborative editing capabilities.

## Features Implemented

### 🔗 WebSocket Connection Management
- **Connection Manager**: Centralized WebSocket connection handling
- **Auto-reconnection**: Automatic reconnection with exponential backoff
- **Heartbeat System**: Keep-alive mechanism to detect and handle disconnections
- **Authentication**: JWT-based WebSocket authentication
- **Connection Pooling**: Efficient management of multiple user connections per workspace

### 👥 User Presence & Activity Tracking
- **Real-time User List**: See who's currently active in each workspace
- **Status Indicators**: Active, idle, and offline states
- **Activity Broadcasting**: Live updates of user actions and current activities
- **Join/Leave Notifications**: Real-time notifications when users enter or leave

### ✏️ Collaborative Cursor Tracking
- **Live Cursor Positions**: See other users' cursors in real-time
- **User Identification**: Color-coded cursors with user names
- **File Context**: Cursors tracked per file/document
- **Selection Ranges**: Support for text selection visualization

### 📝 Real-time Document Updates
- **Operational Transformation**: Conflict-free collaborative editing
- **Version Control**: Document versioning for update synchronization
- **Change Broadcasting**: Live propagation of document changes
- **Typing Indicators**: Show when users are actively typing

### 🔔 Live Notifications & Activity Feed
- **System Notifications**: Important alerts and updates
- **Activity Stream**: Real-time feed of workspace activities
- **Document Changes**: Live updates of file modifications
- **Auto-dismiss**: Configurable auto-hide for notifications

## Architecture

### Backend Components

#### 1. WebSocket Manager (`websocket_manager.py`)
```python
# Core connection management
class ConnectionManager:
    - active_connections: Dict[workspace_id, Dict[user_id, WebSocket]]
    - user_presence: Dict[workspace_id, Dict[user_id, UserInfo]]
    - cursor_positions: Dict[workspace_id, Dict[user_id, CursorData]]
    - document_versions: Dict[document_id, version]
    - message_queue: Dict[user_id, List[Message]]
```

**Key Methods:**
- `connect()`: Establish new WebSocket connection
- `disconnect()`: Clean up user connection
- `broadcast_to_workspace()`: Send message to all workspace users
- `handle_cursor_update()`: Process cursor position changes
- `handle_document_update()`: Process document modifications
- `cleanup_inactive_users()`: Remove idle/disconnected users

#### 2. WebSocket API Endpoints (`api/websocket.py`)
```
/ws/workspace/{workspace_id}    - Main collaboration endpoint
/ws/notifications               - User-specific notifications
/ws/workspace/{workspace_id}/presence - Get active users (HTTP)
/broadcast/{workspace_id}       - Admin broadcast (HTTP)
```

#### 3. Authentication Integration
- JWT token validation for WebSocket connections
- User permission checking for workspace access
- Secure token-based authentication flow

### Frontend Components

#### 1. WebSocket Hooks

**`useWebSocket.ts`**
- Low-level WebSocket connection management
- Auto-reconnection with configurable retry logic
- Heartbeat system for connection health
- Message queuing for offline scenarios

**`useCollaboration.ts`**
- High-level collaboration features
- User presence management
- Cursor and document update handling
- Activity tracking and broadcasting

#### 2. UI Components

**`UserPresence.tsx`**
- Display active users with avatars
- Status indicators (active/idle/offline)
- Typing indicators
- User activity display

**`CollaborativeCursor.tsx`**
- Render other users' cursors
- Position tracking and animation
- User identification labels
- Selection range visualization

**`RealtimeNotifications.tsx`**
- System notification display
- Activity feed with filtering
- Document update notifications
- Auto-dismiss functionality

**`EnhancedCollaborativeWorkspace.tsx`**
- Main workspace component
- Integration of all collaboration features
- Real-time workspace management
- Sidebar with presence and notifications

## Setup Instructions

### 1. Backend Setup

The WebSocket dependencies are already included in `requirements.txt`:
```
websockets>=12.0
fastapi>=0.115.0
```

The WebSocket routes are automatically included in the FastAPI application via the main router.

### 2. Frontend Setup

Install the additional WebSocket dependencies:
```bash
npm install ws@^8.15.0
npm install --save-dev @types/ws@^8.5.10
```

### 3. Environment Configuration

Ensure your development environment allows WebSocket connections:
- CORS policy includes WebSocket origins
- Firewall allows WebSocket traffic on port 8000
- JWT tokens are properly configured

### 4. Database Requirements

No additional database tables are required - the implementation uses in-memory storage for real-time data with optional database integration for persistence.

## Usage Examples

### 1. Basic WebSocket Connection
```javascript
import { useCollaboration } from './hooks/useCollaboration';

const MyComponent = () => {
  const collaboration = useCollaboration({
    workspaceId: 123,
    onUserJoined: (user) => console.log('User joined:', user),
    onCursorUpdate: (cursor) => console.log('Cursor moved:', cursor),
    onDocumentUpdate: (update) => console.log('Document changed:', update)
  });

  return (
    <div>
      <div>Connected: {collaboration.isConnected}</div>
      <div>Users: {collaboration.activeUsers.length}</div>
    </div>
  );
};
```

### 2. Sending Updates
```javascript
// Update cursor position
collaboration.updateCursor({
  line: 10,
  column: 5
}, null, 'myfile.js');

// Send document update
collaboration.updateDocument('file123', {
  type: 'insert',
  position: { line: 10, column: 5 },
  content: 'Hello World!'
});

// Update activity status
collaboration.updateActivity('editing_file', {
  filename: 'myfile.js'
});
```

### 3. Message Types

**Client → Server:**
```json
{
  "type": "cursor_update",
  "data": {
    "position": { "line": 10, "column": 5 },
    "selection": { "start": {...}, "end": {...} },
    "file_path": "example.js"
  }
}
```

**Server → Client:**
```json
{
  "type": "user_joined",
  "data": {
    "id": "user123",
    "username": "john_doe",
    "cursor_color": "#FF6B6B",
    "status": "active"
  }
}
```

## Testing

### 1. Demo Page
Open `websocket-demo.html` in your browser to test WebSocket functionality:
1. Enter a valid JWT token
2. Enter a workspace ID
3. Click "Connect"
4. Test various message types using the provided buttons

### 2. Multi-User Testing
1. Open multiple browser tabs/windows
2. Connect with different user tokens
3. Observe real-time updates across all connections
4. Test cursor movements, document changes, and presence updates

### 3. Connection Reliability
- Test auto-reconnection by temporarily stopping the server
- Verify message queuing for offline users
- Test heartbeat system by monitoring connection health

## Configuration Options

### WebSocket Settings
```javascript
const collaboration = useCollaboration({
  workspaceId: 123,
  reconnectInterval: 3000,        // Reconnection delay
  maxReconnectAttempts: 5,        // Max retry attempts
  heartbeatInterval: 30000,       // Heartbeat frequency
  onUserJoined: handleUserJoined,
  onUserLeft: handleUserLeft,
  onCursorUpdate: handleCursor,
  onDocumentUpdate: handleDocument,
  onActivityUpdate: handleActivity
});
```

### Connection Manager Settings
```python
# In websocket_manager.py
INACTIVE_THRESHOLD = 300    # 5 minutes
CLEANUP_INTERVAL = 60       # 1 minute
MAX_MESSAGE_QUEUE = 100     # Per user
HEARTBEAT_TIMEOUT = 45      # Seconds
```

## Security Considerations

### 1. Authentication
- All WebSocket connections require valid JWT tokens
- Tokens are validated on connection and periodically refreshed
- Users can only access workspaces they have permissions for

### 2. Rate Limiting
- Message frequency limits prevent spam
- Connection limits per user/IP
- Automatic disconnection for suspicious activity

### 3. Data Validation
- All incoming messages are validated against schemas
- Sanitization of user-generated content
- Protection against injection attacks

### 4. Privacy
- Users only see data from workspaces they have access to
- Sensitive information is not broadcasted
- Audit logging for compliance

## Performance Optimization

### 1. Connection Management
- Connection pooling reduces resource usage
- Automatic cleanup of inactive connections
- Efficient message routing and broadcasting

### 2. Message Optimization
- Message batching for high-frequency updates
- Compression for large messages
- Selective broadcasting based on user permissions

### 3. Memory Management
- Automatic cleanup of old cursor positions
- Limited message history retention
- Garbage collection of disconnected user data

## Troubleshooting

### Common Issues

#### 1. Connection Failures
```
Error: WebSocket connection failed
```
**Solutions:**
- Verify JWT token is valid and not expired
- Check workspace ID exists and user has access
- Ensure WebSocket URL is correct (ws:// not http://)
- Check firewall/proxy settings

#### 2. Auto-reconnection Problems
```
Error: Maximum reconnection attempts reached
```
**Solutions:**
- Check network connectivity
- Verify server is running and accessible
- Review authentication token validity
- Check browser WebSocket support

#### 3. Message Delivery Issues
```
Warning: Message not sent - WebSocket not connected
```
**Solutions:**
- Check connection status before sending messages
- Implement message queuing for offline scenarios
- Verify message format matches expected schema

### Debug Mode
Enable debug logging:
```javascript
// Frontend
localStorage.setItem('websocket_debug', 'true');

// Backend
import logging
logging.getLogger('websockets').setLevel(logging.DEBUG)
```

## API Reference

### WebSocket Message Types

#### Client → Server
| Type | Description | Data Schema |
|------|-------------|-------------|
| `cursor_update` | Update cursor position | `{position, selection?, file_path?}` |
| `document_update` | Document modification | `{document_id, operation}` |
| `activity_update` | User activity change | `{activity, details?}` |
| `typing_indicator` | Typing status | `{is_typing, location?}` |
| `ping` | Heartbeat | `{timestamp}` |
| `request_sync` | Request state sync | `{}` |

#### Server → Client
| Type | Description | Data Schema |
|------|-------------|-------------|
| `connection_established` | Confirm connection | `{user_id, workspace_id, cursor_color}` |
| `workspace_users` | Active users list | `[{id, username, status, ...}]` |
| `user_joined` | User joined workspace | `{id, username, cursor_color, ...}` |
| `user_left` | User left workspace | `{user_id, username}` |
| `cursor_update` | Cursor position change | `{user_id, username, cursor_color, position, ...}` |
| `document_update` | Document was modified | `{document_id, user_id, username, version, operation}` |
| `activity_update` | User activity change | `{user_id, username, activity, details}` |
| `user_typing` | Typing indicator | `{user_id, username, is_typing, location?}` |
| `pong` | Heartbeat response | `{timestamp}` |

## Future Enhancements

### Planned Features
1. **Operational Transformation**: Advanced conflict resolution for simultaneous edits
2. **Voice/Video Chat**: Integrated communication features
3. **Screen Sharing**: Share screens within workspaces
4. **File Locking**: Prevent conflicting edits on critical files
5. **Collaborative Whiteboards**: Real-time drawing and diagramming
6. **Advanced Permissions**: Fine-grained access control for collaboration features
7. **Mobile Support**: Optimized mobile collaboration experience
8. **Offline Sync**: Synchronization of changes when reconnecting

### Performance Improvements
1. **Redis Integration**: Scalable multi-server support
2. **Message Compression**: Reduce bandwidth usage
3. **Delta Sync**: Only send changes, not full documents
4. **Connection Clustering**: Load balancing for high-traffic scenarios

## Contributing

When contributing to the WebSocket implementation:

1. **Follow the established patterns** for message types and data structures
2. **Add proper error handling** for all WebSocket operations
3. **Include tests** for new functionality
4. **Update documentation** for any API changes
5. **Consider security implications** of new features
6. **Test with multiple concurrent users** to verify real-time behavior

## Support

For issues related to WebSocket implementation:
1. Check the browser console for WebSocket connection errors
2. Verify server logs for authentication and connection issues
3. Use the demo page to isolate problems
4. Review network traffic in browser developer tools
5. Test with different browsers and network conditions

## Conclusion

This WebSocket implementation provides a solid foundation for real-time collaboration in BlueBirdHub. The modular architecture allows for easy extension and customization, while the comprehensive feature set supports various collaboration scenarios. The system is designed to be scalable, secure, and performant, making it suitable for both small teams and large organizations.