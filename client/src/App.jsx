import { useState, useEffect, useRef } from 'react'
import Characters, { getFandomByCharacterId, getCharacterById } from './components/Characters'
import ExampleSkits from './components/ExampleSkits'
import * as ApiService from './components/ApiService'
import './App.css'

function App() {
  const [prompt, setPrompt] = useState('')
  const [selectedCharacter, setSelectedCharacter] = useState('harry-potter')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState(null)
  const [step, setStep] = useState(1) // 1: Enter prompt, 2: Select character, 3: Result
  const [showExamples, setShowExamples] = useState(true)
  const [chapters, setChapters] = useState([])
  const [activeChapter, setActiveChapter] = useState(0)
  const [subtopics, setSubtopics] = useState([])
  const [processingQueue, setProcessingQueue] = useState([])
  const videoRef = useRef(null)
  const [loadingStatus, setLoadingStatus] = useState('')
  const [error, setError] = useState(null)

  // Effect to play the video when transitioning from loading to results
  useEffect(() => {
    // If we just finished generating the first video
    if (!isGenerating && videoRef.current && chapters.length > 0 && chapters[activeChapter]?.status === 'ready') {
      console.log('DEBUG: Auto-playing video after generation completed');

      // Get current chapter
      const currentChapter = chapters[activeChapter];

      // Add a fresh timestamp to the URL to avoid caching issues
      if (currentChapter.videoUrl) {
        const baseUrl = currentChapter.videoUrl.split('?')[0];
        const freshUrl = `${baseUrl}?t=${Date.now()}`;

        if (videoRef.current) {
          // Update the src attribute with the fresh URL
          videoRef.current.src = freshUrl;

          // Load and play the video
          videoRef.current.load();
          videoRef.current.play().catch(e => {
            console.error('Error auto-playing video:', e);

            // If that fails, try one more time with a fresh URL
            const retryUrl = `${baseUrl}?t=${Date.now()}`;
            if (videoRef.current) {
              videoRef.current.src = retryUrl;
              videoRef.current.load();
              videoRef.current.play().catch(err =>
                console.error('Final error playing video after retry:', err)
              );
            }
          });
        }
      }
    }
  }, [isGenerating, activeChapter, chapters]);

  // Get character name based on ID
  const getCharacterName = (id) => {
    const character = getCharacterById(id);
    return character.name;
  }

  const handlePromptSubmit = (e) => {
    e?.preventDefault()
    if (!prompt.trim()) return

    setStep(2) // Move to character selection
    setShowExamples(false)
  }

  const handleCharacterSelect = (characterId) => {
    setSelectedCharacter(characterId)
  }


  // const fetchSubtopicsFromApi = async (concept) => {
  //   try {
  //     console.log(`App: Fetching subtopics for concept: ${concept}`);
  //     // ApiService.fetchSubtopics already returns an array of string titles
  //     const subtopicTitles = await ApiService.fetchSubtopics(concept);
  //     console.log(`App: Received subtopic titles:`, subtopicTitles);
  //     return subtopicTitles;
  //   } catch (error) {
  //     console.error('Failed to fetch subtopics:', error);
  //     // Return some default subtopics if API fails
  //     return [
  //       `Introduction to ${concept}`,
  //       `Basic ${concept} principles`,
  //       `Advanced ${concept} concepts`,
  //       `Real-world applications of ${concept}`
  //     ];
  //   }
  // }

  // Process the next subtopic in the queue
  // const processNextInQueue = async () => {
  //   // If there are no items in the queue, we're done
  //   if (processingQueue.length === 0) {
  //     console.log("DEBUG: Processing queue is empty, nothing to process");
  //     return;
  //   }

  //   console.log(`DEBUG: Processing queue has ${processingQueue.length} items`);

  //   // Get the next item to process
  //   const nextItem = processingQueue[0];
  //   console.log(`DEBUG: Processing queue item:`, nextItem);

  //   try {
  //     // Update the chapter status to show it's generating
  //     setChapters(prev => {
  //       const updated = [...prev];
  //       updated[nextItem.index].status = 'generating';
  //       updated[nextItem.index].progress = 10;
  //       return updated;
  //     });

  //     console.log(`DEBUG: Chapter status updated to generating`);

  //     // Update loading message if still on loading screen
  //     if (isGenerating && nextItem.index === 0) {
  //       setLoadingStatus(`Generating script for "${nextItem.subtopic}"...`);
  //       console.log(`DEBUG: Updated loading status for first item`);
  //     }

  //     // Step 1: Generate script
  //     console.log(`DEBUG: About to generate script for: ${nextItem.subtopic}`);
  //     updateProgress(nextItem.index, 20, `Generating script...`);

  //     console.log(`DEBUG: Making API call to generate script with:`, {
  //       subtopic: nextItem.subtopic,
  //       fandom: getFandomByCharacterId(selectedCharacter)
  //     });

  //     const script = await ApiService.generateScript(
  //       nextItem.subtopic,
  //       getFandomByCharacterId(selectedCharacter)
  //     );
  //     console.log(`DEBUG: Script generated successfully`);

  //     // Step 2: Generate voiceover
  //     console.log('Generating voiceover...');
  //     setLoadingStatus(`Generating voiceover for "${nextItem.subtopic}"...`);
  //     updateProgress(nextItem.index, 40, `Creating voiceover...`);
  //     const voiceoverResult = await ApiService.generateVoiceover(script);

  //     // Step 3: Generate video
  //     console.log('Generating video...');
  //     setLoadingStatus(`Generating video for "${nextItem.subtopic}" (takes 3-4 minutes)...`);
  //     updateProgress(nextItem.index, 70, `Creating video with images and clips...`);

  //     try {
  //       const videoResult = await ApiService.generateVideo(voiceoverResult.voiceover_data);

  //       const videoUrl = ApiService.getVideoUrl(videoResult.video_data.video_filename);

  //       // Final result with all data
  //       const result = {
  //         script,
  //         voiceover: voiceoverResult,
  //         video: videoResult,
  //         videoUrl: videoUrl
  //       };

  //       // Update the chapter
  //       setChapters(prev => {
  //         const updated = [...prev];
  //         updated[nextItem.index] = {
  //           ...updated[nextItem.index],
  //           status: 'ready',
  //           videoUrl: result.videoUrl,
  //           duration: formatDuration(result.video.video_data.duration)
  //         };
  //         return updated;
  //       });
  //     } catch (error) {
  //       console.error(`Error generating video for subtopic: ${nextItem.subtopic}`, error);

  //       // show error message in the frontend
  //       setResult({
  //         title: `${prompt} with ${getCharacterName(selectedCharacter)}`,
  //         status: 'Error: Failed to generate content'
  //       });
  //       setIsGenerating(false);
  //       setActiveChapter(0);
  //       return;
  //     }

  //     // If this is the first video, immediately transition to results
  //     if (nextItem.index === 0) {
  //       console.log('DEBUG: First video is ready, transitioning to results view');
  //       setIsGenerating(false);
  //       setActiveChapter(0);
  //     }

  //     // Remove this item from the queue
  //     setProcessingQueue(prev => prev.slice(1));

  //     // Continue processing the next item
  //     processNextInQueue();

  //   } catch (error) {
  //     console.error(`Error processing subtopic: ${nextItem.subtopic}`, error);

  //     // Update the chapter to show the error
  //     setChapters(prev => {
  //       const updated = [...prev];
  //       updated[nextItem.index].status = 'error';
  //       updated[nextItem.index].error = 'Failed to generate content';
  //       return updated;
  //     });

  //     // If this is the first video and we're still on loading screen, show error and transition
  //     if (nextItem.index === 0 && isGenerating) {
  //       setIsGenerating(false);
  //     }

  //     // Continue with the next item despite the error
  //     setProcessingQueue(prev => prev.slice(1));
  //     processNextInQueue();
  //   }
  // };

  // Helper function to update progress
  const updateProgress = (index, progress, statusMessage) => {
    setChapters(prev => {
      const updated = [...prev];
      updated[index].progress = progress;
      return updated;
    });

    // Update loading message if this is the first item and we're still on the loading screen
    if (isGenerating && index === 0) {
      setLoadingStatus(`${statusMessage} (${progress}%)`);
    }
  };

  // Format seconds to mm:ss
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleGenerateSkit = async () => {
    setIsGenerating(true);
    setLoadingStatus('Preparing your content...');
    setStep(3); // Move to review step
    console.log(`DEBUG: Starting generation with prompt: ${prompt}`);

    try {
      // Fetch actual subtopics from the API
      console.log(`DEBUG: About to fetch subtopics`);
      const fetchedSubtopics = await ApiService.fetchSubtopics(prompt);
      console.log(`DEBUG: Fetched subtopics:`, fetchedSubtopics);

      if (!fetchedSubtopics || fetchedSubtopics.length === 0) {
        console.log(`DEBUG: No subtopics fetched, throwing error`);
        throw new Error("Failed to get subtopics");
      }

      // Create initial chapters based on subtopics
      const initialChapters = fetchedSubtopics.map((subtopic, index) => ({
        id: index + 1,
        title: typeof subtopic === 'string' ? subtopic : (subtopic.title || `Chapter ${index + 1}`),
        status: index === 0 ? 'generating' : 'queued',
        progress: index === 0 ? 10 : 0,
        estimatedTime: '5:00'
      }));

      // Create a processing queue for the subtopics
      const queue = fetchedSubtopics.map((subtopic, index) => ({
        subtopic: typeof subtopic === 'string' ? subtopic : (subtopic.title || `Chapter ${index + 1}`),
        index
      }));

      console.log(`DEBUG: Created processing queue:`, queue);

      // Set all state at once to avoid race conditions
      setSubtopics(fetchedSubtopics);
      setChapters(initialChapters);
      setProcessingQueue(queue);
      setLoadingStatus('Fetched subtopics, preparing generation...');
      setResult({
        title: `${prompt} with ${getCharacterName(selectedCharacter)}`,
        status: 'Generating content...'
      });
      console.log(`DEBUG: All state set, queue length:`, queue.length);

      // Start processing items directly using the queue we just created
      // rather than depending on the state update
      if (queue.length > 0) {
        const firstSubtopic = queue[0].subtopic;
        console.log(`DEBUG: Starting generation directly with first subtopic:`, firstSubtopic);
        setLoadingStatus(`Starting generation of "${firstSubtopic}"...`);

        // Instead of using setTimeout and depending on state, 
        // we'll process the queue directly
        await processQueueItems(queue);
      } else {
        console.log(`DEBUG: No subtopics to process (this shouldn't happen)`);
      }
    } catch (error) {
      console.error('Error starting generation:', error);
      setIsGenerating(false);
      // Show error state
      setResult({
        title: `${prompt} with ${getCharacterName(selectedCharacter)}`,
        status: 'Error: Failed to generate content (ref: in handleGenerateSkit)'
      });
    }
  };

  // New function to process queue items without relying on state updates
  const processQueueItems = async (queue) => {
    // Process all items in the queue one by one
    for (let i = 0; i < queue.length; i++) {
      const item = queue[i];
      console.log(`DEBUG: Processing queue item ${i + 1}/${queue.length}:`, item);

      try {
        // Update chapter status
        setChapters(prev => {
          const updated = [...prev];
          updated[item.index].status = 'generating';
          updated[item.index].progress = 10;
          return updated;
        });

        // Step 1: Generate script
        console.log(`DEBUG: About to generate script for: ${item.subtopic}`);

        // Update progress
        setLoadingStatus(`Generating script for "${item.subtopic}"...`);
        updateProgress(item.index, 20, `Generating script...`);

        const fandom = getFandomByCharacterId(selectedCharacter);
        console.log(`DEBUG: Making API call to generate script with:`, {
          subtopic: item.subtopic,
          fandom: fandom
        });

        const script = await ApiService.generateScript(
          item.subtopic,
          fandom
        );
        console.log(`DEBUG: Script generated successfully`);

        // Step 2: Generate voiceover
        console.log('DEBUG: Generating voiceover...');
        setLoadingStatus(`Generating voiceover for "${item.subtopic}"...`);
        updateProgress(item.index, 40, `Creating voiceover...`);

        const voiceoverResult = await ApiService.generateVoiceover(script);

        // Step 3: Generate video
        console.log('DEBUG: Generating video...');
        setLoadingStatus(`Generating video for "${item.subtopic}" (takes 3-4 minutes)...`);
        updateProgress(item.index, 70, `Creating video with images and clips...`);

        try {
          const videoResult = await ApiService.generateVideo(voiceoverResult.voiceover_data);

          const videoUrl = ApiService.getVideoUrl(videoResult.video_data.video_filename);
          // Final result with all data
          const result = {
            script,
            voiceover: voiceoverResult,
            video: videoResult,
            videoUrl: videoUrl
          };

          // Update the chapter
          setChapters(prev => {
            const updated = [...prev];
            updated[item.index] = {
              ...updated[item.index],
              status: 'ready',
              videoUrl: result.videoUrl,
              duration: formatDuration(result.video.video_data.duration)
            };
            return updated;
          });

          // If this is the first video, immediately transition to results
          if (item.index === 0) {
            console.log('DEBUG: First video is ready, transitioning to results view');
            setIsGenerating(false);
            setActiveChapter(0);

            // Stop processing more items for now, let the user see the first video
            // We'll handle the remaining videos in the background
            if (i < queue.length - 1) {
              // Process remaining items in the background
              setTimeout(() => {
                processQueueItems(queue.slice(i + 1));
              }, 1000);

              // Exit the loop since we're handling remaining items separately
              break;
            }
          }
        } catch (error) {
          console.error(`Error generating video for subtopic: ${item.subtopic}`, error);

          // show error message in the frontend
          setResult({
            title: `${prompt} with ${getCharacterName(selectedCharacter)}`,
            status: 'Error: Failed to generate content (ref: in processQueueItems)'
          });

          // If this is the first video, transition to results view even with error
          if (item.index === 0) {
            setIsGenerating(false);
            setActiveChapter(0);
          }

          return;
        }
      } catch (error) {
        console.error(`Error processing subtopic: ${item.subtopic}`, error);

        // Update the chapter to show error
        setChapters(prev => {
          const updated = [...prev];
          updated[item.index].status = 'error';
          updated[item.index].error = 'Failed to generate content';
          return updated;
        });

        // If this is the first video and we're still on loading screen, transition
        if (item.index === 0 && isGenerating) {
          setIsGenerating(false);
          setActiveChapter(0);
        }
      }
    }
  };

  const handleReset = () => {
    setPrompt('')
    setStep(1)
    setResult(null)
    setShowExamples(true)
    setChapters([])
    setSubtopics([])
    setProcessingQueue([])
  }

  const handleChapterSelect = (index) => {
    const chapter = chapters[index];
    if (chapter.status === 'ready') {
      console.log(`Selecting chapter ${index}: ${chapter.title}`);
      setActiveChapter(index);

      // If we have a video element reference, reset and play the new video
      if (videoRef.current) {
        // Get fresh URL with timestamp for cache busting
        if (chapter.videoUrl) {
          const baseUrl = chapter.videoUrl.split('?')[0];
          const freshUrl = `${baseUrl}?t=${Date.now()}`;

          // Update video src and load/play
          videoRef.current.src = freshUrl;
          videoRef.current.load();

          // Try to play, but don't worry if it fails (user can click play)
          videoRef.current.play().catch(e => {
            console.log('User interaction may be needed to play the video:', e);
          });
        }
      }
    } else {
      console.log(`Chapter ${index} not ready yet, status: ${chapter.status}`);
    }
  }

  // Replace the video placeholder with an actual video player
  const renderVideoPlayer = () => {
    const chapter = chapters[activeChapter];

    if (!chapter || chapter.status !== 'ready') {
      return (
        <div className="video-placeholder">
          <div className="play-icon">▶</div>
          {chapter ? (
            <>
              <p>Chapter {activeChapter + 1}: {chapter.title}</p>
              <p className="video-guide">
                {chapter.status === 'generating'
                  ? `Generating video... ${chapter.progress || 0}%`
                  : chapter.status === 'error'
                    ? 'Error generating video'
                    : 'Waiting in queue...'}
              </p>
            </>
          ) : (
            <p>Select a ready chapter to watch the video</p>
          )}
        </div>
      );
    }

    // Check if this is an audio-only fallback
    if (chapter.isAudioOnly) {
      return (
        <div className="audio-player-container">
          <div className="audio-player-header">
            <h3>Audio Only Mode</h3>
            <p>Video generation was not successful, but you can still listen to the audio explanation.</p>
          </div>
          {chapter.videoUrl ? (
            <audio
              ref={videoRef}
              controls
              autoPlay
              src={chapter.videoUrl}
              className="audio-only-player"
              onError={(e) => console.error('Error playing audio:', e)}
            >
              Your browser does not support the audio element.
            </audio>
          ) : (
            <div className="script-fallback">
              <h4>Audio Unavailable</h4>
              <p>Sorry, neither video nor audio could be generated. Here's the script:</p>
              <div className="script-content">
                {chapter.script && typeof chapter.script === 'object' ? (
                  <pre>{JSON.stringify(chapter.script, null, 2)}</pre>
                ) : (
                  <p>{chapter.script || "No script available"}</p>
                )}
              </div>
            </div>
          )}
        </div>
      );
    }

    // Add timestamp for cache busting
    const videoUrl = chapter.videoUrl ?
      `${chapter.videoUrl.split('?')[0]}?t=${Date.now()}` :
      '';

    // Handler for video loading events
    const handleVideoLoaded = () => {
      console.log('Video loaded successfully');
    };

    // Handler for video loading errors
    const handleVideoError = (e) => {
      console.error('Error loading video:', e);

      // If the video failed to load, we'll retry with a new URL
      const videoElement = e.target;
      if (videoElement && chapter.videoUrl) {
        console.log('Retrying video playback with fresh URL');

        // Create a fresh URL with a timestamp to bypass cache
        const freshUrl = `${chapter.videoUrl.split('?')[0]}?t=${Date.now()}`;

        // Set a small timeout before retrying
        setTimeout(() => {
          videoElement.src = freshUrl;
          videoElement.load();
          videoElement.play().catch(err => console.error('Error playing video after retry:', err));
        }, 1000);
      }
    };

    return (
      <div className="video-wrapper">
        <video
          ref={videoRef}
          className="actual-video-player"
          controls
          autoPlay
          preload="auto"
          width="100%"
          height="auto"
          src={videoUrl}
          poster={`https://via.placeholder.com/640x360/111827/FFFFFF?text=${encodeURIComponent(chapter.title)}`}
          onError={handleVideoError}
          onCanPlay={handleVideoLoaded}
        >
          Your browser does not support the video tag.
        </video>
        <div className="video-loading-message">
          If the video doesn't start automatically, please click the play button.
        </div>
      </div>
    );
  }

  // Handle navigation between chapters
  const handlePreviousChapter = () => {
    if (activeChapter > 0) {
      // Find the previous ready chapter
      for (let i = activeChapter - 1; i >= 0; i--) {
        if (chapters[i].status === 'ready') {
          handleChapterSelect(i);
          return;
        }
      }
    }
  };

  const handleNextChapter = () => {
    if (activeChapter < chapters.length - 1) {
      // Find the next ready chapter
      for (let i = activeChapter + 1; i < chapters.length; i++) {
        if (chapters[i].status === 'ready') {
          handleChapterSelect(i);
          return;
        }
      }
    }
  };

  // Check if there are previous or next ready chapters
  const hasPreviousReadyChapter = () => {
    for (let i = activeChapter - 1; i >= 0; i--) {
      if (chapters[i]?.status === 'ready') return true;
    }
    return false;
  };

  const hasNextReadyChapter = () => {
    for (let i = activeChapter + 1; i < chapters.length; i++) {
      if (chapters[i]?.status === 'ready') return true;
    }
    return false;
  };

  // Handle application errors
  const handleError = () => {
    setError(null);
    setStep(1);
    setIsGenerating(false);
    setChapters([]);
    setProcessingQueue([]);
  };

  return (
    <div className="app-container">
      <header>
        <h1>Ed<span className="accent">Verse</span></h1>
        <p className="tagline">Fictional characters explain complex topics</p>
      </header>

      <main>
        {/* Interactive creation process */}
        <div className="creation-process">
          <div className="steps-indicator">
            <div className={`step ${step >= 1 ? 'active' : ''}`}>
              <div className="step-number">1</div>
              <span>Topic</span>
            </div>
            <div className="step-connector"></div>
            <div className={`step ${step >= 2 ? 'active' : ''}`}>
              <div className="step-number">2</div>
              <span>Character</span>
            </div>
            <div className="step-connector"></div>
            <div className={`step ${step >= 3 ? 'active' : ''}`}>
              <div className="step-number">3</div>
              <span>Result</span>
            </div>
          </div>

          <div className="step-content">
            {step === 1 && (
              <section className="prompt-section">
                <h2>What topic would you like explained?</h2>
                <p className="instruction">Enter any complex topic you want to learn about</p>

                <form onSubmit={handlePromptSubmit} className="prompt-form">
                  <div className="input-container">
                    <input
                      type="text"
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="AI Transformers, Climate Change, Quantum Physics..."
                      className="prompt-input"
                      autoFocus
                    />
                    <button
                      type="submit"
                      className="next-btn"
                      disabled={!prompt.trim()}
                    >
                      Next
                    </button>
                  </div>
                </form>
              </section>
            )}

            {step === 2 && (
              <section className="character-selection-section">
                <h2>Who should explain "{prompt}"?</h2>
                <p className="instruction">Choose a character to explain your topic</p>

                <Characters
                  selectedCharacter={selectedCharacter}
                  onSelectCharacter={handleCharacterSelect}
                  showAllByDefault={true}
                />

                <div className="navigation-buttons">
                  <button className="back-btn" onClick={() => setStep(1)}>
                    Back
                  </button>
                  <button className="generate-btn" onClick={handleGenerateSkit}>
                    Generate Skit
                  </button>
                </div>
              </section>
            )}

            {step === 3 && (
              <section className="result-section">
                {error ? (
                  <div className="error-message">
                    <h2>Something went wrong</h2>
                    <p>{error}</p>
                    <button className="retry-btn" onClick={handleError}>
                      Start Over
                    </button>
                  </div>
                ) : isGenerating ? (
                  <div className="loading-section">
                    <h2>Creating your skit...</h2>
                    <p>Using AI to transform "{prompt}" into an engaging scene with {getCharacterName(selectedCharacter)}</p>
                    <p className="patience-note">This process can take several minutes. Please be patient.</p>
                    <div className="loading-animation">
                      <div className="magic-orb">
                        <div className="inner-orb"></div>
                        <div className="orbit">
                          <div className="orbit-particle"></div>
                        </div>
                        <div className="orbit orbit2">
                          <div className="orbit-particle"></div>
                        </div>
                      </div>
                    </div>
                    <p className="loading-message">{loadingStatus || 'Starting generation process...'}</p>
                    {chapters.length > 0 && (
                      <div className="loading-progress">
                        <h3>Current Progress:</h3>
                        <div className="chapters-status-list">
                          {chapters.map((chapter, index) => (
                            <div key={index} className={`chapter-status ${chapter.status}`}>
                              <span className="chapter-status-title">{chapter.title}</span>
                              <div className="chapter-status-info">
                                {chapter.status === 'ready' ? (
                                  <span className="status-complete">Ready</span>
                                ) : chapter.status === 'generating' ? (
                                  <div className="mini-progress-bar">
                                    <div
                                      className="mini-progress-fill"
                                      style={{ width: `${chapter.progress}%` }}
                                    ></div>
                                    <span>{chapter.progress}%</span>
                                  </div>
                                ) : chapter.status === 'error' ? (
                                  <span className="status-error">Error</span>
                                ) : (
                                  <span className="status-queued">In queue</span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="skit-result">
                    <div className="result-header">
                      <h2>{result?.title}</h2>
                      <div className="badge success-badge">Video Series</div>
                    </div>

                    <div className="chapters-container">
                      <div className="chapters-sidebar">
                        <h3>Chapters</h3>
                        <div className="chapters-list">
                          {chapters.map((chapter, index) => (
                            <div
                              key={chapter.id}
                              className={`chapter-item ${activeChapter === index ? 'active' : ''} ${chapter.status}`}
                              onClick={() => handleChapterSelect(index)}
                            >
                              <div className="chapter-number">{index + 1}</div>
                              <div className="chapter-details">
                                <h4>{chapter.title}</h4>
                                {chapter.status === 'ready' ? (
                                  <span className="chapter-duration">{chapter.duration}</span>
                                ) : chapter.status === 'generating' ? (
                                  <div className="chapter-progress">
                                    <div className="progress-bar">
                                      <div className="progress-fill" style={{ width: `${chapter.progress}%` }}></div>
                                    </div>
                                    <span>Generating... ~{chapter.estimatedTime}</span>
                                  </div>
                                ) : (
                                  <span className="chapter-queued">In queue (~{chapter.estimatedTime})</span>
                                )}
                              </div>
                              {chapter.status === 'ready' && <div className="chapter-ready-icon">▶</div>}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="video-player-container">
                        <div className="video-player">
                          {renderVideoPlayer()}
                        </div>
                        {chapters.length > 0 && chapters[activeChapter]?.status === 'ready' && (
                          <div className="video-controls">
                            <button
                              className="video-control-btn"
                              disabled={!hasPreviousReadyChapter()}
                              onClick={handlePreviousChapter}
                            >
                              Previous
                            </button>
                            <div className="video-timeline">
                              <div className="timeline-progress" style={{ width: `${((activeChapter + 1) / chapters.length) * 100}%` }}></div>
                            </div>
                            <button
                              className="video-control-btn"
                              disabled={!hasNextReadyChapter()}
                              onClick={handleNextChapter}
                            >
                              Next
                            </button>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="action-buttons">
                      <button className="share-btn">
                        <span className="icon">↗</span> Share
                      </button>
                      <button className="download-btn">
                        <span className="icon">↓</span> Download
                      </button>
                      <button className="new-skit-btn" onClick={handleReset}>
                        Create New Skit
                      </button>
                    </div>
                  </div>
                )}
              </section>
            )}
          </div>
        </div>

        {/* Hero section only shown on first visit */}
        {step === 1 && (
          <section className="hero-section">
            <div className="hero-content">
              <h2>Create magical skits with your favorite characters</h2>
              <p>
                We use AI to generate creative scenes where fictional characters explain
                complex topics in an entertaining and educational way.
              </p>
              <div className="hero-benefits">
                <div className="benefit-item">
                  <div className="benefit-icon">🎭</div>
                  <div className="benefit-text">Entertaining explanations</div>
                </div>
                <div className="benefit-item">
                  <div className="benefit-icon">🧠</div>
                  <div className="benefit-text">Complex topics simplified</div>
                </div>
                <div className="benefit-item">
                  <div className="benefit-icon">⚡</div>
                  <div className="benefit-text">Generated in seconds</div>
                </div>
              </div>
            </div>
            <div className="hero-image">
              <div className="magic-circle"></div>
            </div>
          </section>
        )}

      </main>

      <footer>
        <div className="hackathon-badge">
          AI Genesis Hackathon Entry
        </div>
        <p>&copy; 2025 EdVerse</p>
      </footer>
    </div>
  )
}

export default App
