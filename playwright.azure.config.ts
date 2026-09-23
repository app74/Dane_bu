import { defineConfig } from "@playwright/test";
import { tmpdir } from "node:os";
import { join } from "node:path";

// E2E test of the Azure App Service package (python azure/build_package.py) run locally:
// frontend + API on one origin, WEBSITE_SITE_NAME simulates App Service, and the tests
// inject the X-MS-CLIENT-PRINCIPAL-* headers that Easy Auth (Microsoft Entra ID) would add.
// Requires the backend dependencies on PATH (activate backend\.venv first).
const database = join(tmpdir(), `dane-azure-e2e-${Date.now()}.db`).replace(/\\/g, "/");

export default defineConfig({
  testDir: "./e2e-azure",
  workers: 1,
  use: { baseURL: "http://127.0.0.1:8010" },
  webServer: {
    command:
      "python -m alembic upgrade head && python -m uvicorn azure_app:app --host 127.0.0.1 --port 8010",
    cwd: "build/azure",
    url: "http://127.0.0.1:8010/api/health",
    reuseExistingServer: false,
    env: {
      WEBSITE_SITE_NAME: "dane-bu-e2e",
      DATABASE_URL: `sqlite:///${database}`,
      FS_LOOKUP_ENABLED: "0",
    },
  },
});
