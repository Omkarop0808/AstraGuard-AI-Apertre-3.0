/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      colors: {
        background: '#020617', // Slate 950
        surface: '#0f172a',    // Slate 900
        primary: '#3b82f6',    // Blue 500
        secondary: '#64748b',  // Slate 500
        success: '#22c55e',    // Green 500
        warning: '#eab308',    // Yellow 500
        danger: '#ef4444',     // Red 500
        muted: '#94a3b8',      // Slate 400
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
