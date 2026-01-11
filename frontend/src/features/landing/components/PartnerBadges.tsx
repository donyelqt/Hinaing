"use client";

import Image from "next/image";
import { useState, useEffect, useRef } from "react";

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
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Prototype context</p>
            <p className="text-sm font-medium text-slate-700 leading-snug">
              Concept for Baguio City sentiment monitoring — not an official government product.
            </p>
          </div>
        </div>
        <span className="hidden rounded-full bg-slate-900 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-white sm:inline-flex">
          Early prototype
        </span>
      </div>
    </section>
  );
}
