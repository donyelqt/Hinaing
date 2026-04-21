"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import clsx from "clsx";

type ScrollRevealProps = {
  children: ReactNode;
  className?: string;
  as?: "div" | "section";
  delay?: number;
};

export function ScrollReveal({ children, className, as: Component = "div", delay = 0 }: ScrollRevealProps) {
  const ref = useRef<HTMLElement | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (!ref.current) return;

    // Dynamic threshold based on viewport height - critical fix for mobile
    // On mobile (small viewports), use lower threshold because elements take more vertical space
    const isMobile = window.innerHeight < 768;
    const threshold = isMobile ? 0.02 : 0.15; // 2% for mobile, 15% for desktop

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { 
        threshold,
        rootMargin: isMobile ? '100px' : '0px' // Extra root margin on mobile to trigger earlier
      },
    );

    observer.observe(ref.current);

    // Fail-safe timeout: Ensure sections render even if observer never triggers (edge cases)
    const timeoutId = setTimeout(() => {
      setIsVisible(prev => {
        if (!prev) {
          observer.disconnect();
          return true;
        }
        return prev;
      });
    }, 2000 + delay); // Wait 2s plus delay before forcing render

    return () => {
      observer.disconnect();
      clearTimeout(timeoutId);
    };
  }, [delay]);

  return (
    <Component
      ref={ref as React.RefObject<any> as any}
      className={clsx(
        "transition-all duration-500 ease-out will-change-transform",
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
        className,
      )}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </Component>
  );
}
