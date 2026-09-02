"use client";

interface GraphPaperProps {
  children: React.ReactNode;
  className?: string;
  variant?: "light" | "white" | "cream";
  opacity?: number;
}

export function GraphPaper({ 
  children, 
  className = "",
  variant = "light",
  opacity = 0.6
}: GraphPaperProps) {
  const bgColors = {
    light: "#fafbfc",
    white: "#ffffff",
    cream: "#f8f7f4"
  };

  return (
    <div 
      className={`relative ${className}`}
      style={{ backgroundColor: bgColors[variant] }}
    >
      {/* Minor grid lines - 20px spacing */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, #e1e8ed 1px, transparent 1px),
            linear-gradient(to bottom, #e1e8ed 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px',
          opacity: opacity * 0.6
        }}
      />
      
      {/* Major grid lines - 100px spacing */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, #cbd5e1 1px, transparent 1px),
            linear-gradient(to bottom, #cbd5e1 1px, transparent 1px)
          `,
          backgroundSize: '100px 100px',
          opacity: opacity
        }}
      />
      
      {/* Paper texture */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
