import os
import re
import json
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env")
API_KEY = os.getenv("API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def validate_api_keys():
    """Validate that necessary API keys are available"""
    if not API_KEY:
        raise Exception("API_KEY environment variable not set")
    if not ELEVEN_API_KEY:
        raise Exception("ELEVEN_API_KEY environment variable not set")
    if not PEXELS_API_KEY:
        raise Exception("PEXELS_API_KEY environment variable not set")

def extract_json_from_ai_response(content):
    """Extract valid JSON from AI API response"""
    try:
        # Look for JSON content between triple backticks if present
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)

        # Remove any leading/trailing whitespace
        content = content.strip()

        # Parse the JSON content
        return json.loads(content)
    except json.JSONDecodeError:
        # If first attempt fails, try to extract just the JSON portion
        try:
            # Look for content between curly braces
            json_match = re.search(r'({[\s\S]*})', content)
            if json_match:
                content = json_match.group(1)
                return json.loads(content)
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Couldn't extract valid JSON from response. Raw content: {content[:200]}..."
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract JSON: {str(e)}. Raw content: {content[:200]}..."
            )

def make_ai_api_request(prompt, system_message=None, model="gpt-4o-mini", max_tokens=4096):
    """Make a request to AI API with proper error handling"""
    url = "https://api.aimlapi.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        response_data = response.json()
        
        # Extract the content from the response
        if "choices" in response_data and len(response_data["choices"]) > 0:
            return response_data["choices"][0]["message"]["content"]
        else:
            raise HTTPException(status_code=500, detail="Unexpected response format from AI API")
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with AI API: {str(e)}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing AI response: {str(e)}") 