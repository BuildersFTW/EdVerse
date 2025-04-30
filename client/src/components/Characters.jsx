import { useState } from 'react';

// Update character data to ensure consistent ID and universe values
const characters = [
    {
        id: 'harry-potter',
        name: 'Hermione Granger',
        universe: 'Harry Potter',
        fandom: 'Harry Potter', // This is the exact fandom name used in API
        voiceId: 'nDJIICjR9zfJExIFeSCN', // Voice ID from voiceover.py
        image: 'https://miro.medium.com/v2/resize:fit:1400/0*fZV8g-1uYh05uz3H',
        available: true
    },
    {
        id: 'star-wars',
        name: 'Darth Vader',
        universe: 'Star Wars',
        fandom: 'Star Wars', // This is the exact fandom name used in API
        voiceId: 'zYcjlYFOd3taleS0gkk3', // Voice ID from voiceover.py
        image: 'https://i.pinimg.com/474x/51/e3/7c/51e37c2b688170cdc07888eba287bfd1.jpg',
        available: true
    },
    {
        id: 'marvel',
        name: 'Iron Man',
        universe: 'Marvel Avengers',
        fandom: 'Marvel Avengers', // This is the exact fandom name used in API
        voiceId: 'jB108zg64sTcu1kCbN9L', // Voice ID from voiceover.py
        image: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1rIWZdIa6hfBRsNAFtrRjPFreZQj9Zomtgg&s',
        available: true
    },
    {
        id: 'sherlock',
        name: 'Sherlock Holmes',
        universe: 'Detective Fiction',
        fandom: 'Detective Fiction',
        voiceId: '',
        image: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSH35kBHWgb3E7WvB0LC8JYu9qGnKTMmBPmGA&s',
        available: false
    },
    {
        id: 'dc-batman',
        name: 'Batman',
        universe: 'DC Comics',
        fandom: 'DC Comics',
        voiceId: '',
        image: 'https://m.media-amazon.com/images/M/MV5BMTYwNjAyODIyMF5BMl5BanBnXkFtZTYwNDMwMDk2._V1_.jpg',
        available: false
    }
];

// Get character info by ID for easier access
export const getCharacterById = (id) => {
    return characters.find(character => character.id === id) || characters[0];
};

// Get fandom name by character ID
export const getFandomByCharacterId = (id) => {
    const character = getCharacterById(id);
    return character.fandom;
};

// Get voice ID by character ID
export const getVoiceIdByCharacterId = (id) => {
    const character = getCharacterById(id);
    return character.voiceId;
};

function Characters({ selectedCharacter, onSelectCharacter, showAllByDefault = false }) {
    const [showAll, setShowAll] = useState(showAllByDefault);

    // Filter out duplicate characters and show only unique ones
    const uniqueCharacters = characters.filter((character, index, self) =>
        index === self.findIndex(c => c.id === character.id)
    );

    // Always show all characters if showAllByDefault is true
    const displayedCharacters = showAll ? uniqueCharacters : uniqueCharacters.slice(0, 6);

    const handleSelectCharacter = (character) => {
        if (character.available) {
            onSelectCharacter(character.id);
        }
    };

    return (
        <div className="characters-container">
            <h3>Choose your narrator</h3>
            <p>Select a character to explain your topic</p>

            <div className="characters-grid">
                {displayedCharacters.map((character) => (
                    <div
                        key={character.id}
                        className={`character-card ${selectedCharacter === character.id ? 'selected' : ''} ${!character.available ? 'disabled' : ''}`}
                        onClick={() => handleSelectCharacter(character)}
                    >
                        <div className="character-image">
                            <img src={character.image} alt={character.name} />
                            {!character.available && (
                                <div className="coming-soon-badge">Coming Soon</div>
                            )}
                        </div>
                        <div className="character-info">
                            <h4>{character.name}</h4>
                            <span>{character.universe}</span>
                        </div>
                    </div>
                ))}
            </div>

            {!showAllByDefault && uniqueCharacters.length > 6 && (
                <button
                    className="show-more-btn"
                    onClick={() => setShowAll(!showAll)}
                >
                    {showAll ? 'Show Less' : 'Show More'}
                </button>
            )}
        </div>
    );
}

export default Characters; 