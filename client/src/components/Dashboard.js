import React, {useState, useEffect, useContext} from 'react';
import axios from 'axios';
import style from "../styles/dashboard.module.css";
import defaultPlaylistCover from "../images/spotify.jpg";
import formContext from "../context/FormContext.js";
import themeContext from "../context/ThemeContext.js";
import {useNavigate} from "react-router-dom";
import { ClipLoader } from 'react-spinners';

const Dashboard = () => {
  // updating states causes the whole component to re-render
  const [playlists, setPlaylists] = useState([]);
  const [user, setUser] = useState([]);
  const [userLoaded, setUserLoaded] = useState(false);
  const [songs, setSongs] = useState([]);
  const {state, dispatch} = useContext(formContext);
  const {theme, toggleTheme} = useContext(themeContext);
  const navigate = useNavigate();

  useEffect(() => {

    axios.post('http://localhost:5000/spotify/sync', {}, {
      withCredentials: 'include'
    })
      .then(response => {
        console.log(response)
      })
      .catch(error => {
        console.log(error);
      })

    axios.get('http://localhost:5000/db/user', {
      withCredentials: 'include'
    })
      .then(response => {
        setUser(response.data)
        setUserLoaded(true)
      })
      .catch(error => {
        console.log(error)
      })
    axios.get('http://localhost:5000/db/playlists', {
      withCredentials: 'include'
    })
      .then(response => {
        console.log("NEWWWWW" + response)
        console.log(response.data)
        setPlaylists(response.data)
        console.log(playlists)
      })
      .catch(error => {
        console.log(error)
      })
  }, []);

    const getSongsFromPlaylist = (id, name) => {
      axios.get('http://localhost:5000/db/songs/' + id)
        .then(response => {
          setSongs(response.data);
          // dispatch to add playlist name and id
          dispatch({
            type: 'SELECT_PLAYLIST',
            next_np_name: name,
            next_op_id: id
          })
          // Add current song information to the form data (queries)
          let queries = [];
          response.data.map((song)=> {
            queries.push(song.song_name + ' ' + song.song_artists.trim());
          }) 
          dispatch({
            type: 'SET_QUERIES',
            next_np_queries: queries
          })
        })
        .catch(error => {
          console.log(error);
        });
      }

      const toggleSongs = (e) => {
        let checked = e.target.checked;
        let query = e.target.value;
        if (checked)
        {
          dispatch({
            type: 'ADD_QUERY',
            next_np_query: query
          })
        }
        else{
          dispatch({
            type: 'REMOVE_QUERY',
            remove_np_query: query
          })
        }
      }

      const filterPlaylist = (e) => {
        let query = e.target.value;
        console.log(query);
        // if (query.length == 0)
        // {
        //     query = "THIS_IS_INVALID_QUERY"
        // }
        axios.get('http://localhost:5000/db/playlists?search=' + query, {
          withCredentials: 'include'
        })
            .then(response => {
              setPlaylists(response.data)
            })
            .catch(error => {
              console.log(error);
            })
      }

      const filterSong = (e) => {
        let query = e.target.value;
        // selects current playlist id for the parameter for the backend API route
        const playlistID = state.op_id
        axios.get('http://localhost:5000/db/songs/' + playlistID + '?search='+ query)
            .then(response => {
              setSongs(response.data)
            })
            .catch(error => {
              console.log(error);
            })
        
      }

      const logoutUser = () => {
        axios.get('http://localhost:5000/auth/logout', {
          withCredentials: 'include',
        })
          .then(response => {
            window.location.href = "http://localhost:3000/"
            // refresh to home page (clearing states) because the logout only displays on page refresh (data is already set here)
          })
          .catch(error => {
            console.log(error);
          })
      }

      const getYouTubePlaylists = () => {
        axios.get('http://localhost:5000/youtube/playlists', {
          // session is never server - it just created in flask but stored in browser, so we should send cookie information tot he server
          withCredentials: 'include',

        })
          .then(response => {
            console.log(response.data);
          })
          .catch(error => {
            console.log(error);
          })
      }

      const navigatePage = (e) => {
        e.preventDefault();
        navigate("/user/create");
      }

  return (
    <div className = "min-vh-100">
      <div>
      <ul className="nav nav-fill nav-tabs" role="tablist">
        <li className="nav-item" role="presentation">
          <a className="nav-link active" id="fill-tab-0" data-bs-toggle="tab" href="#fill-tabpanel-0" role="tab" aria-controls="fill-tabpanel-0" aria-selected="true">
            <span className={style.tabOverride}>Welcome</span> 
          </a>
        </li>
        <li className="nav-item" role="presentation">
          <a className="nav-link" id="fill-tab-1" data-bs-toggle="tab" href="#fill-tabpanel-1" role="tab" aria-controls="fill-tabpanel-1" aria-selected="false">
            <span className={style.tabOverride}>Create</span>
          </a>
        </li>
        <li className="nav-item" role="presentation">
          <a className="nav-link" id="fill-tab-2" data-bs-toggle="tab" href="#fill-tabpanel-2" role="tab" aria-controls="fill-tabpanel-2" aria-selected="false">
            <span className={style.tabOverride}>View</span>
          </a>
        </li>
      </ul>
      </div>

      <div className="tab-content pt-5" id="tab-content">
        {/* TAB 1: Welcome */}
        <div className="tab-pane active" id="fill-tabpanel-0" role="tabpanel" aria-labelledby="fill-tab-0">
          {
            (!(userLoaded)) ? (
               <div className = {`d-flex flex-column justify-content-center align-items-center ${style.loadingScreen}`}>
                  <ClipLoader
                  color="#ffffffff"
                  loading={true}
                  size={100}
                  aria-label="Loading Spinner"
                  data-testid="loader"
                />
                <div>
                <h1>Fetching User Data...</h1>
                </div>
                </div>
            ) : (
          
          <section>
            <div className="px-4 py-5 px-md-5 text-center text-lg-start">
              <div className="container">
                <div className="row gx-lg-5 align-items-center">
                  <div className="col-lg-6 mb-5 mb-lg-0">
                    <div className={style.nextLine}>
                      <div className="d-flex justify-content-center">
                        <img src={user.image} id={style.userProfile} alt="User Profile" />
                      </div>
                      <div className={style.inLine}>
                        <h1>Welcome</h1>
                        <h1>{user.name}</h1>
                        <div>
                      </div>
                        
                      </div>
                      <div className = "d-flex justify-content-center">
                        {/* TIP: use d-flex justify center for button elements with icon and text,
                        also use text-nowrap to make sure buttons children (elements) all stay on same line and add me-2 (gap for flex) */}
                        <button type="button" class="d-flex align-items-center justify-content-center btn btn-secondary px-5 w-50 text-nowrap" data-bs-toggle="modal" data-bs-target="#settingsModal" id = {style.roundedButton}><i class="bi bi-gear-fill me-2"></i>   Settings</button>
                        <div class="modal fade" id="settingsModal" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="staticBackdropLabel" aria-hidden="true">
                          <div class="modal-dialog modal-sm">
                            <div class="modal-content">
                              <div class="modal-header">
                                <h1 class="modal-title fs-5" id="staticBackdropLabel">Settings</h1>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                              </div>
                              <div class="modal-body">
                                <div class="form-check form-switch">
                                  <input class="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckDefault" onChange = {toggleTheme}></input>
                                  <label class="form-check-label" for="flexSwitchCheckDefault">Dark Mode</label>
                                </div>
                                <hr>
                                </hr>
                                <button class = "btn btn-primary" onClick = {logoutUser}>Logout</button>
                                <hr>
                                </hr>
                                <a class = "btn btn-primary" href = "http://localhost:5000/youtube/login">Login With YouTube</a>
                              </div>
                              <hr></hr>
                                <a class = "btn btn-primary" onClick = {getYouTubePlaylists}>Log YouTube Playlists</a>
                              
                              <div class="modal-footer">
                                <button type="button" class="btn btn-primary" data-bs-dismiss = "modal">Close</button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="col-lg-6 mb-5 mb-lg-0">
                    <div className="card">
                      <div className="card-body py-4 px-md-5">
                        <h3>Getting Started</h3>
                        <hr />
                        <p>Hello, welcome to my website! I am an incoming sophomore at The Ohio State 
                          University, pursuing a degree in Computer Science & Engineering. I am really passionate about web development, and this
                          is my second full-stack application project. This project was built with Spotify, YouTube API, and OAuth 2.0. information
                          from your Spotify account is taken, and updated in real-time onto our website. Unfortunately, there is no way
                          to have one sign in - so anytime you want to create a YouTube karaoke playlist you will have to login in to YouTube every
                          single time. 
                          
                        </p>
                        <h3>Using this website</h3>
                        <hr />
                        <p>
                          Create - Allows you to select Songs from Spotify, then login to YouTube and create your playlist<hr></hr>
                          View - A Dashboard that allows you to see your YouTube playlists that have been converted
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
          )}
        </div>
        
        
        {/* TAB 2: View Playlists */}
        <div className="tab-pane" id="fill-tabpanel-1" role="tabpanel" aria-labelledby="fill-tab-1">
          
          <section>
            <div className = "col-12 mb-2">
                    <div className = "d-flex flex-column align-items-center gap-1 p-2 bg-light bg-opacity-25 rounded text-center">
                      <h3>Select Playlists and Songs to Continue</h3>
                      <a onClick = {navigatePage} className= {` w-25 btn btn-primary ${(state.np_name) || `disabled`}`} tabindex="-1" aria-disabled= {state.np_name ? `true` : `false`} role="button" data-bs-toggle="button">Next</a>
                    </div>
            </div>
            
            <div className="px-4 py-5 px-md-5 text-center text-lg-start">
              
              
              <div className="container">
                
                  
                <div className="row gx-lg-5 align-items-center">
                  <div className="col-lg-6 mb-5 mb-lg-0">
                    <h2 className = "text-center mb-3">Your Playlists</h2>
                    <div className = "d-flex justify-content-center">
                          <div class="position-relative mb-3 w-50">
                      <input className="px-2 py-2 border rounded-2 w-100 bg-transparent text-white placeholder-white" 
                            placeholder="Search Playlist" 
                            type="text" onChange = {filterPlaylist}></input>
                      <i class="bi bi-search position-absolute top-50 end-0 translate-middle-y me-3 text-white"></i>
                      </div>
                    </div>
                    
                    <div className={`border p-3 rounded row ${style.scrollableContainer}`}>
                      {playlists.length > 0 ? 
                        (
                          playlists.map((playlist) => {
                            return (<div key={playlist.id} id = {playlist.id} className={`col-md-4 mb-3 ${(state.op_id === playlist.id) && style.cardClicked}`} onClick = {() => getSongsFromPlaylist(playlist.id, playlist.name)}>
                              <div className="card">
                                <img className="card-img-top" src = {(playlist.image) ? playlist.image : defaultPlaylistCover} alt="Card image cap"></img>
                                <div className="card-body">
                                  <h5 className="card-title">{playlist.name}</h5>
                                </div>
                              </div>
                          </div>)})
                        ) : (
                            <div className="col-lg-6 mb-5 mb-lg-0">
                              <p>No playlists found in your Spotify account</p>
                            </div>
                      )}
                    </div>
                  </div>
                  <div className = "col-lg-6 mb-5 mb-lg-0">
                    <h2 className = "text-center mb-3">Songs</h2>
                    <div className = "d-flex justify-content-center">
                      <div class="position-relative mb-3 w-50">
                      <input className="px-2 py-2 border rounded-2 w-100 bg-transparent text-white placeholder-white" 
                            placeholder="Search Songs" onChange = {filterSong} 
                            type="text"></input>
                      <i class="bi bi-search position-absolute top-50 end-0 translate-middle-y me-3 text-white"></i>
                    </div>
                    </div>
                    
                    <div className={`border p-3 rounded row ${style.scrollableContainer}`}>
                      {songs.length > 0 ? (
                        songs.map((song, index) => {
                          return (
                            <div key={song.id} className="col-12 mb-2">
                              <div className="d-flex align-items-center p-2 bg-light bg-opacity-25 rounded">
                                {/* Track Number */}
                                <div className="me-2  small" style={{minWidth: '20px'}}>
                                  {index + 1}
                                </div>
                                
                                {/* Album Art */}
                                <img 
                                  src={song.image} 
                                  alt={song.name}
                                  className="rounded me-3"
                                  width="40" 
                                  height="40"
                                />
                                
                                {/* Song Info */}
                                <div className="flex-grow-1 me-2">
                                  <div className="fw-bold small">{song.name}</div>
                                  <div className=" small">{song.artists.trim()}</div>
                                </div>
                                
                                {/* Checkbox, the value is the song name plus the artist, which will be what we will use as the searching query for now */}
                                <input type="checkbox" value = {song.name + ' ' + song.artists.trim()} className="form-check-input songElement" onChange = {toggleSongs} defaultChecked></input>
                              </div>
                            </div>
                          )
                        })
                      ) : (
                        <div className="col-12">
                          <p>No songs selected</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                </div>
              </div>
            </div>
          </section>
        </div>
        
        {/* TAB 3: Create Playlist */}
        <div className="tab-pane" id="fill-tabpanel-2" role="tabpanel" aria-labelledby="fill-tab-2">
          <section>
            <div className="px-4 py-5 px-md-5 text-center text-lg-start">
              <div className="container">
                <div className="row gx-lg-5 justify-content-center">
                  <div className="col-lg-8">
                    <div className="card">
                      <div className="card-body py-4 px-md-5">
                        <h3>Create New Instrumental Playlist</h3>
                        <hr />
                        <div>
                          <div className="mb-3">
                            <label htmlFor="playlistSelect" className="form-label">Select Playlist to Convert</label>
                            <select className="form-select" id="playlistSelect">
                              <option value="">Choose a playlist...</option>
                              {playlists.map((playlist) => {
                                return <option key={playlist.id} value={playlist.id}>{playlist.name}</option>
                              })}
                            </select>
                          </div>
                          <div className="mb-3">
                            <label htmlFor="newPlaylistName" className="form-label">New Playlist Name</label>
                            <input type="text" className="form-control" id="newPlaylistName" placeholder="Enter new playlist name" />
                          </div>
                          <div className="mb-3">
                            <label htmlFor="playlistDescription" className="form-label">Description (Optional)</label>
                            <textarea className="form-control" id="playlistDescription" rows="3" placeholder="Describe your instrumental playlist..."></textarea>
                          </div>
                          <button type="button" className="btn btn-success">Create Instrumental Playlist</button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
      </div>
  )
}

export default Dashboard