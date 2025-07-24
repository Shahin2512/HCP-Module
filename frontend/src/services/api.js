import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const getHCPs = () => api.get('/hcps');
export const createHCP = (hcpData) => api.post('/hcps/', hcpData);
export const logInteraction = (interactionData) => api.post('/interactions/', interactionData);
export const logInteractionFromChat = (chatData) => api.post('/interactions/chat', chatData);
export const getInteractions = () => api.get('/interactions');