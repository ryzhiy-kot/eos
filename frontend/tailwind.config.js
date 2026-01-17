/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          900: '#0a0a0f', // Main Background
          800: '#141419', // Panel Background
          700: '#1f1f26', // Border/Hover
        },
        accent: {
          main: '#00f0ff', // Cyan - Primary Action/Focus
          secondary: '#ffaa00', // Amber - Warnings/Highlights
          dim: 'rgba(0, 240, 255, 0.2)', // Low opacity main
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'], // Tech look
        sans: ['"Inter"', 'sans-serif'],
      },
      boxShadow: {
        'glow': '0 0 10px rgba(0, 240, 255, 0.3)',
        'glow-strong': '0 0 20px rgba(0, 240, 255, 0.5)',
      }
    },
  },
  plugins: [],
}

