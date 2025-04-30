from fastapi import HTTPException
from pydantic import BaseModel
import json
from utils import make_ai_api_request, extract_json_from_ai_response

class ScriptRequest(BaseModel):
    concept_subtopic: str
    fandom: str

async def generate_educational_script(request: ScriptRequest):
    """Generate an educational script using a concept and fandom"""
    print(f"Script request received: {request.concept_subtopic} | {request.fandom}")
    
    if not request.concept_subtopic:
        print("Error: Missing concept_subtopic")
        raise HTTPException(status_code=400, detail="Concept Subtopic Parameter is required")
    if not request.fandom:
        print("Error: Missing fandom")
        raise HTTPException(status_code=400, detail="Fandom Parameter is required")
    
    # Check if fandom is valid
    narrators = {
        "Harry Potter": {"name": "Hermione", "id": 120},
        "Star Wars": {"name": "Hermione", "id": 121},
        "Marvel Avengers": {"name": "Iron Man", "id": 122}
    }
    
    # Default narrator if fandom not found
    narrator = narrators.get(request.fandom, {"name": "Narrator", "id": 120})
    print(f"Using narrator: {narrator}")
    
    # Updated prompt with better formatting to encourage valid JSON responses
    prompt = f"""Create an educational video script that teaches "{request.concept_subtopic}" using characters, settings, and terminology from {request.fandom}.
        Return your response as a valid JSON object with the following structure:
        {{
            "educationalConcept": "{request.concept_subtopic}",
            "conceptDescription": "Brief explanation of the concept in standard terms",
            "chosenFandom": "{request.fandom}",
            "videoTitle": "Catchy title for the video",
            "narrator": "{narrator}",
            "scenes": [
                {{
                    "sceneNumber": 1,
                    "videoQuery": "3-5 simple, searchable keywords for finding video content for scene start",
                    "imageQuery": "3-5 simple, searchable keywords for finding image content for scene end",
                    "narrationScript": "Brief narration that can be spoken in 5 seconds"
                }},
                {{
                    "sceneNumber": 2,
                    "videoQuery": "3-5 simple, searchable keywords for finding video content for scene start",
                    "imageQuery": "3-5 simple, searchable keywords for finding image content for scene end",
                    "narrationScript": "Brief narration that can be spoken in 5 seconds"
                }}
            ]
        }}

        Guidelines:
        narrationScript:
        - Keep narrationScript short enough to be spoken within 5-8 seconds
        - Focus on universally recognizable concepts from the fandom
        - Ensure logical flow across scenes
        - Write the storyline from the narrator's perspective, using their typical speech patterns and personality
    
        videoQuery and imageQuery:
        - Use simple, generic keywords derived from what is being narrated in narrationScript
        - Make sure the keywords matches the context of the narrationScript
        - These keywords will be used to find video and image content from copyright-free sources like Pexels
        - videoQuery should be more focused on the first part of the narrationScript
        - imageQuery should be more focused on the last part of the narrationScript
        - Avoid franchise-specific names that are hard to find (e.g. use 'desert planet' instead of 'Tatooine')
        - When referencing characters, use descriptive terms that can be easily searched (e.g. 'wizard with wand' instead of 'Harry Potter')
        
        Note: Maximum 3 scenes
        """

    system_message = "You are a helpful educational content creator."
    
    try:
        print("Making AI API request for script generation...")
        content = make_ai_api_request(prompt, system_message=system_message)
        
        # Add debugging to see the raw response
        print(f"AI API Response received, length: {len(content)}")
        print(f"AI API Response content (first 200 chars): {content[:200]}...")
        
        try:
            # Try to parse JSON directly first
            print("Attempting to parse JSON directly...")
            script_data = json.loads(content)
            print("Direct JSON parsing succeeded")
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the response
            print("Direct JSON parsing failed, trying extraction...")
            script_data = extract_json_from_ai_response(content)
            print("JSON extraction succeeded")
        
        # Validate the script_data has required fields
        print(f"Script data keys: {script_data.keys() if isinstance(script_data, dict) else 'Not a dict'}")
        
        if not isinstance(script_data, dict) or 'scenes' not in script_data:
            print("Script data is invalid or missing scenes")
            # Create default script data as fallback
            script_data = {
                "educationalConcept": request.concept_subtopic,
                "conceptDescription": f"Understanding {request.concept_subtopic}",
                "chosenFandom": request.fandom,
                "videoTitle": f"{request.fandom} teaches {request.concept_subtopic}",
                "narrator": narrator,
                "scenes": [
                    {
                        "sceneNumber": 1,
                        "videoQuery": "educational video",
                        "imageQuery": "knowledge learning",
                        "narrationScript": f"Welcome to a lesson about {request.concept_subtopic}."
                    },
                    {
                        "sceneNumber": 2,
                        "videoQuery": "studying learning",
                        "imageQuery": "education class",
                        "narrationScript": f"Let's explore the key concepts of {request.concept_subtopic}."
                    }
                ]
            }
        
        print("Returning script data successfully")
        return script_data
        
    except Exception as e:
        print(f"Error in script generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in script generation: {str(e)}") 