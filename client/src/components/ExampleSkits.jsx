import React from 'react';

const exampleSkits = [
    {
        id: 1,
        title: 'Quantum Computing with Iron Man',
        thumbnail: 'https://via.placeholder.com/300x180?text=Quantum+Computing',
        views: '2.3K',
        character: 'Iron Man'
    },
    {
        id: 2,
        title: 'Climate Change explained by Harry Potter',
        thumbnail: 'https://via.placeholder.com/300x180?text=Climate+Change',
        views: '4.1K',
        character: 'Harry Potter'
    },
    {
        id: 3,
        title: 'Blockchain Technology with Sherlock Holmes',
        thumbnail: 'https://via.placeholder.com/300x180?text=Blockchain',
        views: '1.7K',
        character: 'Sherlock Holmes'
    }
];

function ExampleSkits() {
    return (
        <section className="examples-section">
            <div className="section-header">
                <h3>Popular Skits</h3>
                <button className="view-all-btn">View All</button>
            </div>

            <div className="examples-grid">
                {exampleSkits.map(skit => (
                    <div key={skit.id} className="example-card">
                        <div className="example-thumbnail">
                            <img src={skit.thumbnail} alt={skit.title} />
                            <div className="play-overlay">
                                <div className="play-button">▶</div>
                            </div>
                        </div>
                        <div className="example-info">
                            <h4>{skit.title}</h4>
                            <div className="example-meta">
                                <span className="character">{skit.character}</span>
                                <span className="views">{skit.views} views</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}

export default ExampleSkits; 