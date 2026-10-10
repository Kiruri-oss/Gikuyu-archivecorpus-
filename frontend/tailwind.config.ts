import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        earth: { 50: "#faf6f0", 500: "#8b6f47", 900: "#3d2f1f" },
        savanna: { 50: "#fff8e7", 500: "#d4a017", 900: "#6b5008" },
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};

export default config;