/**
 * Performance optimization hooks for React components
 * Implements memoization, virtualization helpers, and performance monitoring
 */
import { useCallback, useMemo, useRef, useEffect, useState } from 'react';

/**
 * Hook for debouncing values
 * Prevents excessive re-renders on rapid value changes
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook for throttling function calls
 * Limits function execution frequency
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastRan = useRef(Date.now());
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback(
    ((...args) => {
      const now = Date.now();
      const timeSinceLastRan = now - lastRan.current;

      if (timeSinceLastRan >= delay) {
        callback(...args);
        lastRan.current = now;
      } else {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => {
          callback(...args);
          lastRan.current = Date.now();
        }, delay - timeSinceLastRan);
      }
    }) as T,
    [callback, delay]
  );
}

/**
 * Hook for measuring component render performance
 */
export function useRenderCount(componentName: string) {
  const renderCount = useRef(0);
  const renderStartTime = useRef<number>();

  useEffect(() => {
    renderCount.current += 1;
    const renderTime = renderStartTime.current 
      ? performance.now() - renderStartTime.current 
      : 0;

    if (process.env.NODE_ENV === 'development') {
      console.log(
        `[Performance] ${componentName} rendered ${renderCount.current} times. ` +
        `Last render took ${renderTime.toFixed(2)}ms`
      );
    }

    renderStartTime.current = performance.now();
  });

  return renderCount.current;
}

/**
 * Hook for lazy loading with intersection observer
 */
export function useLazyLoad(
  threshold: number = 0.1,
  rootMargin: string = '100px'
) {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
      },
      { threshold, rootMargin }
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [threshold, rootMargin]);

  return { ref, isIntersecting };
}

/**
 * Hook for virtual scrolling
 * Returns visible items for large lists
 */
export function useVirtualScroll<T>(
  items: T[],
  itemHeight: number,
  containerHeight: number,
  scrollTop: number,
  overscan: number = 3
) {
  return useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );

    const visibleItems = items.slice(startIndex, endIndex);
    const totalHeight = items.length * itemHeight;
    const offsetY = startIndex * itemHeight;

    return {
      visibleItems,
      totalHeight,
      offsetY,
      startIndex,
      endIndex
    };
  }, [items, itemHeight, containerHeight, scrollTop, overscan]);
}

/**
 * Hook for monitoring memory usage
 */
export function useMemoryMonitor(interval: number = 5000) {
  const [memoryInfo, setMemoryInfo] = useState<{
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  } | null>(null);

  useEffect(() => {
    if (!('memory' in performance)) {
      console.warn('Performance.memory is not available');
      return;
    }

    const updateMemory = () => {
      const memory = (performance as any).memory;
      setMemoryInfo({
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit
      });
    };

    updateMemory();
    const intervalId = setInterval(updateMemory, interval);

    return () => clearInterval(intervalId);
  }, [interval]);

  return memoryInfo;
}

/**
 * Hook for FPS monitoring
 */
export function useFPSMonitor() {
  const [fps, setFps] = useState(0);
  const frameCount = useRef(0);
  const lastTime = useRef(performance.now());

  useEffect(() => {
    let animationId: number;

    const measureFPS = () => {
      frameCount.current++;
      const currentTime = performance.now();
      
      if (currentTime >= lastTime.current + 1000) {
        setFps(Math.round((frameCount.current * 1000) / (currentTime - lastTime.current)));
        frameCount.current = 0;
        lastTime.current = currentTime;
      }

      animationId = requestAnimationFrame(measureFPS);
    };

    animationId = requestAnimationFrame(measureFPS);

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, []);

  return fps;
}

/**
 * Hook for preventing unnecessary re-renders
 * Memoizes complex objects/arrays
 */
export function useDeepMemo<T>(value: T, deps: any[]): T {
  const ref = useRef<T>(value);
  const depsRef = useRef<any[]>(deps);

  const hasChanged = !deps.every((dep, i) => 
    Object.is(dep, depsRef.current[i])
  );

  if (hasChanged) {
    ref.current = value;
    depsRef.current = deps;
  }

  return ref.current;
}