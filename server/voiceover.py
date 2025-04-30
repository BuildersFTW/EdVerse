import os
import io
import tempfile
import requests
import time
from fastapi import HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
from pydub import AudioSegment
from datetime import datetime

# Create audio directory if it doesn't exist
AUDIO_DIR = "generated_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def make_api_request(url, headers, payload, max_retries=3):
    """Make API request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 401 and attempt < max_retries - 1:
                print(f"API key error, retrying in 2 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
                continue
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error communicating with Eleven Labs API after {max_retries} attempts: {str(e)}"
                )
            print(f"Request failed, retrying in 2 seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(2)

class VoiceoverRequest(BaseModel):
    script: dict
    voice_id: str = None  # Make voice_id optional, will be determined based on fandom

async def generate_voiceover(request: VoiceoverRequest):
    """Generate voiceovers using Eleven Labs API based on script
    
    Voice selection is automatic based on fandom:
    - Wizarding World: Hermione (nDJIICjR9zfJExIFeSCN)
    - Star Wars: Placeholder voice (XrExE9yKIg1WjnnlVkGX)
    - Marvel: Placeholder voice (bVMeCyTHy58xNoL34h3p)
    - Default: Rachel (21m00Tcm4TlvDq8ikWAM)
    
    Returns a JSON object with the following structure:
    {
      "audio_file": "/path/to/filename.mp3",
      "voiceover_data": {
        "educationalConcept": "...",
        "conceptDescription": "...",
        "chosenFandom": "...",
        "videoTitle": "...",
        "timestamps": [
          {
            "sceneNumber": 1,
            "startTime": 0.0,
            "endTime": 5.0,
            "text": "...",
            "videoPrompt": "..."
          },
          // Additional scenes
        ],
        "totalDuration": 60.0
      }
    }
    """
    if not request.script or "scenes" not in request.script:
        raise HTTPException(status_code=400, detail="Valid script with scenes is required")
    
    ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
    if not ELEVEN_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVEN_API_KEY environment variable not set")
    
    # Get script metadata
    educational_concept = request.script.get("educationalConcept", "")
    concept_description = request.script.get("conceptDescription", "")
    chosen_fandom = request.script.get("chosenFandom", "").lower()
    video_title = request.script.get("videoTitle", "")
    
    # Select voice based on fandom
    voice_id = request.voice_id
    if not voice_id:
        # Map fandoms to voice IDs
        fandom_voice_map = {
            "harry potter": "nDJIICjR9zfJExIFeSCN",  # Hermione
            "star wars": "zYcjlYFOd3taleS0gkk3",        # Darth Vader
            "marvel avengers": "jB108zg64sTcu1kCbN9L"    # Iron Man
        }
        
        # Default voice (Rachel) if no mapping found
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        
        # Check if any fandom keywords match
        for fandom_key, fandom_voice_id in fandom_voice_map.items():
            if fandom_key.lower() in chosen_fandom:
                voice_id = fandom_voice_id
                break
    
    scenes = request.script["scenes"]
    
    # Initialize audio segments and timestamps
    combined_audio = AudioSegment.empty()
    timestamps = []
    current_position = 0  # Position in milliseconds
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"voiceover_{timestamp}.mp3"
    output_path = os.path.join(AUDIO_DIR, output_filename)
    
    # Log selected voice and verify API key
    print(f"Using voice ID: {voice_id} for fandom: {chosen_fandom}")
    print(f"API Key length: {len(ELEVEN_API_KEY)} characters")
    
    for scene in scenes:
        if "narrationScript" not in scene:
            continue
            
        narration_text = scene["narrationScript"]
        scene_number = scene.get("sceneNumber", 0)
        video_prompt = scene.get("videoPrompt", "")
        
        print(f"Generating voiceover for scene {scene_number} with text: {narration_text}")
        
        # Call Eleven Labs API to generate voice
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_API_KEY
        }
        
        payload = {
            "text": narration_text,
            "model_id": "eleven_flash_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            response = make_api_request(url, headers, payload)
            print(f"API Response Status: {response.status_code}")
            print(f"Response Content Type: {response.headers.get('content-type')}")
            print(f"Response Length: {len(response.content)} bytes")
            
            # Check if we got audio data
            if not response.content:
                raise HTTPException(
                    status_code=500,
                    detail="Empty response received from Eleven Labs API"
                )
            
            # Save the audio data to a file
            with open(output_path, 'wb') as audio_file:
                audio_file.write(response.content)
            
            try:
                # Load the audio file
                audio_segment = AudioSegment.from_file(output_path, format="mp3")
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process audio data: {str(e)}"
                )
            
            # Add to timestamp data
            start_time = current_position / 1000.0  # Convert to seconds
            
            # Calculate the duration of current audio segment in seconds
            
            # Ensure minimum segment duration of 5 seconds
            if len(audio_segment) < 4500:  # If less than 4.5 seconds
                # Calculate silence needed to reach minimum 4.5 seconds + 0.5s pause
                silence_duration_ms = 4500 - len(audio_segment) + 500
                silence = AudioSegment.silent(duration=silence_duration_ms)
                
                # Add silence to the audio segment
                audio_segment += silence
                # Update position for next audio
                current_position += len(audio_segment)
            else:
                # Add a consistent pause after each line (0.5 seconds)
                pause = AudioSegment.silent(duration=500)
                audio_segment += pause
                current_position += len(audio_segment)
            
            # Calculate end time after adjustments
            end_time = current_position / 1000.0
            
            # Add to combined audio
            combined_audio += audio_segment
            
            # Store timestamp data including video and image queries
            timestamps.append({
                "sceneNumber": scene_number,
                "startTime": start_time,
                "endTime": end_time,
                "text": narration_text,
                "videoPrompt": video_prompt,
                "videoQuery": scene.get("videoQuery", ""),
                "imageQuery": scene.get("imageQuery", "")
            })
            
            time.sleep(0.1)
            
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )
    
    # Export combined audio to the final file
    combined_audio.export(output_path, format="mp3")
    
    # Return both the audio file and timestamps
    response_data = {
        "educationalConcept": educational_concept,
        "conceptDescription": concept_description,
        "chosenFandom": chosen_fandom,
        "videoTitle": video_title,
        "timestamps": timestamps,
        "totalDuration": current_position / 1000.0,  # Total duration in seconds
        "audio_path": output_path,  # Full path to the audio file
        "audio_filename": output_filename  # Just the filename
    }
    
    return {
        "audio_file": output_path,  # Return the full path to the audio file
        "voiceover_data": response_data
    }

async def download_audio(filename):
    """Download an audio file from the generated_audio directory"""
    file_path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Audio file {filename} not found")
    return FileResponse(file_path, media_type="audio/mpeg", filename=filename) 