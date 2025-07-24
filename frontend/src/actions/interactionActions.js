import {
    getHCPs,
    createHCP,
    logInteraction,
    logInteractionFromChat
} from '../services/api';

export const FETCH_HCPS_REQUEST = 'FETCH_HCPS_REQUEST';
export const FETCH_HCPS_SUCCESS = 'FETCH_HCPS_SUCCESS';
export const FETCH_HCPS_FAILURE = 'FETCH_HCPS_FAILURE';

export const CREATE_HCP_REQUEST = 'CREATE_HCP_REQUEST';
export const CREATE_HCP_SUCCESS = 'CREATE_HCP_SUCCESS';
export const CREATE_HCP_FAILURE = 'CREATE_HCP_FAILURE';

export const LOG_INTERACTION_REQUEST = 'LOG_INTERACTION_REQUEST';
export const LOG_INTERACTION_SUCCESS = 'LOG_INTERACTION_SUCCESS';
export const LOG_INTERACTION_FAILURE = 'LOG_INTERACTION_FAILURE';

export const LOG_CHAT_INTERACTION_REQUEST = 'LOG_CHAT_INTERACTION_REQUEST';
export const LOG_CHAT_INTERACTION_SUCCESS = 'LOG_CHAT_INTERACTION_SUCCESS';
export const LOG_CHAT_INTERACTION_FAILURE = 'LOG_CHAT_INTERACTION_FAILURE';

export const ADD_CHAT_MESSAGE = 'ADD_CHAT_MESSAGE';
export const CLEAR_CHAT_MESSAGES = 'CLEAR_CHAT_MESSAGES';
export const SET_LAST_LOGGED_INTERACTION = 'SET_LAST_LOGGED_INTERACTION';

export const fetchHCPs = () => {
    return async (dispatch) => {
        dispatch({ type: FETCH_HCPS_REQUEST });
        try {
            const response = await getHCPs();
            dispatch({
                type: FETCH_HCPS_SUCCESS,
                payload: response.data
            });
        } catch (error) {
            dispatch({
                type: FETCH_HCPS_FAILURE,
                payload: error.message
            });
        }
    };
};

export const createHCPAction = (hcpData) => {
    return async (dispatch) => {
        dispatch({ type: CREATE_HCP_REQUEST });
        try {
            const response = await createHCP(hcpData);
            dispatch({
                type: CREATE_HCP_SUCCESS,
                payload: response.data
            });
            return response.data;
        } catch (error) {
            dispatch({
                type: CREATE_HCP_FAILURE,
                payload: error.response?.data?.detail || error.message
            });
            throw error;
        }
    };
};

export const logInteractionAction = (interactionData) => {
    return async (dispatch) => {
        dispatch({ type: LOG_INTERACTION_REQUEST });
        try {
            const response = await logInteraction(interactionData);
            dispatch({
                type: LOG_INTERACTION_SUCCESS,
                payload: response.data
            });
            dispatch({
                type: SET_LAST_LOGGED_INTERACTION,
                payload: response.data
            });
            alert('Interaction logged successfully!');
        } catch (error) {
            dispatch({
                type: LOG_INTERACTION_FAILURE,
                payload: error.message
            });
            alert(`Failed to log interaction: ${error.response?.data?.detail || error.message}`);
        }
    };
};

export const logChatInteractionAction = (chatData) => {
    return async (dispatch) => {
        dispatch({ type: LOG_CHAT_INTERACTION_REQUEST });

        try {
            const response = await logInteractionFromChat({
                raw_text_input: chatData.raw_text_input,
                hcp_name: chatData.hcp_name,
                // Ensure field names match backend expectations
                topics_discussed: chatData.topics_discussed,
                attendees: chatData.attendees,
                materials_shared: chatData.materials_shared,
                samples_distributed: chatData.samples_distributed,
                outcomes: chatData.outcomes,
                follow_up_actions: chatData.follow_up_actions
            });

            if (response.data?.interaction_object) {
                dispatch({
                    type: SET_LAST_LOGGED_INTERACTION,
                    payload: response.data.interaction_object
                });
            }

            // Add success message
            dispatch({
                type: ADD_CHAT_MESSAGE,
                payload: {
                    text: response.data?.response || "Interaction logged successfully!", // Use response.data.response
                    sender: 'ai'
                }
            });

        } catch (error) {
            dispatch({
                type: LOG_CHAT_INTERACTION_FAILURE,
                payload: error.message
            });
            dispatch({
                type: ADD_CHAT_MESSAGE,
                payload: {
                    text: `Error processing: ${error.response?.data?.detail || error.message}`,
                    sender: 'ai'
                }
            });
            alert(`Failed to process chat interaction: ${error.response?.data?.detail || error.message}`);
        }
    };
};

export const addChatMessage = (message) => ({
    type: ADD_CHAT_MESSAGE,
    payload: message,
});

export const clearChatMessages = () => ({
    type: CLEAR_CHAT_MESSAGES,
});

export const setLastLoggedInteraction = (interaction) => ({
    type: SET_LAST_LOGGED_INTERACTION,
    payload: interaction,
});