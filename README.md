# Listing content pipeline

A FastAPI service that generates real-estate listing captions, reel storyboards,
and autonomous comment replies using your own Anthropic API key. No claude.ai
involved anywhere in the running app — this is entirely yours to host, brand,
and demo.

## 1. Get an API key

1. Go to https://console.anthropic.com and sign up (separate from your claude.ai
   account — this is the developer/billing console).
2. Create an API key under **API Keys**.
3. Add a small amount of credit. Haiku 4.5 is cheap: generating one full
   content package (caption + storyboard + hashtags) costs a small fraction of
   a cent, so testing this thoroughly will cost you well under a dollar.

## 2. Run it locally

```bash
cd real-estate-bot
python3 -m venv venv
source venv/bin/activate        
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your real ANTHROPIC_API_KEY

uvicorn main:app --reload
```

Open http://localhost:8000 — same interface and behavior as the demo you saw
in Claude, just running on your own machine with your own key.

## 3. Deploy it so you can send a real link

**Render.com is the simplest option for a FastAPI app** (Vercel and Netlify are
built around static sites and JS serverless functions — they can run Python,
but Render's "Web Service" flow is a more direct fit for a long-running FastAPI
app and has a genuinely free tier):

1. Push this folder to a new GitHub repo.
2. Go to https://render.com → **New → Web Service** → connect the repo.
3. Render will detect the `Dockerfile` automatically and build from it. If it
   doesn't, set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment**, add `ANTHROPIC_API_KEY` with your real key (and
   optionally `ANTHROPIC_MODEL` if you want to override the default).
5. Deploy. Render gives you a URL like `your-app.onrender.com` — that's what
   you send the client. No claude.ai branding, no login wall, works for
   anyone who opens the link.

Railway.app and Fly.io work the same way if you'd rather use those — both
accept the included `Dockerfile` as-is.

## 4. Swapping in real photo/video generation later

The `/api/generate-content` endpoint already returns a `storyboard` array —
that's the input you'd feed to an image-generation API (e.g. Flux via
Replicate, or DALL·E) for photos, and a templated video tool (e.g. Creatomate)
for the walkthrough reel. Wiring those in is a matter of adding two more calls
inside `generate_content()` and returning the resulting URLs alongside the
text — happy to help scope that once you've confirmed with the client which
platform(s) and comment behavior they actually want.

## Cost note

Every click of "Generate content" or "Generate reply" is a real, billed API
call against your key. Fine for demos and normal client usage, but don't wire
this up to run unattended at high volume without a usage cap or you could see
an unexpected bill.
