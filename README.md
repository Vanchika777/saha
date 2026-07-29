# Saha — Enterprise AI Book Companion ($0 Stack)

Saha is an enterprise-grade AI book assistant built using a 100% free stack: **Python Flask**, **React + TypeScript**, **LangChain**, **Groq (Llama 3.3 70B)**, **ChromaDB**, **MongoDB Atlas (M0)**, and **Cloudflare R2**.

---

## 🌟 Key Features

1. **Book Shelf (Carousel)**: Drag-and-drop PDF upload with automatic title/author extraction, embedded page cover rendering, and API fallback (Open Library / Google Books).
2. **AI Recommendation System**: Analyzes reading preferences (genres, authors, languages) to suggest books from Open Library and Project Gutenberg (with free PDF download links).
3. **RAG Chat Window (Main Highlight)**: Ask questions across uploaded PDFs and recommended books. Powered by Groq `llama-3.3-70b-versatile` with streaming Server-Sent Events (SSE) and citation source attribution.
4. **Guest & Logged-In Auth**: Use instantly as a guest (ephemeral session) or sign in (email/password or Google OAuth) to persist library and chat history.
5. **$0 Enterprise Stack**: Designed to run entirely within free tiers.

---

## 🚀 Quick Start (Local Development)

### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
```
Fill in `.env` with your free API keys (Groq API key from [console.groq.com](https://console.groq.com), MongoDB Atlas URI, etc.).

Run backend:
```bash
python run.py
```
Backend starts on `http://localhost:5000`.

---

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend starts on `http://localhost:5173`.

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (React + TS + Vite)               │
│  Navbar → Library Carousel → Recommendations → Chat  │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS REST + SSE Streaming
┌───────────────────────▼─────────────────────────────────┐
│              BACKEND (Flask + LangChain)                │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Auth API    │  │  Book API    │  │  Chat API     │  │
│  │  (JWT/OAuth) │  │  (upload,    │  │  (RAG stream, │  │
│  └──────────────┘  │   metadata)  │  │   history)    │  │
│                    └──────────────┘  └───────────────┘  │
└──────┬─────────────────┬────────────────────┬───────────┘
       │                 │                    │
┌──────▼──────┐  ┌───────▼──────┐  ┌─────────▼──────────┐
│  MongoDB    │  │  ChromaDB    │  │   Groq LLM API     │
│  Atlas M0   │  │ (vector DB)  │  │ (Llama-3.3 70b)   │
└─────────────┘  └──────────────┘  └────────────────────┘
       │
┌──────▼──────┐
│ Cloudflare  │
│ R2 Storage  │
└─────────────┘
```

---

## 🌐 Deployment ($0 Budget)

- **Frontend**: Deploy `frontend/` on [Vercel](https://vercel.com).
- **Backend**: Deploy `backend/` on [Fly.io](https://fly.io) or Railway using the included `Dockerfile` and `fly.toml`.
- **Database**: Free MongoDB Atlas M0 cluster.
- **Storage**: Free 10GB Cloudflare R2 bucket.
