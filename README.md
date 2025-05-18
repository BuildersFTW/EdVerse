# EdVerse

EdVerse is an educational content generation platform that automatically creates educational videos on various topics. The application uses AI to generate educational content including subtopics, scripts, voiceovers, and finally produces complete educational videos.

🚀 This project was built during the [/execute Genesis AI Hackathon](https://lablab.ai/event/execute-ai-genesis) by lablab.ai in May, 2025.

## Project Structure

The project consists of two main parts:

- **Client**: A React-based frontend built with Vite
- **Server**: A FastAPI backend that handles content generation

## Features

- Generate educational subtopics for any concept
- Create educational scripts with AI assistance
- Generate voiceovers for educational content
- Produce complete educational videos
- Download generated audio and video files

## Technology Stack

### Frontend
- React 19
- Vite 6
- Modern ES modules

### Backend
- FastAPI
- Python 3
- MoviePy for video generation
- OpenCV for image processing
- Various AI services for content generation

## Getting Started

### Prerequisites
- Node.js (latest LTS version)
- Python 3.8+
- pip (Python package manager)

### Server Setup
1. Navigate to the server directory:
   ```
   cd server
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the server:
   ```
   python main.py
   ```
   The server will start at http://localhost:8000

### Client Setup
1. Navigate to the client directory:
   ```
   cd client
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```
   The client will be available at http://localhost:5173

## API Endpoints

- GET `/subtopics?concept={concept}` - Get educational subtopics for a concept
- POST `/script` - Generate an educational script
- POST `/generate_voiceover` - Generate a voiceover from a script
- POST `/generate_video` - Generate a video from a script and voiceover
- GET `/download_audio/{filename}` - Download a generated audio file
- GET `/download_video/{filename}` - Download a generated video file

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
