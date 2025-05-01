// API service for interacting with the backend
const API_BASE_URL = 'edverse-server.ralgo.org';

// Fetch educational subtopics based on a concept
export const fetchSubtopics = async (concept) => {
  try {
    console.log(`Fetching subtopics for: ${concept}`);
    const response = await fetch(`https://${API_BASE_URL}/subtopics?concept=${encodeURIComponent(concept)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      console.error(`API error: ${response.status}`);
      // If API fails, return default subtopics
      throw new Error(`Failed to fetch subtopics: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Received subtopics data:', data);
    
    // Validate the response format
    if (!data || !data.subtopics || !Array.isArray(data.subtopics)) {
      console.error('Invalid response format:', data);
      throw new Error('Invalid response format from API');
    }
    
    // Extract titles and ensure they're all strings
    const subtopics = data.subtopics.map(item => {
      if (typeof item === 'string') return item;
      if (item && typeof item === 'object' && item.title) return item.title;
      return `Subtopic ${Math.floor(Math.random() * 1000)}`; // Fallback
    });
    
    // Make sure we have at least one subtopic
    if (subtopics.length === 0) {
      throw new Error('No subtopics returned');
    }
    
    return subtopics;
  } catch (error) {
    console.error('Error fetching subtopics:', error);
    // Return fallback subtopics
    return [
      `Introduction to ${concept}`,
      `Key components of ${concept}`,
      `Applications of ${concept}`
    ];
  }
};

// Generate a script based on a concept and fandom
export const generateScript = async (conceptSubtopic, fandom) => {
  try {
    console.log(`ApiService: Generating script for subtopic "${conceptSubtopic}" and fandom "${fandom}"`);
    console.log('ApiService: Request payload:', {
      concept_subtopic: conceptSubtopic,
      fandom: fandom
    });
    
    const response = await fetch(`https://${API_BASE_URL}/script`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        concept_subtopic: conceptSubtopic,
        fandom: fandom
      })
    });
    
    console.log(`ApiService: Script generation response status: ${response.status}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`ApiService: Script generation failed with status ${response.status}:`, errorText);
      throw new Error(`Failed to generate script: ${response.status} - ${errorText}`);
    }
    
    const data = await response.json();
    console.log('ApiService: Script generated successfully', { dataKeys: Object.keys(data) });
    return data;
  } catch (error) {
    console.error('ApiService: Error generating script:', error);
    throw error;
  }
};

// Generate voiceover for a script
export const generateVoiceover = async (script) => {
  try {
    const response = await fetch(`https://${API_BASE_URL}/generate_voiceover`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        script: script
      }),
      credentials: 'omit', // Don't send credentials
      mode: 'cors' // Explicitly set CORS mode
    });
    
    if (!response.ok) {
      throw new Error(`Failed to generate voiceover: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error generating voiceover:', error);
    throw error;
  }
};

// Generate video from voiceover data
export const generateVideo = async (voiceoverData) => {
  try {
    console.log('ApiService: Generating video with voiceover data:', {
      dataKeys: Object.keys(voiceoverData),
      hasTimestamps: !!voiceoverData.timestamps,
      timestamps_count: voiceoverData.timestamps?.length
    });

    // Try using a different approach for the fetch request
    const response = await fetch(`https://${API_BASE_URL}/generate_video`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        voiceover_data: voiceoverData
      }),
      credentials: 'omit', // Don't send credentials
      mode: 'cors' // Explicitly set CORS mode
    });
    
    if (!response.ok) {
      let errorText = "";
      try {
        errorText = await response.text();
      } catch (e) {
        errorText = `Status: ${response.status} ${response.statusText}`;
      }
      console.error(`ApiService: Video generation failed with status ${response.status}:`, errorText);
      throw new Error(`Failed to generate video: ${response.status} - ${errorText}`);
    }
    
    const data = await response.json();
    console.log('ApiService: Video generated successfully', data);
    return data;
  } catch (error) {
    console.error('ApiService: Error generating video:', error);

    // Provide more detailed error information for debugging
    if (error.message && error.message.includes('Failed to fetch')) {
      console.error('ApiService: This may be a CORS error. Check the server CORS configuration and network tab.');
    }
    throw error;
  }
};

// Download a video file
export const downloadVideo = async (filename) => {
  try {
    console.log(`ApiService: Downloading video file: ${filename}`);
    const response = await fetch(`https://${API_BASE_URL}/download_video/${filename}`, {
      method: 'GET',
      headers: {
        'Accept': 'video/mp4'
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`ApiService: Video download failed with status ${response.status}:`, errorText);
      throw new Error(`Failed to download video: ${response.status} - ${errorText}`);
    }
    
    // Return the blob for video playback
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  } catch (error) {
    console.error('ApiService: Error downloading video:', error);

    throw error;
  }
};

// Get video URL for streaming
export const getVideoUrl = async (filename) => {
  if (!filename) return null;
  
  try {
    // Instead of returning a URL to the backend, download the video first
    // and return a blob URL that can be played locally in the browser
    console.log(`ApiService: Creating blob URL for video: ${filename}`);
    return await downloadVideo(filename);
  } catch (error) {
    console.error('ApiService: Error creating blob URL for video:', error);
    // Return null instead of a potentially problematic direct URL
    return null;
  }
};

