# Personal CTO AI frontend

A small React, TypeScript, and Vite interface for describing an app, starting a
generation run, revisiting previous runs, and downloading a completed project.

## Run locally

Start the FastAPI backend in one PowerShell window:

```powershell
cd ..\backend
uvicorn app.main:app --reload
```

Then start the frontend in another window:

```powershell
cd ..\frontend
npm install
npm run dev
```

The Vite development server proxies `/api/*` to `http://127.0.0.1:8000/*`.
Generation requires the backend's model configuration to be set. The frontend
does not store or display provider credentials. If the backend does not have an
OpenAI key configured, expand **OpenAI API key** in the prompt form to provide
one for that generation. It is sent only with that request and is not saved in
browser storage or build history; leave it blank to use the backend's key.
Only send a key to a backend you trust; use HTTPS when connecting to a remote
backend.

## Use the app

1. Describe the app you want to create in the prompt box and select **Start
   creating**. Prompts must be at least 10 characters.
2. Select a run in **History** to check its queued, running, completed, or failed
   status. Active runs refresh automatically while the page is open.
3. Download the generated project as a ZIP when generation completes.

Generated test files are included in the download but are not run automatically.
Review generated code before running it. Workflow progress and detailed repair
history are not currently exposed by the backend.

Set `VITE_API_BASE_URL` to override the default `/api` URL. For a direct backend
connection, create `.env.local` with `VITE_API_BASE_URL=http://127.0.0.1:8000`;
the backend must then allow the frontend's origin.

## Checks

```powershell
npm run build
npm run lint
npm test
```
