/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#090D16",
          card: "#121824",
          border: "#1E293B",
          text: "#F8FAFC",
          muted: "#94A3B8"
        },
        risk: {
          low: "#10B981",       // green
          medium: "#F59E0B",    // yellow
          high: "#F97316",      // orange
          critical: "#EF4444",  // red
        }
      }
    },
  },
  plugins: [],
}
