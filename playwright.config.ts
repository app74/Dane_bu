import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://127.0.0.1:5173" },
  webServer: [
    {
      command: "npm --prefix frontend run dev -- --host 127.0.0.1",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: true,
    },
    {
      command: "C:\\Users\\PC\\AppData\\Local\\Programs\\Python\\Python312\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      cwd: "backend",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: true,
    },
  ],
});
