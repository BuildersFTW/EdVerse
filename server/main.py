import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse



# Import functionality from modules
from utils import validate_api_keys
from subtopics import get_educational_subtopics
from script import ScriptRequest, generate_educational_script
from voiceover import VoiceoverRequest, generate_voiceover, download_audio
from video import VideoRequest, generate_video, download_video

# Initialize FastAPI app
app = FastAPI(title="Educational Subtopics API")

# Allow only the specified origin
origins = [
    "https://edverse-mu.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # specific allowed origin
    allow_credentials=True,
    allow_methods=["*"],  # Explicitly include OPTIONS for preflight
    allow_headers=["*"],
)

# Add custom middleware to ensure CORS headers are included in error responses
@app.middleware("http")
async def add_cors_headers(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        # Ensure CORS headers are included even in exception responses
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
            headers={
                "Access-Control-Allow-Origin": "https://edverse-mu.vercel.app",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            }
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
    response = await generate_video(request)
    if isinstance(response, dict):
        return JSONResponse(
            content=response,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            }
        )
    return response


@app.get("/download_video/{filename}")
async def download_video_endpoint(filename: str):
    print(f"Request to download video file: {filename}")
    try:
        # Get the response from the download_video function
        response = await download_video(filename)
        
        # Ensure CORS headers are added
        # These should be handled by the CORS middleware, but we'll add them explicitly as well
        # to ensure they're present in the FileResponse
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
        print(f"Video file {filename} successfully streamed")
        return response
    except Exception as e:
        print(f"Error streaming video file {filename}: {str(e)}")
        # Return a properly formatted error response
        return JSONResponse(
            status_code=500,
            content={"error": f"Error streaming video: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
