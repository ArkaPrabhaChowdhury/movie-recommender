# Deployment Guide (Vercel)

This project is configured for easy deployment on [Vercel](https://vercel.com).

## Prerequisites

1.  **GitHub Account**: Push this code to a GitHub repository.
2.  **Vercel Account**: Sign up at vercel.com.

## Deployment Steps

1.  **Push to GitHub**:
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    # Add your remote origin
    # git remote add origin https://github.com/yourusername/your-repo.git
    git push -u origin main
    ```

2.  **Import to Vercel**:
    *   Go to your Vercel Dashboard.
    *   Click **"Add New..."** -> **"Project"**.
    *   Import your GitHub repository.

3.  **Configure Project**:
    *   **Framework Preset**: Vercel should automatically detect `Vite` for the frontend.
    *   **Root Directory**: Leave as `./` (root).
    *   **Build Command**: `cd movie-recommender-frontend && npm install && npm run build` (You might need to override this if Vercel doesn't auto-detect the subfolder correctly, but usually it's smarter to just set the "Root Directory" to `movie-recommender-frontend` if you ONLY wanted frontend. Since we want BOTH, keep Root Directory as `./`).
    *   **Wait!** Vercel's default behavior for monorepos can be tricky.
    
    **Recommended Settings for this Monorepo:**
    *   **Framework Preset**: Vite
    *   **Root Directory**: `movie-recommender-frontend` (This tells Vercel where the frontend code lives).
    *   **BUT**, we also need the backend.
    
    **Actually, the best way for this specific setup (Frontend + Python Backend in one repo):**
    1.  Leave **Root Directory** as `./` (empty).
    2.  **Build Command**: `cd movie-recommender-frontend && npm install && npm run build`
    3.  **Output Directory**: `movie-recommender-frontend/dist`
    4.  **Install Command**: `cd movie-recommender-frontend && npm install`

    *Note: The Python backend dependencies are installed automatically because `requirements.txt` is in the root.*

4.  **Environment Variables**:
    Add the following environment variables in the Vercel Project Settings:
    *   `TMDB_API_KEY`: Your TMDB API Key.
    *   `OLLAMA_API_URL`: **IMPORTANT** - This defaults to `http://localhost:11434`. This **WILL NOT WORK** on Vercel because Vercel cannot access your local computer.
        *   *Solution*: You need a hosted LLM API (like OpenAI) or a public Ollama instance.
        *   If you don't have one, the AI Chat features will fail, but the rest of the site (Discovery, Search) will work fine.

## Troubleshooting

*   **404 on API calls**: Check the `vercel.json` rewrites. It maps `/api/*` to the Python backend.
*   **AI Chat Error**: As mentioned, local Ollama won't work. You'll see connection errors in the logs.
