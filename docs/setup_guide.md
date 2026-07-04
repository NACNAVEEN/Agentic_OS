# AgenticOS — Setup & Deployment Guide

## Prerequisites
- **Python** 3.11+
- **Node.js** 18+
- **Groq API Key** (free) from [console.groq.com](https://console.groq.com)

## Quick Start

### 1. Clone & Setup Backend
```bash
git clone https://github.com/your-username/AgenticOS.git
cd AgenticOS/backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cd ..
copy .env.example .env
# Edit .env: GROQ_API_KEY=gsk_your_key_here
```

### 3. Start Backend
```bash
cd backend
python main.py
# Runs at http://localhost:8000
```

### 4. Start Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### 5. Open http://localhost:5173 in your browser

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | (required) | Groq Cloud API key |
| `DEFAULT_MODEL` | `llama-3.3-70b-versatile` | LLM model |
| `HOST` | `0.0.0.0` | Backend host |
| `PORT` | `8000` | Backend port |

## Troubleshooting
- **WebSocket disconnected**: Ensure backend runs on port 8000
- **GROQ_API_KEY missing**: Create `.env` with your key
- **Module not found**: Activate venv, re-run pip install
