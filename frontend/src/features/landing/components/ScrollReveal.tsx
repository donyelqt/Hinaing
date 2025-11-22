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

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15 },
    );

    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

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
