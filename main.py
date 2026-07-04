import json
import os
from pathlib import Path

from anthropic import Anthropic, APIError, APIStatusError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
# Haiku 4.5 is fast and cheap - plenty for captions/storyboards/replies.
# Swap to "claude-sonnet-5" via the ANTHROPIC_MODEL env var if you want higher quality.
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

app = FastAPI(title="Listing Content Pipeline")
client = Anthropic(api_key=API_KEY) if API_KEY else None


class PropertyDetails(BaseModel):
    address: str
    price: str
    beds: str
    baths: str
    features: str


class ReplyRequest(PropertyDetails):
    comment: str


def require_client() -> Anthropic:
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="Server is missing ANTHROPIC_API_KEY. Set it in the environment and restart.",
        )
    return client


def call_claude(prompt: str, max_tokens: int) -> str:
    c = require_client()
    try:
        response = c.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
    except APIStatusError as e:
        # Bad/missing key, rate limit, etc. - surfaces as a clean 502 instead of a crash.
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {e.message}")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")
    return response.content[0].text.strip()


@app.post("/api/generate-content")
def generate_content(details: PropertyDetails):
    prompt = f"""Property details:
Address: {details.address}
Price: {details.price}
Beds: {details.beds} / Baths: {details.baths}
Features: {details.features}

Return a JSON object only, no markdown fences, no commentary, with exactly this shape:
{{"caption": "2-3 sentence engaging Instagram listing caption", "storyboard": ["scene 1", "scene 2", "scene 3", "scene 4"], "hashtags": ["word", "word2"]}}
Storyboard entries are short shot descriptions, in order, for a 20-30 second walkthrough reel. Hashtags have no # symbol."""

    text = call_claude(prompt, max_tokens=800)
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Model did not return valid JSON. Try again.")


@app.post("/api/generate-reply")
def generate_reply(req: ReplyRequest):
    prompt = f"""You are replying, on behalf of the listing agent, to a comment on the social post for this property:
{req.address}, {req.price}, {req.beds} bed / {req.baths} bath. {req.features}

Incoming comment: "{req.comment}"

Write a brief, warm, professional reply (1-2 sentences) a prospective buyer would find helpful. Respond with the reply text only, nothing else."""

    return {"reply": call_claude(prompt, max_tokens=200)}


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")
