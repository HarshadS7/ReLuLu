"use client";

import { useEffect, useState } from "react";
import localFont from "next/font/local";

const cosity = localFont({
  src: "../fonts/ALTRONED Trial.otf",
  display: "swap",
});

export default function SpectraLoader() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(false), 3600);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className="loader-fade-exit fixed inset-0 z-[100] flex items-center justify-center bg-[#0d0417] overflow-hidden font-sans">
      
      {/* Background: Rich Dark Violet Gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#2e1065_0%,_#0d0417_70%)] opacity-60" />

      <div className="relative flex items-center justify-center w-full">
        
        {/* Container for both ball and text — they share the same baseline */}
        <div className="relative">
          {/* 2. THE WHITE TEXT — grows upward from baseline */}
          <h1 className={`${cosity.className} text-8xl md:text-9xl tracking-tighter text-white animate-text-liquid-rise select-none`}>
            SPECTRA
          </h1>
          
          {/* 1. THE WHITE BALL — drops to the bottom of the text and spreads along it */}
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 z-20">
            <div className="h-16 w-16 rounded-full bg-white shadow-[0_0_40px_rgba(255,255,255,0.3)] animate-ball-liquid-morph origin-bottom" />
          </div>
        </div>

      </div>
    </div>
  );
}