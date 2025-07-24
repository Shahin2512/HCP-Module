import React from 'react';
import Header from './components/Header';
import LogInteractionForm from './components/LogInteractionForm';
import ChatInterface from './components/ChatInterface';
import './index.css'; // Import the global styles

function App() {
    return (
        <div className="app-container">
            <Header />
            {/* The crm-container now acts as the outerContainer for the two main panels */}
            <div style={appStyles.crmContainer}> 
                <LogInteractionForm /> {/* Left panel */}
                <ChatInterface />      {/* Right panel */}
            </div>
        </div>
    );
}

const appStyles = {
    crmContainer: {
        display: 'flex',
        maxWidth: '1200px', // Overall width of the module
        margin: '20px auto', // Center the module on the page
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)', // Subtle shadow
        borderRadius: '8px',
        overflow: 'hidden',
        backgroundColor: '#f8f9fa', // Overall light background for the module
        minHeight: '800px', // Minimum height for the module
    },
    // No need for formPanelWrapper or chatPanelWrapper here anymore.
    // The flex properties and background will be applied directly to the components
    // within their own styles, or directly in LogInteractionForm.jsx/ChatInterface.jsx.
};

export default App;