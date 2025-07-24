import {
    FETCH_HCPS_REQUEST,
    FETCH_HCPS_SUCCESS,
    FETCH_HCPS_FAILURE,
    CREATE_HCP_REQUEST,
    CREATE_HCP_SUCCESS,
    CREATE_HCP_FAILURE,
    LOG_INTERACTION_REQUEST,
    LOG_INTERACTION_SUCCESS,
    LOG_INTERACTION_FAILURE,
    LOG_CHAT_INTERACTION_REQUEST,
    LOG_CHAT_INTERACTION_SUCCESS,
    LOG_CHAT_INTERACTION_FAILURE,
    ADD_CHAT_MESSAGE,
    CLEAR_CHAT_MESSAGES,
    SET_LAST_LOGGED_INTERACTION
} from '../actions/interactionActions';

const initialState = {
    hcps: [],
    loadingHCPs: false,
    errorHCPs: null,
    loadingInteraction: false,
    errorInteraction: null,
    chatMessages: [],
    loadingChatInteraction: false,
    errorChatInteraction: null,
    loggedInInteraction: null,
    lastLoggedInteraction: null,
};

const interactionReducer = (state = initialState, action) => {
    switch (action.type) {
        case FETCH_HCPS_REQUEST:
            return { ...state,
                loadingHCPs: true,
                errorHCPs: null
            };
        case FETCH_HCPS_SUCCESS:
            return { ...state,
                loadingHCPs: false,
                hcps: action.payload
            };
        case FETCH_HCPS_FAILURE:
            return { ...state,
                loadingHCPs: false,
                errorHCPs: action.payload
            };

        case CREATE_HCP_REQUEST:
            return { ...state,
                loadingHCPs: true,
                errorHCPs: null
            };
        case CREATE_HCP_SUCCESS:
            return { ...state,
                loadingHCPs: false,
                hcps: [...state.hcps, action.payload]
            };
        case CREATE_HCP_FAILURE:
            return { ...state,
                loadingHCPs: false,
                errorHCPs: action.payload
            };

        case LOG_INTERACTION_REQUEST:
            return { ...state,
                loadingInteraction: true,
                errorInteraction: null
            };
        case LOG_INTERACTION_SUCCESS:
            return { ...state,
                loadingInteraction: false,
                loggedInInteraction: action.payload
            };
        case LOG_INTERACTION_FAILURE:
            return { ...state,
                loadingInteraction: false,
                errorInteraction: action.payload
            };

        case LOG_CHAT_INTERACTION_REQUEST:
            return { ...state,
                loadingChatInteraction: true,
                errorChatInteraction: null
            };
        case LOG_CHAT_INTERACTION_SUCCESS:
            return { ...state,
                loadingChatInteraction: false,
                loggedInInteraction: action.payload
            };
        case LOG_CHAT_INTERACTION_FAILURE:
            return { ...state,
                loadingChatInteraction: false,
                errorChatInteraction: action.payload
            };

        case ADD_CHAT_MESSAGE:
            return { ...state,
                chatMessages: [...state.chatMessages, action.payload]
            };
        case CLEAR_CHAT_MESSAGES:
            return { ...state,
                chatMessages: []
            };
        case SET_LAST_LOGGED_INTERACTION: // <--- ADD THIS NEW CASE
            return {
                ...state,
                lastLoggedInteraction: action.payload // Store the full interaction object
            };

        default:
            return state;
    }
};

export default interactionReducer;