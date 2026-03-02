"use client";

import Image from "next/image";
import { useState, useEffect, useRef } from "react";
import { Shield, CheckCircle, Award } from "lucide-react";

export function PartnerBadges() {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Array of images for the slideshow - add more images as needed
  const images = [
    {
      src: "/baguio-city-seal.png",
      alt: "Official seal of Baguio City",
    },
    {
      src: "/UC.png",
      alt: "Official seal of UC Baguio",
    },
    {
      src: "/citcs.png",
      alt: "Official seal of UC Baguio - CITCS",
    },
    // Add more images here as needed for the slideshow
    // {
    //   src: "/university-logo.png", // Replace with actual university logo
    //   alt: "University research partner logo",
    // },
    // {
    //   src: "/research-logo.png", // Replace with actual research logo
    //   alt: "Research methodology logo",
    // }
  ];

  useEffect(() => {
    if (images.length <= 1) return; // No need to animate if there's only one image

    const interval = setInterval(() => {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentImageIndex((prevIndex) => (prevIndex + 1) % images.length);
        setIsAnimating(false);
      }, 500); // Match the transition duration
    }, 4000); // Change image every 4 seconds (including transition time)

    return () => clearInterval(interval);
  }, [images.length]);

  // Pause animation on hover
  const handleMouseEnter = () => {
    setIsAnimating(true);
  };

  const handleMouseLeave = () => {
    setIsAnimating(false);
  };

  return (
    <section className="bg-slate-50/80 border-t border-slate-200/50">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-6 text-xs text-slate-500 sm:px-6 xl:px-8">
        <div className="flex items-center gap-4">
          <div
            ref={containerRef}
            className="relative h-28 w-28 overflow-hidden rounded-full border border-slate-200 bg-white flex-shrink-0 shadow-sm"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            <div className="relative w-full h-full overflow-hidden rounded-full">
              {images.map((image, index) => (
                <div
                  key={index}
                  className={`absolute inset-0 transition-transform duration-700 ease-in-out ${
                    index === currentImageIndex
                      ? "translate-x-0 z-20"
                      : index < currentImageIndex
                        ? "-translate-x-full z-10"
                        : "translate-x-full z-10"
                  } ${
                    isAnimating
                      ? "transition-transform duration-700 ease-in-out"
                      : ""
                  }`}
                >
                  <Image
                    src={image.src}
                    alt={image.alt}
                    fill
                    sizes="100px"
                    className={`object-contain ${
                      image.src === "/citcs.png" ? "p-0 scale-150" : "p-1.5"
                    }`}
                  />
                </div>
              ))}
            </div>

            {/* Animated border effect */}
            <div className="absolute inset-0 rounded-full border border-transparent bg-gradient-to-r from-violet-500/20 via-blue-500/20 to-cyan-500/20 [mask-composite:intersect] [mask:radial-gradient(ellipse_at_center,white_70%,transparent_90%)] animate-spin-slow" />
          </div>
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Autonomous, Self-Learning & Multi-Signal Verification</p>
            <p className="text-sm font-medium text-slate-700 leading-snug">
              Sentiment monitoring system — thesis research project for Baguio City.
            </p>
          </div>
        </div>
        {/* TRL 7 Validation Badge - Medal Design */}
        <div className="hidden sm:flex flex-col items-center">
          {/* Medal Badge Container */}
          <div className="group relative">
            {/* Outer glow effect - Vibrant blue */}
            <div className="absolute -inset-1 rounded-2xl bg-blue-500/40 blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            {/* Main Badge - Vibrant blue background */}
            <div className="relative flex items-center gap-3 rounded-xl bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 p-[2px] shadow-xl shadow-blue-600/30">
              {/* Inner content - lighter blue */}
              <div className="flex items-center gap-3 rounded-[10px] bg-gradient-to-br from-blue-500 to-blue-700 px-4 py-3">
                {/* Shield Icon with white/cyan accent */}
                <div className="relative flex-shrink-0">
                  <div className="absolute inset-0 rounded-lg bg-cyan-300/40 blur-md" />
                  <div className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-white shadow-lg shadow-blue-900/20">
                    <Shield className="h-5 w-5 text-blue-600 fill-blue-100" />
                  </div>
                  {/* Small check badge overlay */}
                  <div className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 border-2 border-blue-600 shadow-sm">
                    <CheckCircle className="h-3 w-3 text-white" />
                  </div>
                </div>
                
                {/* Text Content */}
                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-300">TRL 7 Validated</span>
                    <span className="h-1 w-1 rounded-full bg-blue-300" />
                    <span className="text-[10px] font-medium text-blue-200">System Architecture</span>
                  </div>
                  <span className="text-xs font-semibold text-white leading-tight">
                    Former Senior Software Engineer at IBM
                  </span>
                </div>
                
                {/* Award Icon */}
                <div className="flex-shrink-0 pl-2 border-l border-blue-400/50">
                  <Award className="h-5 w-5 text-cyan-300" />
                </div>
              </div>
            </div>
            
            {/* Ribbon effect below badge */}
            <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 flex">
              <div className="h-0 w-0 border-l-[6px] border-r-[6px] border-t-[8px] border-l-transparent border-r-transparent border-t-blue-600" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
