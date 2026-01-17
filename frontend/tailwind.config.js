/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Legacy support (mapped to new or kept if distinctive)
        terminal: {
          900: '#09090b', // Zinc 950 (background-dark)
          800: '#121214', // Panel Dark
          700: '#27272a', // Border Dark
        },
        // Mock Colors
        primary: "#0ea5e9", // Electric Sky Blue
        "background-light": "#e2e4e7",
        "background-dark": "#09090b", // Zinc 950
        "panel-light": "#ffffff",
        "panel-dark": "#121214",
        "border-light": "#cbd5e1",
        "border-dark": "#27272a",
        "accent-red": "#ef4444",
        "accent-green": "#22c55e",
        "accent-amber": "#f59e0b",
        "accent-blue": "#3b82f6",

        accent: {
          main: '#0ea5e9', // Mapped to primary
          secondary: '#f59e0b', // Mapped to amber
          dim: 'rgba(14, 165, 233, 0.2)', // Low opacity primary
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        display: ['"JetBrains Mono"', 'monospace'],
        sans: ['"Inter"', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: "2px",
      },
      boxShadow: {
        'glow': '0 0 10px rgba(14, 165, 233, 0.3)',
        'glow-strong': '0 0 20px rgba(14, 165, 233, 0.5)',
        'neon': '0 0 5px theme("colors.primary"), 0 0 10px theme("colors.primary")',
      }
    },
  },
  plugins: [],
}

