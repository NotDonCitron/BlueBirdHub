/**
 * Collaborative Cursor Component - Shows other users' cursors in real-time
 */

import React, { useEffect, useState } from 'react';
import './CollaborativeCursor.css';

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

interface CollaborativeCursorProps {
  cursors: CursorPosition[];
  currentFilePath?: string;
  editorContainer?: HTMLElement | null;
  className?: string;
}

const CollaborativeCursor: React.FC<CollaborativeCursorProps> = ({
  cursors,
  currentFilePath,
  editorContainer,
  className = ''
}) => {
  const [cursorElements, setCursorElements] = useState<Map<string, HTMLElement>>(new Map());

  // Filter cursors for current file
  const relevantCursors = cursors.filter(cursor => 
    !currentFilePath || cursor.file_path === currentFilePath
  );

  useEffect(() => {
    if (!editorContainer) return;

    const newCursorElements = new Map<string, HTMLElement>();

    relevantCursors.forEach(cursor => {
      const { user_id, username, cursor_color, position } = cursor;
      
      // Create or update cursor element
      let cursorElement = cursorElements.get(user_id);
      
      if (!cursorElement) {
        cursorElement = document.createElement('div');
        cursorElement.className = 'collaborative-cursor';
        cursorElement.innerHTML = `
          <div class="cursor-line" style="background-color: ${cursor_color}"></div>
          <div class="cursor-label" style="background-color: ${cursor_color}">
            <span class="cursor-username">${username}</span>
          </div>
        `;
        editorContainer.appendChild(cursorElement);
      }

      // Update cursor position
      const lineHeight = 20; // Adjust based on your editor's line height
      const charWidth = 8; // Adjust based on your editor's character width
      
      const top = position.line * lineHeight;
      const left = position.column * charWidth;
      
      cursorElement.style.transform = `translate(${left}px, ${top}px)`;
      cursorElement.style.opacity = '1';
      
      // Update color if changed
      const cursorLine = cursorElement.querySelector('.cursor-line') as HTMLElement;
      const cursorLabel = cursorElement.querySelector('.cursor-label') as HTMLElement;
      
      if (cursorLine) cursorLine.style.backgroundColor = cursor_color;
      if (cursorLabel) cursorLabel.style.backgroundColor = cursor_color;
      
      newCursorElements.set(user_id, cursorElement);
    });

    // Remove cursors that are no longer present
    cursorElements.forEach((element, userId) => {
      if (!newCursorElements.has(userId)) {
        element.remove();
      }
    });

    setCursorElements(newCursorElements);

    // Cleanup function
    return () => {
      cursorElements.forEach(element => {
        if (element.parentNode) {
          element.parentNode.removeChild(element);
        }
      });
    };
  }, [relevantCursors, editorContainer]);

  // Auto-hide cursors after inactivity
  useEffect(() => {
    const hideInactiveCursors = () => {
      const now = new Date().getTime();
      const inactivityThreshold = 30000; // 30 seconds

      cursorElements.forEach((element, userId) => {
        const cursor = relevantCursors.find(c => c.user_id === userId);
        if (cursor) {
          const cursorTime = new Date(cursor.timestamp).getTime();
          const isInactive = now - cursorTime > inactivityThreshold;
          
          element.style.opacity = isInactive ? '0.3' : '1';
        }
      });
    };

    const interval = setInterval(hideInactiveCursors, 5000);
    return () => clearInterval(interval);
  }, [cursorElements, relevantCursors]);

  return (
    <div className={`collaborative-cursors-container ${className}`}>
      {/* Cursors are rendered directly into the editor container */}
    </div>
  );
};

export default CollaborativeCursor;