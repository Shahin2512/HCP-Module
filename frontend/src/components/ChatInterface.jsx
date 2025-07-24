// frontend/src/components/ChatInterface.jsx
import React, {
    useState,
    useRef,
    useEffect
} from 'react';
import {
    useSelector,
    useDispatch
} from 'react-redux';
import {
    logChatInteractionAction,
    addChatMessage,
    clearChatMessages,
    fetchHCPs
} from '../actions/interactionActions';

const ChatInterface = () => {
    const dispatch = useDispatch();
    const {
        chatMessages,
        loadingChatInteraction,
        errorChatInteraction,
        hcps
    } = useSelector((state) => state.interactions);
    const [chatInput, setChatInput] = useState('');
    const [selectedHCPName, setSelectedHCPName] = useState('');
    const messagesEndRef = useRef(null);

    useEffect(() => {
        dispatch(fetchHCPs());
    }, [dispatch]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({
            behavior: "smooth"
        });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chatMessages]);

    const handleSendChat = (e) => {
        e.preventDefault();
        if (!chatInput.trim()) return;

        const correctionMatch = chatInput.match(/should be (Dr\.?\s?\w+)(?:\s+not|\s+instead of|\s+,\s+)?(Dr\.?\s?\w+)?/i);
        if (correctionMatch) {
            const correctName = correctionMatch[1];
            const incorrectName = correctionMatch[2] || selectedHCPName;
            dispatch(logChatInteractionAction({
                raw_text_input: `CORRECTION: Change ${incorrectName} to ${correctName}`,
                hcp_name: correctName
            }));
            setSelectedHCPName(correctName);
            setChatInput('');
            return;
        }

        if (!selectedHCPName) {
            dispatch(addChatMessage({
                text: "Please select an HCP from the dropdown before logging an interaction via chat.",
                sender: "ai"
            }));
            return;
        }

        // --- FIX START ---
        // Removed the .then() block, as the logic for adding AI's response is already inside the thunk.
        dispatch(logChatInteractionAction({
            raw_text_input: chatInput,
            hcp_name: selectedHCPName,
        }));
        // --- FIX END ---

        setChatInput('');
    };

    const handleHCPSelection = (e) => {
        setSelectedHCPName(e.target.value);
    };

    return (
        <div className="ai-assistant-panel">
            <div className="section-title">AI Assistant</div>
            <div style={{ marginBottom: '15px' }}>
                <label htmlFor="chat-hcp-select" style={{ display: 'block', marginBottom: '5px' }}>Select HCP for Chat:</label>
                <select
                    id="chat-hcp-select"
                    value={selectedHCPName}
                    onChange={handleHCPSelection}
                    style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                >
                    <option value="">-- Select HCP --</option>
                    {hcps.map((hcp) => (
                        <option key={hcp.id} value={hcp.name}>
                            {hcp.name}
                        </option>
                    ))}
                </select>
            </div>

            <div className="chat-messages">
                {chatMessages.length === 0 && (
                    <div style={{ color: '#888', textAlign: 'center', marginTop: '20%' }}>
                        Log interaction details here(e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.
                    </div>
                )}
                {chatMessages.map((msg, index) => (
                    <div key={index} className={`chat-message ${msg.sender}`}>
                        {msg.text}
                    </div>
                ))}
                {loadingChatInteraction && <div className="chat-message ai">AI is typing...</div>}
                {errorChatInteraction && (
                    <div className="chat-message ai" style={{ color: 'red' }}>
                        Error: {errorChatInteraction}
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSendChat} className="chat-input-container">
                <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Describe Interaction..."
                />
                <button type="submit" className="action-button">Log</button>
            </form>

            {/* AI Suggested Follow-ups (Placeholder, AI agent needs to return these) */}
            {/*
            <div className="ai-suggested-follow-ups">
                <div className="section-title">AI Suggested Follow-ups:</div>
                <ul>
                    <li>Schedule follow-up meeting in 2 weeks</li>
                    <li>Send Oncoboost Phase III PDF</li>
                    <li>Add Dr. Sharma to advisory board invite list</li>
                </ul>
            </div>
            */}
        </div>
    );
};

export default ChatInterface;