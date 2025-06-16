/**
 * Virtual List Component for efficient rendering of large lists
 * Implements windowing technique to only render visible items
 */
import React, { useRef, useState, useCallback, useEffect, memo } from 'react';
import { useVirtualScroll } from '../../hooks/usePerformance';
import './VirtualList.css';

interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  height: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  className?: string;
  overscan?: number;
  onScroll?: (scrollTop: number) => void;
}

function VirtualListComponent<T>({
  items,
  itemHeight,
  height,
  renderItem,
  className = '',
  overscan = 3,
  onScroll
}: VirtualListProps<T>) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);

  const {
    visibleItems,
    totalHeight,
    offsetY,
    startIndex
  } = useVirtualScroll(items, itemHeight, height, scrollTop, overscan);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);
    onScroll?.(newScrollTop);
  }, [onScroll]);

  // Scroll to item function
  const scrollToItem = useCallback((index: number) => {
    if (scrollContainerRef.current) {
      const scrollPosition = Math.min(
        index * itemHeight,
        totalHeight - height
      );
      scrollContainerRef.current.scrollTop = scrollPosition;
    }
  }, [itemHeight, totalHeight, height]);

  // Expose scrollToItem via ref
  useEffect(() => {
    if (scrollContainerRef.current) {
      (scrollContainerRef.current as any).scrollToItem = scrollToItem;
    }
  }, [scrollToItem]);

  return (
    <div
      ref={scrollContainerRef}
      className={`virtual-list-container ${className}`}
      style={{ height, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div
        className="virtual-list-content"
        style={{ height: totalHeight, position: 'relative' }}
      >
        <div
          className="virtual-list-items"
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0
          }}
        >
          {visibleItems.map((item, index) => (
            <div
              key={startIndex + index}
              className="virtual-list-item"
              style={{ height: itemHeight }}
            >
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Memoized component to prevent unnecessary re-renders
export const VirtualList = memo(VirtualListComponent) as typeof VirtualListComponent;

// Hook for easy virtual list usage
export function useVirtualList<T>(items: T[], itemHeight: number) {
  const [containerHeight, setContainerHeight] = useState(400);
  const [scrollTop, setScrollTop] = useState(0);
  
  const measureContainer = useCallback((element: HTMLElement | null) => {
    if (element) {
      setContainerHeight(element.clientHeight);
    }
  }, []);

  const virtualData = useVirtualScroll(
    items,
    itemHeight,
    containerHeight,
    scrollTop
  );

  return {
    ...virtualData,
    measureContainer,
    setScrollTop,
    containerHeight
  };
}