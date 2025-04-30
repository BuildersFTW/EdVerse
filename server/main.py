import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Import functionality from modules
from utils import validate_api_keys
from subtopics import get_educational_subtopics
from script import ScriptRequest, generate_educational_script
from voiceover import VoiceoverRequest, generate_voiceover, download_audio
from video import VideoRequest, generate_video, download_video

# Initialize FastAPI app
app = FastAPI(title="Educational Subtopics API")

# Add CORS middleware specifically for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:5173",  # Vite dev server (if used)
        "http://127.0.0.1:5173",  # Alternative for Vite
        "*",  # Allow all origins temporarily for debugging
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers in response
)

# Validate API keys on startup
try:
    validate_api_keys()
except Exception as e:
    print(f"WARNING: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Educational Subtopics API. Use /subtopics endpoint with a concept parameter."}

@app.get("/subtopics")
async def subtopics_endpoint(concept: str = Query(..., description="The concept to get educational subtopics for")):
    return await get_educational_subtopics(concept)

@app.post("/script")
async def script_endpoint(request: ScriptRequest):
    return await generate_educational_script(request)

@app.post("/generate_voiceover")
async def voiceover_endpoint(request: VoiceoverRequest):
    return await generate_voiceover(request)

@app.post("/generate_video")
async def video_endpoint(request: VideoRequest):
    return await generate_video(request)


@app.get("/download_video/{filename}")
async def download_video_endpoint(filename: str):
    print(f"Request to download video file: {filename}")
    try:
        response = await download_video(filename)
        print(f"Video file {filename} successfully streamed")
        return response
    except Exception as e:
        print(f"Error streaming video file {filename}: {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
