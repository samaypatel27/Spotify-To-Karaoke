import React, {useState, useEffect, useContext} from 'react';
import axios from 'axios';
import formContext from "../context/FormContext.js";
import {useNavigate} from "react-router-dom";

const Create = () => {
    useEffect(() => {
        // Load Google Identity Services
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);

        script.onload = () => {
            // Initialize Google Identity Services
            window.google.accounts.id.initialize({
                client_id: '582096807393-bvs6akh56olvna85fat0run1vuuv63mc.apps.googleusercontent.com'
            });
        };

        return () => {
            // Cleanup
            document.head.removeChild(script);
        };
    }, []);

    const {state, dispatch} = useContext(formContext);
    const navigate = useNavigate();

    const updateName = (e) => {
        let name = e.target.value;
        dispatch({
            type: 'UPDATE_NAME',
            next_np_name: name
        })
    }

    const updateDescription = (e) => {
        let description = e.target.value;
        dispatch({
            type: 'UPDATE_DESCRIPTION',
            next_np_description: description
        })
    }

    const updateVisability = (e) => {
        let isPublic = !(e.target.checked);
        dispatch({
            type: 'UPDATE_VISABILITY',
            next_np_visability: isPublic
        })
    }

    const updateCollab = (e) => {
        let isCollab = e.target.checked
        dispatch({
            type: 'UPDATE_COLLAB',
            np_next_collab: isCollab
        })
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        // Use Google Identity Services for OAuth
        const client = window.google.accounts.oauth2.initTokenClient({
            client_id: '582096807393-bvs6akh56olvna85fat0run1vuuv63mc.apps.googleusercontent.com',
            scope: 'https://www.googleapis.com/auth/youtube',
            callback: (response) => {
                if (response.error) {
                    console.error('YouTube login failed:', response.error);
                    return;
                }
                
                // Store the access token
                sessionStorage.setItem('youtubeToken', response.access_token);
                navigate("/user/process");
                
                // Redirect to next page
                // window.location.href = '/next-page';
                // OR if using React Router: navigate('/next-page');
            }
        });
        
        // Request access token
        client.requestAccessToken();

    }
    
    
    return (
        <form id = "createForm" onSubmit = {handleSubmit}>
            <div className = "col-12 mb-2">
                    <div className = "d-flex flex-column align-items-center gap-1 p-2 bg-light bg-opacity-25 rounded text-center">
                      <h3>Fill Out Required Fields</h3>
                      <button onSubmit = {handleSubmit} type = "submit" className= {` w-25 btn btn-primary ${(state.np_name && state.np_description && state.np_queries.length > 0) || `disabled`}`} tabindex="-1" aria-disabled= {`${(state.np_name && state.np_description && state.np_queries.length > 0) ? `false` : `true`}`}>Create</button>
                    </div>
            </div>
                <div className="py-5 text-center text-lg-start">
                <div className="container">
                    <div className="row justify-content-center">
                    <div className="col-md-8 col-lg-6">
                        <div className="border p-3 rounded bg-light bg-opacity-25">
                            <div className="mb-3">
                                <label htmlFor="formName" className="form-label">Playlist Name</label>
                                <input defaultValue= {state.np_name + ' - insturmental'} onChange = {updateName} className="form-control" id="formName" aria-describedby="emailHelp"></input>
                            </div>
                            <div className="mb-3">
                                <label htmlFor="formDescription" className = "form-label">Description</label>
                                <textarea onChange = {updateDescription} className="form-control" id="formDescription"></textarea>
                            </div>
                            <div className = "mb-3 d-flex justify-content-between">
                                <div class="form-check form-switch">
                                    <input onChange = {updateVisability} className="form-check-input" type="checkbox" role="switch" id="toggleVisability" defaultChecked></input>
                                    <label className="form-check-label" for="toggleVisability">Make Private</label>  
                                </div>
                                <div class="form-check form-switch">
                                    <input onChange = {updateCollab} className="form-check-input" type="checkbox" role="switch" id="toggleCollaborative" defaultChecked></input>
                                    <label className="form-check-label" for="toggleCollaborative">Allow Collaborations</label>  
                                </div> 
                            </div>
                            <div class="mb-3 form-check">
                                <input class="form-check-input" type="checkbox" value="" id="flexCheckDefault"></input>
                                <label class="form-check-label" for="flexCheckDefault">
                                    Add Custom Playlist Profile
                                </label>
                            </div>
                            <div class="mb-3 ">
                                <label for="formFileDisabled" class="form-label"></label>
                                <input class="form-control" type="file" id="formFileDisabled" disabled></input>
                            </div>
                        </div>
                         
                    </div>
                    </div>
                </div>
                </div>
        </form>
    )

}
export default Create;