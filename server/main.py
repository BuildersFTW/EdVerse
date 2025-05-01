import os
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware



# Import functionality from modules
from utils import validate_api_keys
from subtopics import get_educational_subtopics
from script import ScriptRequest, generate_educational_script
from voiceover import VoiceoverRequest, generate_voiceover, download_audio
from video import VideoRequest, generate_video, download_video

# Initialize FastAPI app
app = FastAPI(title="Educational Subtopics API")

# Define a custom middleware to ensure CORS headers are present on every response
class CORSHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Process the request and get the response
        response = await call_next(request)
        
        # Add CORS headers to every response
        response.headers["Access-Control-Allow-Origin"] = "https://edverse-mu.vercel.app"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        
        return response

# Add our custom CORS middleware first
app.add_middleware(CORSHeaderMiddleware)

# Handle OPTIONS requests (preflight requests)
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "https://edverse-mu.vercel.app"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response

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
    try:
        response = await generate_video(request)
        
        # Convert any response to a JSONResponse
        if not isinstance(response, dict):
            response = {"result": "success", "data": str(response)}
            
        return JSONResponse(content=response)
    except Exception as e:
        print(f"Error in generate_video: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/download_video/{filename}")
async def download_video_endpoint(filename: str):
    print(f"Request to download video file: {filename}")
    try:
        # Get the response from the download_video function
        response = await download_video(filename)
        print(f"Video file {filename} successfully streamed")
        return response
    except Exception as e:
        print(f"Error streaming video file {filename}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error streaming video: {str(e)}"}
        )

# Handle all exceptions globally
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)