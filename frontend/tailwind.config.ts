import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#03060f",
        card: "#0a0e1a",
        border: "#1f2937",
        primary: {
          DEFAULT: "#7C3AED",
          hover: "#8b5cf6",
        },
        secondary: {
          DEFAULT: "#00d4ff",
          hover: "#33ddff",
        },
        text: {
          primary: "#ffffff",
          secondary: "#94a3b8",
          muted: "#64748b",
        }
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
        '3xl': '24px',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'sans-serif'],
      },
      spacing: {
        '4': '4px',
        '8': '8px',
        '12': '12px',
        '16': '16px',
        '20': '20px',
      }
    },
  },
  plugins: [],
};
export default config;
