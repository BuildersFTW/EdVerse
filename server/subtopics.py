from fastapi import HTTPException
import json
from utils import make_ai_api_request, extract_json_from_ai_response

async def get_educational_subtopics(concept: str):
    """Generate educational subtopics for a given concept"""
    if not concept:
        raise HTTPException(status_code=400, detail="Concept Parameter is required")

    prompt = f"""I need you to analyze the educational concept I provide and identify exactly 3 key subtopics that are most important for understanding it. Please format your response as valid JSON with this structure:

    {{"subtopics": [{{"title": "First subtopic title"}}, {{"title": "Second subtopic title"}}, {{"title": "Third subtopic title"}}]}}

    No introduction or explanation needed, just return the JSON. The educational concept is: {concept}"""

    try:
        # Get the AI response
        content = make_ai_api_request(prompt)
        
        # Try to parse JSON directly first
        try:
            subtopics = json.loads(content)
            return subtopics
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the response
            try:
                subtopics = extract_json_from_ai_response(content)
                return subtopics
            except Exception as e:
                # If all parsing fails, create a default response
                print(f"Error parsing JSON response: {str(e)}, content: {content[:200]}...")
                # Fall back to generating subtopics manually
                formatted_concept = concept.title()
                return {
                    "subtopics": [
                        {"title": f"Introduction to {formatted_concept}"},
                        {"title": f"Key Components of {formatted_concept}"},
                        {"title": f"Applications of {formatted_concept}"}
                    ]
                }
    except Exception as e:
        print(f"Error in get_educational_subtopics: {str(e)}")
        # Fall back to generating subtopics manually as a last resort
        formatted_concept = concept.title()
        return {
            "subtopics": [
                {"title": f"Introduction to {formatted_concept}"},
                {"title": f"Key Components of {formatted_concept}"},
                {"title": f"Applications of {formatted_concept}"}
            ]
        } 