/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html","./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#05070D",
        panel: "#0B1020",
        panel2: "#111833",
        line: "#1E263F",
        sub: "#8A93A6",
        accent: "#6366F1",
        accent2: "#22D3EE",
        good: "#10B981",
        warn: "#F59E0B",
        bad: "#EF4444",
      },
      fontFamily: {
        sans: ["Inter","ui-sans-serif","system-ui","sans-serif"],
        mono: ["JetBrains Mono","ui-monospace","SFMono-Regular","monospace"],
      },
      boxShadow: {
        glow: "0 0 40px -10px rgba(99,102,241,0.45)",
        glowcyan: "0 0 40px -10px rgba(34,211,238,0.45)",
        card: "0 10px 40px -20px rgba(0,0,0,0.8)",
      },
      keyframes: {
        float: {
          "0%,100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        gridmove: {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "40px 40px" },
        },
      },
      animation: {
        float: "float 7s ease-in-out infinite",
        shimmer: "shimmer 2.5s infinite",
        gridmove: "gridmove 8s linear infinite",
      },
    },
  },
  plugins: [],
};
