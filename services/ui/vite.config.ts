import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// @ts-expect-error - vite-plugin-eslint has module resolution issues
import eslint from "vite-plugin-eslint";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), eslint(), tailwindcss()],
});
