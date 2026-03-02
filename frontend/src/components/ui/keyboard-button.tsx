"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { clsx, type ClassValue } from "clsx";

interface KeyboardButtonProps {
  children: ReactNode;
  variant?: "primary" | "secondary";
  size?: "sm" | "md" | "lg";
  icon?: ReactNode;
  badge?: string;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
  className?: string;
  fullWidth?: boolean;
}

export function KeyboardButton({
  children,
  variant = "primary",
  size = "md",
  icon,
  badge,
  href,
  onClick,
  disabled = false,
  type = "button",
  className = "",
  fullWidth = false,
}: KeyboardButtonProps) {
  // Size-specific classes
  const sizeClasses = {
    sm: {
      wrapper: "",
      shadow: "rounded-md translate-y-[2px] group-hover:translate-y-[1px] group-active:translate-y-[0.5px]",
      keycap: "rounded-md px-3 py-1.5 text-xs gap-1.5 group-hover:translate-y-[0.5px] group-active:translate-y-[1px]",
      gloss: "h-[40%] rounded-t-[2px]",
      icon: "h-3 w-3",
      badge: "text-[9px] px-1 py-0",
    },
    md: {
      wrapper: "",
      shadow: "rounded-lg translate-y-[3px] group-hover:translate-y-[2px] group-active:translate-y-[1px]",
      keycap: "rounded-lg px-5 py-2.5 text-sm gap-1.5 group-hover:translate-y-[1px] group-active:translate-y-[2px]",
      gloss: "h-[40%] rounded-t-md",
      icon: "h-4 w-4",
      badge: "text-[10px] px-1.5 py-0.5",
    },
    lg: {
      wrapper: "",
      shadow: "rounded-xl translate-y-[3px] group-hover:translate-y-[2px] group-active:translate-y-[1px]",
      keycap: "rounded-xl px-6 py-3 text-base gap-2 group-hover:translate-y-[1px] group-active:translate-y-[2px]",
      gloss: "h-[40%] rounded-t-lg",
      icon: "h-5 w-5",
      badge: "text-xs px-2 py-0.5",
    },
  };

  // Variant-specific classes
  const variantClasses = {
    primary: {
      shadow: "bg-violet-400/60",
      keycap: "from-violet-400 via-blue-500 to-cyan-500 text-white border-violet-500/50 shadow-[inset_0_1px_0_rgba(255,255,255,0.6),inset_0_-1px_0_rgba(0,0,0,0.1)]",
      gloss: "from-white/40",
      icon: "text-white/90",
      badge: "text-white/80 border-white/30 bg-white/10",
    },
    secondary: {
      shadow: "bg-slate-300",
      keycap: "bg-white text-slate-600 border-slate-300 shadow-[inset_0_1px_0_rgba(255,255,255,1),inset_0_-1px_0_rgba(0,0,0,0.02)]",
      gloss: "from-white/80",
      icon: "text-slate-400",
      badge: "text-slate-400 border-slate-200 bg-slate-50",
    },
  };

  const s = sizeClasses[size];
  const v = variantClasses[variant];

  const buttonContent = (
    <>
      {/* Shadow */}
      <span
        className={clsx(
          "absolute inset-0 transition-transform duration-100",
          s.shadow,
          v.shadow
        )}
      />

      {/* Keycap */}
      <span
        className={clsx(
          "relative inline-flex items-center font-bold tracking-tight border-[2px] transition-all duration-100",
          variant === "primary" && "bg-gradient-to-b",
          fullWidth && "w-full justify-center",
          s.keycap,
          v.keycap,
          disabled && "opacity-60 cursor-not-allowed"
        )}
      >
        {/* Gloss overlay */}
        <span
          className={clsx(
            "absolute inset-x-0 top-0 bg-gradient-to-b to-transparent pointer-events-none",
            s.gloss,
            v.gloss
          )}
        />

        {/* Icon */}
        {icon && (
          <span className={clsx("relative shrink-0", s.icon, v.icon)}>
            {icon}
          </span>
        )}

        {/* Text */}
        <span className="relative font-bold tracking-tight drop-shadow-sm">
          {children}
        </span>

        {/* Badge */}
        {badge && (
          <span
            className={clsx(
              "relative ml-1 font-bold border rounded",
              s.badge,
              v.badge
            )}
          >
            {badge}
          </span>
        )}
      </span>
    </>
  );

  const wrapperClass = clsx(
    "group relative inline-flex items-center select-none",
    fullWidth && "w-full",
    className
  );

  if (href && !disabled) {
    return (
      <Link href={href} className={wrapperClass} onClick={onClick}>
        {buttonContent}
      </Link>
    );
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={wrapperClass}
    >
      {buttonContent}
    </button>
  );
}
