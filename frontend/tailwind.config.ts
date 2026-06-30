import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        muted: "#5b6475",
        line: "#d9dee7",
        panel: "#ffffff",
        canvas: "#f7f8fb",
        blue: {
          signal: "#1f5fbf"
        },
        green: {
          signal: "#18794e"
        },
        amber: {
          signal: "#9a6700"
        }
      },
      boxShadow: {
        soft: "0 1px 2px rgba(23, 32, 51, 0.06), 0 8px 20px rgba(23, 32, 51, 0.04)"
      }
    }
  },
  plugins: []
};

export default config;
