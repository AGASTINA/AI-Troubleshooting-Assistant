# AI Troubleshooting Assistant

A local technical support assistant built with React and Flask. It can use a configured OpenAI-compatible hosted model for diagnosis, falls back to transparent local rules when the model is unavailable, and offers a small set of user-approved Windows repairs.

> **Important:** The hosted model is optional and is not bundled. Without credentials, diagnoses use local rules. The model can suggest guidance but cannot issue machine commands. Automated repairs come only from the fixed backend allow-list and require a confirmation in the UI.

## Features

- React chat interface with example prompts
- Flask REST API (`POST /api/chat`, `GET /api/health`)
- Hosted diagnosis through an OpenAI-compatible chat-completions API, with validated JSON output and offline rule fallback
- Rule-based categories: network, login, slow performance, application errors, printer, and unknown issues
- User-confirmed Windows repairs: flush DNS cache and reset Microsoft Store cache when relevant
- Input validation, safe handling of unsupported input, and response categories
- Automated backend tests with pytest
- CORS enabled for local development

## Project structure

```text
ai-troubleshooting-assistant/
├── backend/
│   ├── app.py
│   ├── ai_assistant.py
│   ├── repairs.py
│   ├── troubleshooting.py
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       └── test_api.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       └── styles.css
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Git (optional, for version control)

## Run the backend

Open a terminal in the project root:

### Windows PowerShell

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again. You can also run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe app.py` without activation.

### macOS/Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5000`.

## Configure the hosted model (optional)

Copy `backend/.env.example` to `backend/.env`, then set `AI_API_KEY` and `AI_MODEL`. Keep `.env` private; it is ignored by Git. `AI_API_BASE_URL` defaults to `https://api.openai.com/v1` and can point to another provider that supports the OpenAI-compatible chat-completions API and JSON response mode. Install the Python dependencies again after updating `requirements.txt`:

```powershell
cd backend
python -m pip install -r requirements.txt
```

Restart Flask after changing `.env`. If the provider is not configured, times out, or returns invalid JSON, the app uses the local rules and labels that fallback in the chat.

## Deploy to Render

The root `render.yaml` describes a single web service that builds the React frontend and serves it from Flask, keeping API calls same-origin. To deploy:

1. Push this project to a GitHub repository.
2. In Render, choose **New +** then **Blueprint**, connect the repository, and apply the `render.yaml` configuration.
3. Wait for the build and open the `onrender.com` URL shown by Render. The health check is `/api/health`.
4. To enable hosted diagnosis, add `AI_API_KEY` under the service's Environment settings and redeploy. Do not commit the key.

The free plan may sleep when idle and take time to wake. Without `AI_API_KEY`, the deployed service continues using local rules. Windows repair endpoints only affect the machine running the backend; a Render container is not the visitor's computer, so local machine repairs are unavailable in the hosted deployment.

## Run the frontend

Open a second terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

Keep both terminals running while using the app.

## API examples

Health check:

```bash
curl http://127.0.0.1:5000/api/health
```

Chat request:

```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"My Wi-Fi is not working\"}"
```

Expected response shape:

```json
{
  "category": "network",
  "title": "Network connectivity",
  "answer": "Try these checks in order:",
  "steps": [
    "Check whether Wi-Fi is enabled and airplane mode is off.",
    "Confirm whether other devices can connect to the same network.",
    "Restart the router only if you are authorized to do so.",
    "Disconnect and reconnect to the network, then retry."
  ],
  "follow_up": "Do you see an error message, or is the network not visible at all?"
}
```

## Run tests

From the project root:

```bash
cd backend
python -m pip install -r requirements.txt
python -m pytest -v
```

The tests cover the health endpoint, valid requests, empty input, invalid JSON, and representative issue categories.

## Automated repairs and safety

On Windows, network diagnoses can offer a DNS cache flush, and Microsoft Store issues can offer the built-in Store cache reset. Each action has a fixed implementation, is displayed before execution, and requires user confirmation. No command text comes from the model or the chat input. Other repairs are guidance-only. Run this app only on a computer you are authorized to manage; do not expose the local Flask server to a public network.

## Manual QA checklist

| Test | Input/action | Expected result |
|---|---|---|
| Network issue | `My Wi-Fi is not working` | Network steps returned |
| Login issue | `I cannot log in` | Login steps returned |
| Slow device | `My laptop is very slow` | Performance steps returned |
| App failure | `The application keeps crashing` | Application steps returned |
| Printer issue | `Printer is not printing` | Printer steps returned |
| Empty message | Submit spaces only | HTTP 400 with validation message |
| Missing field | Send `{}` | HTTP 400 with validation message |
| Wrong content type/body | Send invalid JSON | API returns a controlled error |
| Unknown topic | `How do I bake a cake?` | Safe fallback asks for more detail |
| Long input | Submit a message over 1,000 characters | API rejects it with HTTP 400 |

## Troubleshooting common setup issues

- **`npm` not recognized:** Install Node.js LTS, reopen the terminal, and check `node -v` and `npm -v`.
- **`ModuleNotFoundError: flask`:** Activate the backend virtual environment and install `requirements.txt`.
- **Frontend says it cannot reach the server:** Start Flask on port 5000 and verify `http://127.0.0.1:5000/api/health`.
- **Port already in use:** Stop the other process using the port or adjust the local configuration consistently.

## GitHub setup

From the project root:

```bash
git init
git add .
git commit -m "Build rule-based AI troubleshooting assistant"
```

Create an empty repository on GitHub, then follow GitHub's instructions to add the remote and push the code.

## Resume-ready description (after you run and test it)

**AI Troubleshooting Assistant | React, Flask, Python, REST API**
- Built a rule-based support chatbot that classifies common network, login, performance, application, and printer issues and returns structured troubleshooting steps.
- Developed and validated REST endpoints with input validation and automated pytest coverage for normal, invalid, and unsupported requests.

Only claim tests passed or deployment completed after you have actually run those steps. The rules and test coverage are a starter; extend them with more scenarios as you learn.
