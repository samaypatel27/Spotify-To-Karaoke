import React, {useState, useEffect, useContext} from 'react';
import axios from 'axios';
import formContext from "../context/FormContext.js";

const Process = () => {
    const {state, dispatch} = useContext(formContext);
    const [progress, setProgress] = useState(0);
    const [currentSong, setCurrentSong] = useState('');
    const [playlistId, setPlaylistId] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [results, setResults] = useState([]);

    useEffect(() => {
        // Start processing when component mounts
        if (state.np_queries && state.np_queries.length > 0) {
            processPlaylist();
        }
    }, []);

    const createYouTubePlaylist = async (token) => {
        try {
            const response = await fetch('https://www.googleapis.com/youtube/v3/playlists?part=snippet,status', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    snippet: {
                        title: state.np_name || 'Karaoke Playlist',
                        description: state.np_description || 'Generated karaoke playlist from Spotify',
                        defaultLanguage: 'en'
                    },
                    status: {
                        privacyStatus: state.np_public ? 'public' : 'private' // public, private, or unlisted
                    }
                })
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error.message);
            }
            
            return data.id;
        } catch (error) {
            console.error('Error creating playlist:', error);
            throw error;
        }
    };

    const searchYouTubeKaraoke = async (query, token) => {
        try {
            // Try different search terms for better karaoke results
            const searchQueries = [
                `${query} karaoke`,
            ];

            for (const searchQuery of searchQueries) {
                const response = await fetch(
                    `https://www.googleapis.com/youtube/v3/search?part=snippet&q=${encodeURIComponent(searchQuery)}&type=video&maxResults=1&key=${token}`,
                    {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    }
                );

                const data = await response.json();
                
                if (data.items && data.items.length > 0) {
                    return {
                        videoId: data.items[0].id.videoId,
                        title: data.items[0].snippet.title,
                        searchTerm: searchQuery
                    };
                }
            }
            
            // If no karaoke version found, return null
            return null;
        } catch (error) {
            console.error('Error searching YouTube:', error);
            return null;
        }
    };

    const addVideoToPlaylist = async (playlistId, videoId, token) => {
        try {
            const response = await fetch('https://www.googleapis.com/youtube/v3/playlistItems?part=snippet', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    snippet: {
                        playlistId: playlistId,
                        resourceId: {
                            kind: 'youtube#video',
                            videoId: videoId
                        }
                    }
                })
            });

            const data = await response.json();
            return !data.error;
        } catch (error) {
            console.error('Error adding video to playlist:', error);
            return false;
        }
    };

    const processPlaylist = async () => {
        setIsProcessing(true);
        const token = sessionStorage.getItem('youtubeToken');
        
        if (!token) {
            alert('YouTube authentication token not found. Please go back and login again.');
            return;
        }

        try {
            // Step 1: Create YouTube playlist
            setCurrentSong('Creating playlist...');
            const newPlaylistId = await createYouTubePlaylist(token);
            setPlaylistId(newPlaylistId);

            // Step 2: Process each song
            const processResults = [];
            const totalSongs = state.np_queries.length;

            for (let i = 0; i < totalSongs; i++) {
                const query = state.np_queries[i];
                setCurrentSong(`Searching: ${query}`);
                setProgress(((i + 1) / totalSongs) * 100);

                // Search for karaoke version
                const searchResult = await searchYouTubeKaraoke(query, token);
                
                if (searchResult) {
                    // Add to playlist
                    const added = await addVideoToPlaylist(newPlaylistId, searchResult.videoId, token);
                    
                    processResults.push({
                        originalQuery: query,
                        found: true,
                        videoTitle: searchResult.title,
                        searchTerm: searchResult.searchTerm,
                        added: added
                    });
                } else {
                    processResults.push({
                        originalQuery: query,
                        found: false,
                        added: false
                    });
                }

                // Small delay to avoid rate limiting
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            setResults(processResults);
            setCurrentSong('Complete!');
            setIsProcessing(false);

        } catch (error) {
            console.error('Error processing playlist:', error);
            alert('Error processing playlist: ' + error.message);
            setIsProcessing(false);
        }
    };

    return (
        <div className="container min-vh-100">
            <div className="row justify-content-center">
                <div className="col-md-8">
                    <div className="card">
                        <div className="card-header">
                            <h3>Converting Spotify Playlist to YouTube Karaoke</h3>
                        </div>
                        <div className="card-body">
                            {isProcessing ? (
                                <div>
                                    <div className="mb-3">
                                        <h5>Processing: {currentSong}</h5>
                                        <div className="progress">
                                            <div 
                                                className="progress-bar" 
                                                role="progressbar" 
                                                style={{width: `${progress}%`}}
                                                aria-valuenow={progress} 
                                                aria-valuemin="0" 
                                                aria-valuemax="100"
                                            >
                                                {Math.round(progress)}%
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : results.length > 0 ? (
                                <div>
                                    <h4 className="text-success mb-3">Conversion Complete!</h4>
                                    {playlistId && (
                                        <div className="mb-3">
                                            <a 
                                                href={`https://www.youtube.com/playlist?list=${playlistId}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="btn btn-primary"
                                            >
                                                View YouTube Playlist
                                            </a>
                                        </div>
                                    )}
                                    
                                    <h5>Results Summary:</h5>
                                    <p>Successfully found: {results.filter(r => r.found).length} / {results.length} songs</p>
                                    
                                    <div className="mt-3">
                                        <h6>Detailed Results:</h6>
                                        {results.map((result, index) => (
                                            <div key={index} className={`p-2 mb-2 rounded ${result.found ? 'bg-success bg-opacity-10' : 'bg-danger bg-opacity-10'}`}>
                                                <strong>{result.originalQuery}</strong>
                                                {result.found ? (
                                                    <div className="small text-success">
                                                        ✓ Found: {result.videoTitle}
                                                        <br />
                                                        Search term: {result.searchTerm}
                                                    </div>
                                                ) : (
                                                    <div className="small text-danger">
                                                        ✗ No karaoke version found
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div>
                                    <h5>Ready to process {state.np_queries?.length || 0} songs</h5>
                                    <p>Playlist Name: {state.np_name}</p>
                                    <p>Description: {state.np_description}</p>
                                    <p>Privacy: {state.np_public ? 'Public' : 'Private'}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Process;