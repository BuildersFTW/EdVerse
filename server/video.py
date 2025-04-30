import os
import requests
import tempfile
import subprocess
import time
import json
import random
import traceback  # Add this for detailed error tracing
import logging  # Add logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='video_generator.log')
logger = logging.getLogger("video_generator")

# Create directories if they don't exist
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
VIDEO_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "generated_videos"))
MEDIA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "media_assets"))
MUSIC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "bg_music"))  # Path to background music

# Ensure all directories exist
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, "videos"), exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, "images"), exist_ok=True)

# Check if MUSIC_DIR exists
if not os.path.exists(MUSIC_DIR):
    logger.warning(f"Music directory not found: {MUSIC_DIR}. Creating it.")
    os.makedirs(MUSIC_DIR, exist_ok=True)
    
    # Create subdirectories if they don't exist
    for subfolder in ["Harry Potter", "Star Wars", "Marvel Avengers"]:
        os.makedirs(os.path.join(MUSIC_DIR, subfolder), exist_ok=True)

class VideoRequest(BaseModel):
    voiceover_data: Dict[str, Any]

def make_pexels_request(url, params=None, max_retries=3):
    """Make Pexels API request with retry logic"""
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    if not PEXELS_API_KEY:
        logger.error("PEXELS_API_KEY environment variable not set")
        raise HTTPException(status_code=500, detail="PEXELS_API_KEY environment variable not set")
    
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 401 and attempt < max_retries - 1:
                logger.warning(f"API key error, retrying in 2 seconds... (Attempt {attempt + 1}/{max_retries})")
                print(f"API key error, retrying in 2 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Pexels API request failed: {str(e)}")
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error communicating with Pexels API after {max_retries} attempts: {str(e)}"
                )
            print(f"Request failed, retrying in 2 seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(2)

def search_pexels_videos(query, per_page=1, orientation="landscape"):
    """Search for videos on Pexels API"""
    url = "https://api.pexels.com/videos/search"
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": orientation,
        "size": "medium"  # medium quality to save bandwidth
    }
    
    result = make_pexels_request(url, params)
    if not result.get("videos"):
        raise HTTPException(status_code=404, detail=f"No videos found for query: {query}")
    
    return result["videos"]

def search_pexels_photos(query, per_page=1, orientation="landscape"):
    """Search for photos on Pexels API"""
    url = "https://api.pexels.com/v1/search"
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": orientation
    }
    
    result = make_pexels_request(url, params)
    if not result.get("photos"):
        raise HTTPException(status_code=404, detail=f"No photos found for query: {query}")
    
    return result["photos"]

def download_media_file(url, media_type, query):
    """Download media file (video or image) from URL"""
    # Create a safe filename from the query
    safe_query = "".join([c if c.isalnum() else "_" for c in query])[:50]
    timestamp = int(time.time())
    
    if media_type == "video":
        extension = ".mp4"
        subfolder = "videos"
    else:  # image
        extension = ".jpg"
        subfolder = "images"
    
    filename = f"{safe_query}_{timestamp}{extension}"
    filepath = os.path.join(MEDIA_DIR, subfolder, filename)
    
    # Download the file
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filepath
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download {media_type} file: {str(e)}"
        )

def apply_image_effects(image_clip, duration):
    """Apply zoom out effect to image clip"""
    # Import here to avoid global import issues
    import cv2
    import numpy as np
    
    # Define a function to manually apply the zoom effect (to avoid ANTIALIAS error)
    def scale_func(get_frame, t):
        # Calculate scale factor (start at 1.2x zoom and end at 1.0x)
        scale_factor = 1.2 - 0.2 * t/duration
        frame = get_frame(t)
        
        # Get frame dimensions
        h, w = frame.shape[:2]
        
        # Create a new frame with same dimensions as the original
        result = np.zeros_like(frame)
        
        # Calculate new dimensions (center crop if larger than original)
        new_h, new_w = int(h * scale_factor), int(w * scale_factor)
        
        # Resize the frame
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # If resized is smaller than original, center it
        if new_h <= h and new_w <= w:
            # Calculate padding to center the resized image
            pad_h = (h - new_h) // 2
            pad_w = (w - new_w) // 2
            
            # Place resized image in the center
            result[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = resized
        else:
            # If resized is larger, take the center portion
            start_h = (new_h - h) // 2
            start_w = (new_w - w) // 2
            
            # Extract the center portion that fits our target size
            center_crop = resized[start_h:start_h+h, start_w:start_w+w]
            result = center_crop
        
        return result
    
    # Apply the custom scaling function
    return image_clip.fl(scale_func)

def standardize_clip_size(clip, width=1920, height=1080):
    """Resize a clip to standard dimensions while maintaining aspect ratio"""
    import cv2
    import numpy as np
    
    def resize_frame(get_frame, t):
        # Get the original frame
        frame = get_frame(t)
        
        # Get original dimensions
        h, w = frame.shape[:2]
        
        # Create a black background of the target size
        result = np.zeros((height, width, 3), dtype=frame.dtype)
        
        # Calculate aspect ratio
        aspect = w / h
        target_aspect = width / height
        
        if aspect > target_aspect:
            # Image is wider than target aspect ratio
            new_w = width
            new_h = int(width / aspect)
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Center vertically
            y_offset = (height - new_h) // 2
            result[y_offset:y_offset+new_h, 0:width] = resized
        else:
            # Image is taller than target aspect ratio
            new_h = height
            new_w = int(height * aspect)
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Center horizontally
            x_offset = (width - new_w) // 2
            result[0:height, x_offset:x_offset+new_w] = resized
            
        return result
    
    # Apply the resize function
    return clip.fl(resize_frame)

def get_random_music_for_fandom(fandom: str) -> str:
    """Get a random background music file path based on fandom"""
    try:
        # Map fandom keywords to directory names
        fandom = fandom.lower() if fandom else ""
        
        if "harry potter" in fandom or "wizarding" in fandom:
            music_folder = "Harry Potter"
        elif "star wars" in fandom:
            music_folder = "Star Wars"
        elif "marvel" in fandom or "avengers" in fandom or "iron man" in fandom:
            music_folder = "Marvel Avengers"
        else:
            # Default to Harry Potter if fandom not recognized
            music_folder = "Harry Potter"
        
        # Get the full path to the music folder
        music_path = os.path.join(MUSIC_DIR, music_folder)
        
        # Check if the folder exists
        if not os.path.exists(music_path):
            logger.warning(f"Music folder not found: {music_path}")
            return None
        
        # Get all mp3 files in the folder
        music_files = [f for f in os.listdir(music_path) if f.endswith('.mp3')]
        
        if not music_files:
            logger.warning(f"No music files found in {music_path}")
            return None
        
        # Select a random file
        random_music = random.choice(music_files)
        logger.info(f"Selected background music: {random_music}")
        
        # Check if the file exists and is readable
        music_file_path = os.path.join(music_path, random_music)
        if not os.path.exists(music_file_path) or not os.access(music_file_path, os.R_OK):
            logger.warning(f"Selected music file is not accessible: {music_file_path}")
            return None
            
        # Return the full path to the music file
        return music_file_path
    except Exception as e:
        logger.error(f"Error selecting background music: {str(e)}")
        return None

async def generate_video(request: VideoRequest):
    """Generate a video based on voiceover data with stock videos and images from Pexels
    
    Returns a JSON object with video file path and information
    """
    try:
        if not request.voiceover_data or "timestamps" not in request.voiceover_data:
            logger.error("Valid voiceover data with timestamps is required")
            raise HTTPException(status_code=400, detail="Valid voiceover data with timestamps is required")
        
        # Log the received data structure
        logger.info(f"Received voiceover data keys: {request.voiceover_data.keys()}")
        
        voiceover_data = request.voiceover_data
        timestamps = voiceover_data["timestamps"]
        audio_path = voiceover_data.get("audio_path")
        
        # Get fandom for background music selection
        fandom = voiceover_data.get("chosenFandom", "")
        
        # Check if audio path exists
        if not audio_path:
            logger.error("Audio path not provided in voiceover data")
            raise HTTPException(status_code=400, detail="Audio path not provided in voiceover data")
            
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found at path: {audio_path}")
            raise HTTPException(status_code=404, detail=f"Audio file not found at path: {audio_path}")
        
        # Generate unique filename for the output video
        timestamp = int(time.time())
        output_filename = f"video_{timestamp}.mp4"
        output_path = os.path.join(VIDEO_DIR, output_filename)
        
        # Check if PEXELS_API_KEY is set
        if not os.getenv("PEXELS_API_KEY"):
            logger.error("PEXELS_API_KEY environment variable not set")
            raise HTTPException(status_code=500, detail="PEXELS_API_KEY environment variable not set")
            
        # Load audio file
        try:
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            logger.info(f"Loaded audio file: {audio_path}, duration: {total_duration}s")
        except Exception as e:
            logger.error(f"Failed to load audio file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load audio file: {str(e)}")
        
        # Sort timestamps by start time to ensure proper sequence
        timestamps = sorted(timestamps, key=lambda x: x.get("startTime", 0))
        
        # Validate if timestamps cover the entire duration
        if timestamps:
            last_timestamp = timestamps[-1]
            last_end_time = last_timestamp.get("endTime", 0)
            
            # If timestamps don't cover the full audio duration, add a final scene
            if last_end_time < total_duration - 0.5:  # If there's more than 0.5 seconds missing
                logger.info(f"Adding additional scene to cover remaining duration from {last_end_time} to {total_duration}")
                print(f"Adding additional scene to cover remaining duration from {last_end_time} to {total_duration}")
                
                # Try to use the last scene's queries as a basis for continuity
                image_query = last_timestamp.get("imageQuery", "nature landscape scenic beautiful")
                video_query = last_timestamp.get("videoQuery", "nature landscape scenic beautiful")
                
                # Add a new timestamp for the final segment
                timestamps.append({
                    "sceneNumber": len(timestamps) + 1,
                    "startTime": last_end_time,
                    "endTime": total_duration,
                    "text": "Educational video by AI Genesis",
                    "videoPrompt": video_query,
                    "imageQuery": image_query
                })
        
        # Prepare list for video clips
        video_clips = []
        
        for scene in timestamps:
            scene_number = scene["sceneNumber"]
            start_time = scene["startTime"]
            end_time = scene["endTime"]
            scene_duration = end_time - start_time
            text = scene["text"]
            
            # Get appropriate prompt from the scene
            video_prompt = scene.get("videoPrompt", "")
            # If videoPrompt is not available, use the keys from test2.py
            if not video_prompt:
                image_query = scene.get("imageQuery", text)
                video_query = scene.get("videoQuery", text)
            else:
                # Use the same prompt for both
                image_query = video_prompt
                video_query = video_prompt
            
            logger.info(f"Generating scene {scene_number} with duration {scene_duration:.2f}s")
            logger.info(f"Image query: {image_query}")
            logger.info(f"Video query: {video_query}")
            
            try:
                # For scenes ≤ 5 seconds: use only stock video
                if scene_duration <= 5.0:
                    logger.info(f"Scene {scene_number} is ≤ 5 seconds, using only video")
                    
                    # Search for stock video
                    videos = search_pexels_videos(video_query)
                    if not videos:
                        logger.error(f"No videos found for scene {scene_number}")
                        raise HTTPException(status_code=404, detail=f"No videos found for scene {scene_number}")
                    
                    # Get the video URL (prefer HD or SD)
                    video_files = videos[0]["video_files"]
                    video_url = None
                    
                    for file in video_files:
                        if file["quality"] == "hd" and file["width"] >= 1280:
                            video_url = file["link"]
                            break
                    
                    # If no HD, get SD
                    if not video_url:
                        for file in video_files:
                            if file["quality"] == "sd" and file["width"] >= 640:
                                video_url = file["link"]
                                break
                    
                    # If still no URL, get any format
                    if not video_url and video_files:
                        video_url = video_files[0]["link"]
                    
                    if not video_url:
                        logger.error(f"No usable video format found for scene {scene_number}")
                        raise HTTPException(status_code=404, detail=f"No usable video format found for scene {scene_number}")
                    
                    # Download and load the video
                    video_path = download_media_file(video_url, "video", video_query)
                    logger.info(f"Downloaded video to: {video_path}")
                    
                    try:
                        video_clip = VideoFileClip(video_path)
                        logger.info(f"Loaded video clip, duration: {video_clip.duration}s")
                    except Exception as e:
                        logger.error(f"Failed to load video clip: {str(e)}")
                        raise HTTPException(status_code=500, detail=f"Failed to load video clip: {str(e)}")
                    
                    # If video is longer than needed, take only the part we need
                    if video_clip.duration > scene_duration:
                        video_clip = video_clip.subclip(0, scene_duration)
                    else:
                        # If video is shorter, loop it to match the needed duration
                        loops_needed = int(scene_duration / video_clip.duration) + 1
                        repeated_clips = [video_clip] * loops_needed
                        video_clip = concatenate_videoclips(repeated_clips, method="compose")
                        video_clip = video_clip.subclip(0, scene_duration)
                    
                    # Set the start time for this segment
                    video_clip = video_clip.set_start(start_time)
                    
                    # Standardize clip size before adding
                    video_clip = standardize_clip_size(video_clip)
                    
                    # Add clip to the list
                    video_clips.append(video_clip)
                    
                else:
                    # For scenes > 5 seconds: use stock video for 4 seconds + stock image for the rest
                    logger.info(f"Scene {scene_number} is > 5 seconds, using video + image")
                    
                    # Search for stock video
                    videos = search_pexels_videos(video_query)
                    if not videos:
                        logger.error(f"No videos found for scene {scene_number}")
                        raise HTTPException(status_code=404, detail=f"No videos found for scene {scene_number}")
                    
                    # Get the video URL
                    video_files = videos[0]["video_files"]
                    video_url = None
                    
                    for file in video_files:
                        if file["quality"] == "hd" and file["width"] >= 1280:
                            video_url = file["link"]
                            break
                    
                    if not video_url:
                        for file in video_files:
                            if file["quality"] == "sd" and file["width"] >= 640:
                                video_url = file["link"]
                                break
                    
                    if not video_url and video_files:
                        video_url = video_files[0]["link"]
                    
                    if not video_url:
                        logger.error(f"No usable video format found for scene {scene_number}")
                        raise HTTPException(status_code=404, detail=f"No usable video format found for scene {scene_number}")
                    
                    # Search for stock image
                    photos = search_pexels_photos(image_query)
                    if not photos:
                        logger.error(f"No images found for scene {scene_number}")
                        raise HTTPException(status_code=404, detail=f"No images found for scene {scene_number}")
                    
                    # Get the image URL
                    image_url = photos[0]["src"]["original"]
                    
                    # Download and load media
                    video_path = download_media_file(video_url, "video", video_query)
                    image_path = download_media_file(image_url, "image", image_query)
                    
                    # First 4 seconds: video
                    video_clip = VideoFileClip(video_path)
                    
                    if video_clip.duration < 4.0:
                        # Loop video to reach 4 seconds
                        loops_needed = int(4.0 / video_clip.duration) + 1
                        repeated_clips = [video_clip] * loops_needed
                        video_clip = concatenate_videoclips(repeated_clips, method="compose")
                    
                    video_clip = video_clip.subclip(0, 4.0)
                    video_clip = video_clip.set_start(start_time)
                    
                    # Rest of the duration: image with zoom effect
                    image_clip = ImageClip(image_path)
                    image_duration = scene_duration - 4.0
                    
                    # Ensure image is shown for at least 2 seconds
                    if image_duration < 2.0:
                        # Reduce video time to ensure image gets at least 2 seconds
                        required_image_time = 2.0
                        
                        # Calculate adjusted video time
                        adjusted_video_time = scene_duration - required_image_time
                        
                        # Ensure video still has some minimal time (at least 1 second)
                        if adjusted_video_time < 1.0:
                            # If scene is too short, rebalance
                            adjusted_video_time = max(1.0, scene_duration * 0.4)  # 40% to video
                            required_image_time = scene_duration - adjusted_video_time  # 60% to image
                        
                        logger.info(f"Scene {scene_number}: Adjusted video time from 4.0s to {adjusted_video_time:.2f}s to give image at least {required_image_time:.2f}s")
                        
                        # Update video duration
                        video_clip = video_clip.subclip(0, adjusted_video_time)
                        video_clip = video_clip.set_duration(adjusted_video_time)
                        
                        # Update image duration and start time
                        image_duration = required_image_time
                        image_start = start_time + adjusted_video_time
                    else:
                        # Standard case, video is 4s and image gets the rest
                        image_start = start_time + 4.0
                    
                    # Apply zoom out effect
                    image_clip = apply_image_effects(image_clip, image_duration)
                    
                    # Set duration and start time
                    image_clip = image_clip.set_duration(image_duration)
                    image_clip = image_clip.set_start(image_start)
                    
                    # Standardize clip sizes before adding
                    video_clip = standardize_clip_size(video_clip)
                    image_clip = standardize_clip_size(image_clip)
                    
                    # Add clips to the list
                    video_clips.append(video_clip)
                    video_clips.append(image_clip)
                    
            except Exception as e:
                logger.error(f"Error processing scene {scene_number}: {str(e)}\n{traceback.format_exc()}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing scene {scene_number}: {str(e)}"
                )
        
        try:
            # Combine all video clips
            final_video = CompositeVideoClip(video_clips, size=(1920, 1080))
            
            # Verify that all time ranges are covered
            covered_times = []
            for clip in video_clips:
                covered_times.append((clip.start, clip.start + clip.duration))
            
            # Sort by start time
            covered_times.sort(key=lambda x: x[0])
            
            # Check for gaps and log them
            for i in range(len(covered_times) - 1):
                current_end = covered_times[i][1]
                next_start = covered_times[i+1][0]
                if next_start - current_end > 0.1:  # Gap larger than 0.1s
                    logger.warning(f"Warning: Gap detected between {current_end:.2f}s and {next_start:.2f}s")
            
            # Ensure the video starts at 0 and covers until the end
            if covered_times[0][0] > 0.1:
                logger.warning(f"Warning: Video doesn't start at 0 but at {covered_times[0][0]:.2f}s")
            if covered_times[-1][1] < total_duration - 0.1:
                logger.warning(f"Warning: Video ends at {covered_times[-1][1]:.2f}s but audio is {total_duration:.2f}s")
            
            # Print the combined duration of clips versus total duration
            total_clip_duration = sum(clip.duration for clip in video_clips)
            logger.info(f"Total clip durations: {total_clip_duration:.2f}s, Audio duration: {total_duration:.2f}s")
            
            # Add audio with background music
            try:
                audio_clip = AudioFileClip(audio_path)
                total_duration = audio_clip.duration
                
                # Get background music based on fandom
                bg_music_path = get_random_music_for_fandom(fandom)
                
                if bg_music_path and os.path.exists(bg_music_path):
                    try:
                        # Load the background music
                        bg_music = AudioFileClip(bg_music_path)
                        
                        # Loop the music if it's shorter than the video
                        if bg_music.duration < total_duration:
                            # Calculate how many loops we need
                            loops_needed = int(total_duration / bg_music.duration) + 1
                            # Create a list of music clips to concatenate
                            music_clips = [bg_music] * loops_needed
                            # Concatenate the clips
                            bg_music = concatenate_videoclips(music_clips)
                        
                        # Trim the music to match video duration
                        bg_music = bg_music.subclip(0, total_duration)
                        
                        # Lower the volume of the background music (25% of original)
                        bg_music = bg_music.volumex(0.25)
                        
                        # Mix the voiceover and background music
                        final_audio = audio_clip.audio_fadein(1).audio_fadeout(1)
                        final_audio = final_audio.audio_fadeout(2)
                        mixed_audio = CompositeVideoClip([final_audio, bg_music])
                        
                        # Apply the mixed audio to the video
                        final_video = final_video.set_audio(mixed_audio)
                        logger.info(f"Added background music from {bg_music_path}")
                    except Exception as e:
                        logger.error(f"Error adding background music: {str(e)}")
                        logger.info("Falling back to voiceover only")
                        # Fallback to just the voiceover audio if music fails
                        final_video = final_video.set_audio(audio_clip)
                else:
                    # Use just the voiceover audio if no music available
                    logger.info("No background music available, using voiceover only")
                    final_video = final_video.set_audio(audio_clip)
                
                # Set video duration to match audio exactly
                final_video = final_video.set_duration(total_duration)
            except Exception as e:
                logger.error(f"Error setting audio for video: {str(e)}")
                # Continue without audio if there's an audio error
                logger.warning("Continuing with video without audio due to error")
                # Still set a reasonable duration
                if hasattr(final_video, 'duration') and final_video.duration > 0:
                    pass  # Keep existing duration
                else:
                    # Set a default duration if none is available
                    final_video = final_video.set_duration(60)  # Default 60 seconds
            
            # Write video file
            temp_output_path = f"{output_path}.temp"
            logger.info(f"Writing video to temporary file: {temp_output_path}")
            
            try:
                # Create a simple test file to verify write permissions
                with open(temp_output_path, 'wb') as test_file:
                    test_file.write(b'test')
                
                # If test successful, remove the test file
                os.remove(temp_output_path)
                logger.info("Write permission test successful")
                
                # Process video with safer settings
                final_video.write_videofile(
                    temp_output_path,
                    codec="libx264",
                    audio_codec="aac",
                    fps=30,
                    threads=2,  # Reduced thread count for better stability
                    preset="ultrafast",  # Faster encoding for reliability
                    logger=None,  # Use our own logging
                    verbose=False
                )
                
                # When write is complete, rename to final path for immediate availability
                if os.path.exists(temp_output_path) and os.path.getsize(temp_output_path) > 0:
                    logger.info(f"Video file successfully written to: {temp_output_path}, size: {os.path.getsize(temp_output_path)}")
                    
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(temp_output_path, output_path)
                    logger.info(f"Video file renamed from {temp_output_path} to {output_path}")
                else:
                    logger.error(f"Video file was not written correctly: {temp_output_path}")
                    raise Exception("Video file was not written correctly or has zero size")
                    
            except Exception as e:
                logger.error(f"Error writing video file: {str(e)}\n{traceback.format_exc()}")
                # Try a simpler fallback method if the first attempt failed
                try:
                    logger.info("Attempting fallback video writing method...")
                    # Try writing directly to the final path with simpler settings
                    final_video.write_videofile(
                        output_path,
                        codec="libx264",
                        audio_codec="aac",
                        fps=24,
                        threads=1,
                        preset="ultrafast",
                        verbose=False,
                        logger=None
                    )
                    logger.info(f"Fallback video writing successful to: {output_path}")
                except Exception as e2:
                    logger.error(f"Fallback video writing also failed: {str(e2)}\n{traceback.format_exc()}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to write video file: {str(e2)}"
                    )
            
            # Clean up
            final_video.close()
            audio_clip.close()
            for clip in video_clips:
                clip.close()
            
            # Return video information
            response_data = {
                "video_file": output_path,
                "video_filename": output_filename,
                "duration": total_duration,
                "scenes_count": len(timestamps),
                "video_title": voiceover_data.get("videoTitle", ""),
                "fandom": voiceover_data.get("chosenFandom", ""),
                "concept": voiceover_data.get("educationalConcept", "")
            }
            
            return {
                "video_path": output_path,
                "video_data": response_data
            }
            
        except Exception as e:
            logger.error(f"Error generating final video: {str(e)}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating final video: {str(e)}"
            )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Log the full error with traceback for unexpected exceptions
        logger.error(f"Unexpected error in generate_video: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error in video generation: {str(e)}"
        )

async def download_video(filename):
    """Download a video file from the generated_videos directory"""
    file_path = os.path.join(VIDEO_DIR, filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        # Log the error
        logger.error(f"Video file not found: {file_path}")
        # Also check if the file is still being written
        temp_file_path = f"{file_path}.temp"
        if os.path.exists(temp_file_path):
            logger.info(f"Video is still being generated: {filename}")
            raise HTTPException(status_code=202, 
                detail="Video is still being generated. Please try again in a few seconds.")
        raise HTTPException(status_code=404, detail=f"Video file {filename} not found")
    
    # Ensure file is readable and complete
    try:
        # Check if file is accessible and get its size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.warning(f"Video file exists but has zero size: {filename}")
            raise HTTPException(status_code=204, 
                detail="Video file exists but is empty. It may still be processing.")
        
        # Set appropriate headers for video streaming
        headers = {
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
        }
        
        # Return the file with video streaming support
        logger.info(f"Serving video file: {filename}, size: {file_size} bytes")
        return FileResponse(
            file_path, 
            media_type="video/mp4", 
            filename=filename,
            headers=headers
        )
    except Exception as e:
        logger.error(f"Error accessing video file {filename}: {str(e)}")
        raise HTTPException(status_code=500, 
            detail=f"Error accessing video file: {str(e)}") 