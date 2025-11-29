import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "hinaing-blue": {
          50: "#f4f8ff",
          100: "#e8f0ff",
          200: "#c6dcff",
          300: "#9ebeff",
          400: "#7098ff",
          500: "#4a70f1",
          600: "#3056d6",
          700: "#2747af",
          800: "#213d8c",
          900: "#1e3572",
        },
        "hinaing-gold": "#f59f0b",
      },
      fontFamily: {
        sans: ["var(--font-roboto)", "system-ui", "sans-serif"],
        mono: ["var(--font-roboto-mono)", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        subtle: "0 10px 30px -12px rgba(15, 23, 42, 0.25)",
        card: "0 20px 45px -30px rgba(15, 23, 42, 0.35)",
      },
      borderRadius: {
        xl: "1rem",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        progress: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "progress": "progress 1.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
