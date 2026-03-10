# 🎬 AI-Powered Personalized Movie & TV Recommender

![Hero Image](https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1000&auto=format&fit=crop) *(Placeholder, replace with actual app screenshot!)*

A full-stack, comprehensive movie and television recommendation engine that combines the vast database of **TMDB**, the raw intelligence of **Local AI (Ollama/Gemma3)**, and seamless **Supabase** cloud synchronization to build the ultimate personalized streaming companion.

Tired of scrolling endlessly through multiple OTT platforms? This app learns what you like, filters explicitly by the streaming platforms you actually subscribe to, and drops you precisely on the generic search page of your favorite streaming service to watch it instantly.

---

## ✨ Core Features

### 🧠 Intelligent AI Discovery
*   **Conversational Recommendations**: Ask the built-in AI assistant for highly specific queries ("Give me a gritty 90s detective movie" or "Shows similar to Breaking Bad but shorter").
*   **Personalized Taste Matrix**: Every time you like, dislike, watch, or watchlist a movie, the AI analyzes your taste across genres, actors, directors, and languages to generate incredibly accurate, custom-tailored recommendations.

### 📺 Smart Streaming Filter & "Watch Now" Routing
*   **Subscribed Platforms Only**: Tell the app what services you pay for (Netflix, Amazon Prime, Hotstar, JioCinema, SonyLIV, Zee5, etc.). It will dynamically filter all movie/TV search results to *only* show content you can actually watch.
*   **1-Click Watch Now**: Found a movie? Click the teal **Watch Now** button. The app intelligently constructs a deep link based on the content available and drops you directly onto the streaming platform's search page, saving you the hassle of manual typing!

### 🌍 Global Search & Rich Metadata
*   **Lightning Fast Search**: Find any movie or TV show globally in an instant.
*   **Extensive Details**: View rich metadata straight from TMDB, including cast, crew, synopsis, high-quality backdrops, user ratings, runtime, release date, and similar content.
*   **Integrated Trailers**: Watch YouTube trailers and teasers directly inside the responsive details modal without ever leaving the app.

### ☁️ Cloud Synced Profiles via Supabase
*   **Google Auth Integration**: Log in securely in one click via your Google account using Supabase OAuth.
*   **Persistent Libraries**: Your Watchlist, History, Likes, Dislikes, and OTT Subscriptions are preserved beautifully in a Supabase PostgreSQL database and synced instantly across all your devices. 
*   **Frictionless Fallback**: Not ready for the cloud? The app seamlessly falls back to local storage and JSON files if Supabase isn't configured, so your development never stops.

---

## 🛠️ Technology Stack

### Frontend (React + Vite)
*   **React 18** for a snappy, component-based UI.
*   **Tailwind CSS** for sleek, responsive, modern, dark-mode styling.
*   **Lucide React** for beautiful, consistent iconography.
*   **Supabase JS Client** for authentication and session management.

### Backend (FastAPI + Python)
*   **FastAPI** for lightning-fast, asynchronous API endpoints.
*   **TMDB API Integration** for fetching real-time global media data.
*   **Ollama (Llama3.1 / Gemma3)** integration for running private, uncensored local AI inference for generating recommendations.
*   **Supabase Python Client** for real-time Postgres database interactions.
*   **Python `asyncio` & `httpx`** for highly concurrent, non-blocking network calls.

---

## 🚀 Getting Started

### 1. Prerequisites
*   [Node.js](https://nodejs.org/) (v16+)
*   [Python](https://www.python.org/) (3.9+)
*   [Ollama](https://ollama.ai/) (Running locally for AI features)
*   A [TMDB API Key](https://developer.themoviedb.org/docs/getting-started)
*   *(Optional)* A [Supabase](https://supabase.com/) Account for Cloud Sync & Auth

### 2. Backend Setup
```bash
cd movie-recommender-backend

# Create virtual environment
python -m venv venv
# Windows: venv\\Scripts\\activate | Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file locally 
# Add your TMDB_API_KEY, SUPABASE_URL, and SUPABASE_KEY to the .env file

# Run the backend
python run.py
```
*The backend runs on `http://localhost:8000`*

### 3. Frontend Setup
```bash
cd movie-recommender-frontend

# Install dependencies
npm install

# Create a .env file locally
# Add your VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to the .env file

# Run the frontend
npm run dev
```
*The frontend runs on `http://localhost:5173`*

---

## 📱 Screenshots
*(Add your beautiful screenshots of the Home Page, the Details Modal with the Watch Now button, the Profile page with the Platform Selectors, and the AI Chat feature!)*

---

## 📄 License
This project is open-source and ready for you to expand! 
