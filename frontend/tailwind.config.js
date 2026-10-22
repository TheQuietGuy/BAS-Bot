/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0E1016",
        surface: "#171A22",
        raised: "#1D212B",
        rule: "#2A2E3A",
        murasaki: {
          DEFAULT: "#7C6FE0",
          soft: "#5A4FB0",
        },
        ai: {
          DEFAULT: "#4C7EF0",
          soft: "#3A5FB8",
        },
        hanko: "#D6432F",
        ivory: "#ECE9F5",
        muted: "#8A8FA6",
      },
      fontFamily: {
        display: ["'Shippori Mincho'", "serif"],
        sans: ["'Space Grotesk'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        panel: "3px",
      },
    },
  },
  plugins: [],
};
