import React, { useState, useEffect, useRef, useCallback, useMemo, memo } from 'react';
import { useRenderTime } from '../../utils/performanceMonitor';
import './VirtualizedList.css';

interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
  className?: string;
  onScroll?: (scrollTop: number) => void;
  getItemKey?: (item: T, index: number) => string | number;
}

interface VisibleRange {
  start: number;
  end: number;
}

function VirtualizedList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 3,
  className = '',
  onScroll,
  getItemKey = (_, index) => index,
}: VirtualizedListProps<T>) {
  useRenderTime('VirtualizedList');

  const [scrollTop, setScrollTop] = useState(0);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  // Calculate which items should be visible
  const visibleRange: VisibleRange = useMemo(() => {
    const start = Math.floor(scrollTop / itemHeight);
    const end = Math.min(
      start + Math.ceil(containerHeight / itemHeight) + overscan,
      items.length - 1
    );
    
    return {
      start: Math.max(0, start - overscan),
      end,
    };
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length]);

  // Calculate total height
  const totalHeight = useMemo(() => items.length * itemHeight, [items.length, itemHeight]);

  // Calculate offset for visible items
  const offsetY = useMemo(() => visibleRange.start * itemHeight, [visibleRange.start, itemHeight]);

  // Get visible items
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end + 1).map((item, index) => ({
      item,
      index: visibleRange.start + index,
      key: getItemKey(item, visibleRange.start + index),
    }));
  }, [items, visibleRange.start, visibleRange.end, getItemKey]);

  // Handle scroll events
  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = event.currentTarget.scrollTop;
    setScrollTop(newScrollTop);
    onScroll?.(newScrollTop);
  }, [onScroll]);

  // Scroll to specific index
  const scrollToIndex = useCallback((index: number) => {
    if (scrollElementRef.current) {
      const scrollTop = index * itemHeight;
      scrollElementRef.current.scrollTop = scrollTop;
      setScrollTop(scrollTop);
    }
  }, [itemHeight]);

  // Scroll to top
  const scrollToTop = useCallback(() => {
    scrollToIndex(0);
  }, [scrollToIndex]);

  // Expose scroll methods via ref
  React.useImperativeHandle(scrollElementRef, () => ({
    scrollToIndex,
    scrollToTop,
    scrollTop,
  }));

  return (
    <div
      ref={scrollElementRef}
      className={`virtualized-list ${className}`}
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      {/* Total height container */}
      <div
        className="virtualized-list-total"
        style={{ height: totalHeight, position: 'relative' }}
      >
        {/* Visible items container */}
        <div
          className="virtualized-list-items"
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map(({ item, index, key }) => (
            <div
              key={key}
              className="virtualized-list-item"
              style={{
                height: itemHeight,
                overflow: 'hidden',
              }}
              data-index={index}
            >
              {renderItem(item, index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default memo(VirtualizedList) as <T>(props: VirtualizedListProps<T>) => JSX.Element;

// Hook for easy virtualized list usage
export const useVirtualizedList = <T,>(
  items: T[],
  itemHeight: number,
  containerHeight: number
) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const visibleRange = useMemo(() => {
    const start = Math.floor(scrollTop / itemHeight);
    const end = Math.min(
      start + Math.ceil(containerHeight / itemHeight),
      items.length - 1
    );
    
    return { start: Math.max(0, start), end };
  }, [scrollTop, itemHeight, containerHeight, items.length]);

  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end + 1);
  }, [items, visibleRange]);

  return {
    visibleItems,
    visibleRange,
    totalHeight: items.length * itemHeight,
    offsetY: visibleRange.start * itemHeight,
    onScroll: setScrollTop,
  };
};

// Specialized components for common use cases
export const VirtualizedTaskList = memo<{
  tasks: Array<{ id: string; title: string; completed: boolean; priority: string }>;
  onTaskClick?: (task: any) => void;
  containerHeight: number;
}>(({ tasks, onTaskClick, containerHeight }) => {
  const renderTask = useCallback((task: any, index: number) => (
    <div 
      className={`task-item ${task.completed ? 'completed' : ''}`}
      onClick={() => onTaskClick?.(task)}
    >
      <div className="task-checkbox">
        {task.completed ? '✅' : '☐'}
      </div>
      <div className="task-content">
        <div className="task-title">{task.title}</div>
        <div className="task-meta">
          <span className={`priority ${task.priority.toLowerCase()}`}>
            {task.priority}
          </span>
        </div>
      </div>
    </div>
  ), [onTaskClick]);

  return (
    <VirtualizedList
      items={tasks}
      itemHeight={60}
      containerHeight={containerHeight}
      renderItem={renderTask}
      getItemKey={(task) => task.id}
      className="virtualized-task-list"
    />
  );
});

VirtualizedTaskList.displayName = 'VirtualizedTaskList';

export const VirtualizedFileList = memo<{
  files: Array<{ id: string; name: string; size: number; type: string; lastModified: Date }>;
  onFileClick?: (file: any) => void;
  containerHeight: number;
}>(({ files, onFileClick, containerHeight }) => {
  const formatFileSize = useCallback((bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  const formatDate = useCallback((date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  }, []);

  const getFileIcon = useCallback((type: string) => {
    switch (type.toLowerCase()) {
      case 'pdf': return '📄';
      case 'doc':
      case 'docx': return '📝';
      case 'xls':
      case 'xlsx': return '📊';
      case 'ppt':
      case 'pptx': return '📽️';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif': return '🖼️';
      case 'mp4':
      case 'avi':
      case 'mov': return '🎥';
      case 'mp3':
      case 'wav': return '🎵';
      case 'zip':
      case 'rar': return '📦';
      default: return '📄';
    }
  }, []);

  const renderFile = useCallback((file: any, index: number) => (
    <div 
      className="file-item"
      onClick={() => onFileClick?.(file)}
    >
      <div className="file-icon">
        {getFileIcon(file.type)}
      </div>
      <div className="file-info">
        <div className="file-name">{file.name}</div>
        <div className="file-meta">
          <span className="file-size">{formatFileSize(file.size)}</span>
          <span className="file-date">{formatDate(file.lastModified)}</span>
        </div>
      </div>
    </div>
  ), [onFileClick, getFileIcon, formatFileSize, formatDate]);

  return (
    <VirtualizedList
      items={files}
      itemHeight={64}
      containerHeight={containerHeight}
      renderItem={renderFile}
      getItemKey={(file) => file.id}
      className="virtualized-file-list"
    />
  );
});

VirtualizedFileList.displayName = 'VirtualizedFileList';