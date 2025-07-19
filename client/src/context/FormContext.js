import {createContext, useReducer} from 'react';

const formContext = createContext();

// np stands for new playlist creation data
// op stands for old playlist
// queries are the song name plus the artist
let formData = {
  op_id: null,
  np_name: null,
  np_description: null,
  np_collaborative: true,
  np_public: false,
  np_queries: []
}

const PlaylistDataProvider = ({children}) => {
    const reducer = (state, action) => {
        switch (action.type) {
            case 'SELECT_PLAYLIST':
                console.log(state);
                return {
                    ...state,
                    np_name: action.next_np_name,
                    op_id: action.next_op_id
                }
            // the queries are currently song_name + song_artist
            case 'UPDATE_NAME':
                return {
                    ...state,
                    np_name: action.next_np_name
                }
            case 'SET_QUERIES':
                return {
                    ...state,
                    np_queries: action.next_np_queries
                }
            case 'ADD_QUERY':
                let queries = [...state.np_queries];
                queries.push(action.next_np_query);
                return {
                    ...state,
                    np_queries: queries
                }
            case 'REMOVE_QUERY':
                return {
                    ...state,
                    np_queries: state.np_queries.filter((query)=> {
                        return !(query === action.remove_np_query)  
                    })
                }
            case 'UPDATE_DESCRIPTION':
                return {
                    ...state,
                    np_description: action.next_np_description
                }
            case 'UPDATE_PUBLICITY':
                return {
                    ...state,
                    np_public: action.next_np_public
                }
            case 'UPDATE_COLLAB':
                return {
                    ...state,
                    np_collaborative: action.next_np_collab
                }
        }
    }
    const [state, dispatch] = useReducer(reducer, formData);
    return (
        <formContext.Provider value = {{state, dispatch}}>
            {children}
        </formContext.Provider>
    )
}

export {PlaylistDataProvider};
export default formContext;

