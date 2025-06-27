/**
 * Collaboration hook for real-time workspace features
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';

interface User {
  id: string;
  username: string;
  email: string;
  status: 'active' | 'idle' | 'offline';
  connected_at: string;
  last_activity: string;
  cursor_color: string;
}

interface CursorPosition {
  user_id: string;
  username: string;
  cursor_color: string;
  position: {
    line: number;
    column: number;
  };
  selection?: {
    start: { line: number; column: number };
    end: { line: number; column: number };
  };
  file_path?: string;
  timestamp: string;
}

interface DocumentUpdate {
  document_id: string;
  user_id: string;
  username: string;
  version: number;
  operation: {
    type: 'insert' | 'delete' | 'replace';
    position: { line: number; column: number };
    content?: string;
    length?: number;
  };
  timestamp: string;
}

interface ActivityUpdate {
  user_id: string;
  username: string;
  activity: string;
  details?: any;
  timestamp: string;
}

interface CollaborationState {
  activeUsers: User[];
  cursorPositions: CursorPosition[];
  isConnected: boolean;
  connectionState: string;
  currentUserColor: string;
}

interface UseCollaborationOptions {
  workspaceId: number;
  onUserJoined?: (user: User) => void;
  onUserLeft?: (userId: string) => void;
  onCursorUpdate?: (cursor: CursorPosition) => void;
  onDocumentUpdate?: (update: DocumentUpdate) => void;
  onActivityUpdate?: (activity: ActivityUpdate) => void;
  onUserTyping?: (userId: string, isTyping: boolean, location?: string) => void;
}

export const useCollaboration = (options: UseCollaborationOptions) => {
  const { workspaceId, onUserJoined, onUserLeft, onCursorUpdate, onDocumentUpdate, onActivityUpdate, onUserTyping } = options;
  
  const [activeUsers, setActiveUsers] = useState<User[]>([]);
  const [cursorPositions, setCursorPositions] = useState<CursorPosition[]>([]);
  const [currentUserColor, setCurrentUserColor] = useState<string>('#4ECDC4');
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  
  const typingTimeouts = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // WebSocket connection
  const wsUrl = workspaceId ? `ws://localhost:8000/ws/workspace/${workspaceId}` : null;
  
  const handleMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'connection_established':
        setCurrentUserColor(message.data.cursor_color);
        break;

      case 'workspace_users':
        setActiveUsers(message.data);
        break;

      case 'cursor_positions':
        setCursorPositions(message.data);
        break;

      case 'user_joined':
        setActiveUsers(prev => {
          const exists = prev.find(u => u.id === message.data.id);
          if (exists) return prev;
          const newUser = message.data;
          onUserJoined?.(newUser);
          return [...prev, newUser];
        });
        break;

      case 'user_left':
        setActiveUsers(prev => {
          const filtered = prev.filter(u => u.id !== message.data.user_id);
          onUserLeft?.(message.data.user_id);
          return filtered;
        });
        setCursorPositions(prev => prev.filter(c => c.user_id !== message.data.user_id));
        break;

      case 'cursor_update':
        setCursorPositions(prev => {
          const filtered = prev.filter(c => c.user_id !== message.data.user_id);
          const newCursor = message.data;
          onCursorUpdate?.(newCursor);
          return [...filtered, newCursor];
        });
        break;

      case 'document_update':
        onDocumentUpdate?.(message.data);
        break;

      case 'activity_update':
        onActivityUpdate?.(message.data);
        break;

      case 'user_typing':
        const { user_id, is_typing, location } = message.data;
        
        setTypingUsers(prev => {
          const newSet = new Set(prev);
          if (is_typing) {
            newSet.add(user_id);
            
            // Clear existing timeout
            const existingTimeout = typingTimeouts.current.get(user_id);
            if (existingTimeout) {
              clearTimeout(existingTimeout);
            }
            
            // Set new timeout to remove typing indicator
            const timeout = setTimeout(() => {
              setTypingUsers(currentSet => {
                const updatedSet = new Set(currentSet);
                updatedSet.delete(user_id);
                return updatedSet;
              });
              typingTimeouts.current.delete(user_id);
            }, 3000); // 3 seconds timeout
            
            typingTimeouts.current.set(user_id, timeout);
          } else {
            newSet.delete(user_id);
            
            // Clear timeout
            const existingTimeout = typingTimeouts.current.get(user_id);
            if (existingTimeout) {
              clearTimeout(existingTimeout);
              typingTimeouts.current.delete(user_id);
            }
          }
          return newSet;
        });
        
        onUserTyping?.(user_id, is_typing, location);
        break;

      case 'user_idle':
        setActiveUsers(prev => prev.map(user => 
          user.id === message.data.user_id 
            ? { ...user, status: 'idle' } 
            : user
        ));
        break;

      case 'pong':
        // Handle heartbeat response
        break;

      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }, [onUserJoined, onUserLeft, onCursorUpdate, onDocumentUpdate, onActivityUpdate, onUserTyping]);

  const { socket, connectionState, sendMessage, reconnect, disconnect } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    onOpen: () => {
      console.log('Connected to collaboration workspace');
    },
    onClose: () => {
      console.log('Disconnected from collaboration workspace');
      setActiveUsers([]);
      setCursorPositions([]);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    }
  });

  // Collaboration methods
  const updateCursor = useCallback((position: any, selection?: any, filePath?: string) => {
    sendMessage({
      type: 'cursor_update',
      data: {
        position,
        selection,
        file_path: filePath
      }
    });
  }, [sendMessage]);

  const updateDocument = useCallback((documentId: string, operation: any) => {
    sendMessage({
      type: 'document_update',
      data: {
        document_id: documentId,
        operation
      }
    });
  }, [sendMessage]);

  const updateActivity = useCallback((activity: string, details?: any) => {
    sendMessage({
      type: 'activity_update',
      data: {
        activity,
        details
      }
    });
  }, [sendMessage]);

  const sendTypingIndicator = useCallback((isTyping: boolean, location?: string) => {
    sendMessage({
      type: 'typing_indicator',
      data: {
        is_typing: isTyping,
        location
      }
    });
  }, [sendMessage]);

  const requestSync = useCallback(() => {
    sendMessage({
      type: 'request_sync',
      data: {}
    });
  }, [sendMessage]);

  // Cleanup typing timeouts on unmount
  useEffect(() => {
    return () => {
      typingTimeouts.current.forEach(timeout => clearTimeout(timeout));
      typingTimeouts.current.clear();
    };
  }, []);

  const collaborationState: CollaborationState = {
    activeUsers,
    cursorPositions,
    isConnected: connectionState === 'connected',
    connectionState,
    currentUserColor
  };

  return {
    ...collaborationState,
    typingUsers: Array.from(typingUsers),
    updateCursor,
    updateDocument,
    updateActivity,
    sendTypingIndicator,
    requestSync,
    reconnect,
    disconnect
  };
};