import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchHCPs, logInteractionAction, createHCPAction } from '../actions/interactionActions';
import './LogInteractionForm.css'; // Import the new CSS file

const LogInteractionForm = () => {
  const dispatch = useDispatch();
  const { hcps, loadingHCPs, lastLoggedInteraction } = useSelector((state) => state.interactions);

  const [formState, setFormState] = useState({
    hcpId: '',
    hcpName: '', // To store HCP name when selected from dropdown or newly created
    interactionType: 'Meeting',
    date: '',
    time: '',
    attendees: '',
    topicsDiscussed: '',
    materialsShared: '',
    samplesDistributed: '',
    hcpSentiment: 'Neutral',
    outcomes: '',
    followUpActions: ''
  });

  const [showCreateHCPModal, setShowCreateHCPModal] = useState(false);
  const [newHCPName, setNewHCPName] = useState('');
  const [newHCPSpecialty, setNewHCPSpecialty] = useState('');
  const [newHCPContact, setNewHCPContact] = useState('');
  const [createHCPError, setCreateHCPError] = useState(null);


  // Initialize with current date/time on component mount
  useEffect(() => {
    const now = new Date();
    const currentDate = now.toISOString().split('T')[0];
    const currentTime = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

    setFormState(prev => ({
      ...prev,
      date: currentDate,
      time: currentTime
    }));

    // Fetch HCPs once on component mount
    dispatch(fetchHCPs());
  }, [dispatch]);

  // Auto-fill from last logged interaction - REFINED LOGIC
  useEffect(() => {
    const autoFillForm = async () => {
      if (!lastLoggedInteraction) {
        return;
      }

      // Ensure HCPs are loaded before trying to find an HCP
      // This is crucial if lastLoggedInteraction updates *before* hcps are fully fetched
      if (hcps.length === 0 && !loadingHCPs) {
        // If HCPs aren't loaded and not currently loading, try fetching again
        await dispatch(fetchHCPs());
      }

      const hcp = hcps.find(h => h.id === lastLoggedInteraction.hcp_id);
      let hcpNameToUse = '';
      let hcpIdToUse = '';

      if (hcp) {
        hcpNameToUse = hcp.name;
        hcpIdToUse = String(hcp.id);
      } else if (lastLoggedInteraction.hcp_name) {
        // Fallback: If HCP not found in current list but name is present in interaction object
        // This might happen if the HCP was just created and hcps list hasn't refreshed yet
        // Or if the initial fetch was slow.
        hcpNameToUse = lastLoggedInteraction.hcp_name;
        // Attempt to find HCP by name if ID lookup failed (more robust)
        const foundHcpByName = hcps.find(h => h.name === lastLoggedInteraction.hcp_name);
        if (foundHcpByName) {
          hcpIdToUse = String(foundHcpByName.id);
        } else {
          // If still not found, leave HCP ID/Name unset, or show an alert
          console.warn(`HCP "${lastLoggedInteraction.hcp_name}" (ID: ${lastLoggedInteraction.hcp_id}) not found in current HCP list for auto-fill.`);
        }
      }

      // Helper for date formatting
      const formatDate = (dateInput) => {
          if (!dateInput) return '';
          let date;
          if (dateInput instanceof Date) {
              date = dateInput;
          } else if (typeof dateInput === 'string') {
              try {
                  date = new Date(dateInput);
                  // Check for invalid date (e.g., "invalid date" string)
                  if (isNaN(date.getTime())) {
                      return '';
                  }
              } catch (e) {
                  return '';
              }
          } else {
              return '';
          }
          return date.toISOString().split('T')[0]; // Format to YYYY-MM-DD
      };

      // Helper for time formatting
      const formatTime = (timeStr) => {
          if (!timeStr) return '';
          // Assuming timeStr is "HH:MM" or "HH:MM:SS" or "HH:MM:SS.ms"
          // We need to ensure it's "HH:MM" for the input type="time"
          const parts = timeStr.split(':');
          if (parts.length >= 2) {
              return `${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}`;
          }
          return ''; // Invalid time format
      };

      setFormState(prev => ({
        ...prev,
        hcpId: hcpIdToUse,
        hcpName: hcpNameToUse,
        interactionType: lastLoggedInteraction.interaction_type || 'Meeting',
        date: formatDate(lastLoggedInteraction.interaction_date),
        time: formatTime(lastLoggedInteraction.interaction_time),
        attendees: lastLoggedInteraction.attendees || '',
        topicsDiscussed: lastLoggedInteraction.topics_discussed || '',
        materialsShared: lastLoggedInteraction.materials_shared || '',
        samplesDistributed: lastLoggedInteraction.samples_distributed || '',
        hcpSentiment: lastLoggedInteraction.hcp_sentiment || 'Neutral',
        outcomes: lastLoggedInteraction.outcomes || '',
        followUpActions: lastLoggedInteraction.follow_up_actions || ''
      }));
    };

    // Call autofill only if lastLoggedInteraction is set or hcps change (which might resolve hcpIdToUse)
    // Avoid running if hcps are currently loading
    if (!loadingHCPs) {
      autoFillForm();
    }
    // Dependency array: re-run if lastLoggedInteraction changes, or if hcps array changes
  }, [lastLoggedInteraction, hcps, loadingHCPs, dispatch]);


  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormState(prev => ({ ...prev, [name]: value }));
  };

  const handleCreateHCPSubmit = async (e) => {
    e.preventDefault();
    setCreateHCPError(null);
    try {
      const newHCP = await dispatch(createHCPAction({
        name: newHCPName,
        specialty: newHCPSpecialty,
        contact_info: newHCPContact
      }));
      alert(`HCP '${newHCP.name}' created successfully!`);
      setShowCreateHCPModal(false);
      setNewHCPName('');
      setNewHCPSpecialty('');
      setNewHCPContact('');
      setFormState(prev => ({
        ...prev,
        hcpId: String(newHCP.id),
        hcpName: newHCP.name
      }));
      dispatch(fetchHCPs()); // Re-fetch to update the main HCP list
    } catch (error) {
      setCreateHCPError(error.message || 'Failed to create HCP.');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formState.hcpId) {
      alert("Please select an HCP or create a new one before logging an interaction.");
      return;
    }
    dispatch(logInteractionAction({
      hcp_id: parseInt(formState.hcpId),
      interaction_type: formState.interactionType,
      interaction_date: formState.date,
      interaction_time: formState.time,
      attendees: formState.attendees,
      topics_discussed: formState.topicsDiscussed,
      materials_shared: formState.materialsShared,
      samples_distributed: formState.samplesDistributed,
      hcp_sentiment: formState.hcpSentiment,
      outcomes: formState.outcomes,
      follow_up_actions: formState.followUpActions
    }));
  };

  if (loadingHCPs) return <div>Loading HCPs...</div>;

  return (
    <div style={styles.formPanel}>
        <h1 style={styles.header}>Log HCP Interaction</h1>

        {/* Interaction Details */}
        <div style={styles.section}>
            <h2 style={styles.sectionHeader}>Interaction Details</h2>
            
            <div style={styles.formRow}>
                <div style={styles.formGroupHalf}>
                    <label style={styles.label}>HCP Name</label>
                    <select
                        value={formState.hcpId}
                        onChange={(e) => {
                            const selectedId = e.target.value;
                            if (selectedId === "NEW_HCP") {
                                setShowCreateHCPModal(true);
                                setFormState(prev => ({ ...prev, hcpId: '', hcpName: '' }));
                            } else {
                                const selectedHCP = hcps.find(h => h.id === parseInt(selectedId));
                                setFormState(prev => ({ 
                                ...prev, 
                                hcpId: selectedId,
                                hcpName: selectedHCP ? selectedHCP.name : ''
                                }));
                            }
                        }}
                        style={styles.input}
                    >
                        <option value="">Search or select HCP...</option>
                        <option value="NEW_HCP" style={styles.optionNewHCP}>+ Add new HCP</option>
                        {hcps.map(hcp => (
                            <option key={hcp.id} value={hcp.id}>{hcp.name}</option>
                        ))}
                    </select>
                </div>

                <div style={styles.formGroupHalf}>
                    <label style={styles.label}>Interaction Type</label>
                    <select
                        name="interactionType"
                        value={formState.interactionType}
                        onChange={handleInputChange}
                        style={styles.input}
                    >
                        <option value="Meeting">Meeting</option>
                        <option value="Call">Call</option>
                        <option value="Email">Email</option>
                        <option value="Presentation">Presentation</option>
                    </select>
                </div>
            </div>

            <div style={styles.formRow}>
                <div style={styles.formGroupHalf}>
                    <label style={styles.label}>Date</label>
                    <input
                        type="date"
                        name="date"
                        value={formState.date}
                        onChange={handleInputChange}
                        style={styles.input}
                    />
                </div>
                <div style={styles.formGroupHalf}>
                    <label style={styles.label}>Time</label>
                    <input
                        type="time"
                        name="time"
                        value={formState.time}
                        onChange={handleInputChange}
                        style={styles.input}
                    />
                </div>
            </div>
    
            <div style={styles.formGroup}>
                <label style={styles.label}>Attendees</label>
                <input
                    type="text"
                    name="attendees"
                    value={formState.attendees}
                    onChange={handleInputChange}
                    placeholder="Enter names or search..."
                    style={styles.input}
                />
            </div>
        </div>

        {/* Topics Discussed */}
        <div style={styles.section}>
            <h2 style={styles.sectionHeader}>Topics Discussed</h2>
            <div style={styles.textareaContainer}>
                <textarea
                    name="topicsDiscussed"
                    value={formState.topicsDiscussed}
                    onChange={handleInputChange}
                    placeholder="Enter key discussion points..."
                    style={{ ...styles.input, ...styles.textarea }}
                />
                <button style={styles.voiceNoteButton} title="Summarize from Voice Note (Requires Consent)">
                  <span className="material-icons" style={styles.voiceNoteIcon}>mic</span>
                </button>
            </div>
            <div style={styles.voiceNoteText}>Summarize from Voice Note (Requires Consent)</div>
        </div>

        {/* Materials Shared / Samples Distributed */}
        <div style={styles.section}>
            <h2 style={styles.sectionHeader}>Materials Shared / Samples Distributed</h2>
            <div style={styles.formGroup}>
                <label style={styles.label}>Materials Shared</label>
                <div style={styles.inputWithButton}>
                    <input
                        type="text"
                        name="materialsShared"
                        value={formState.materialsShared}
                        onChange={handleInputChange}
                        placeholder="No materials added."
                        style={styles.input}
                    />
                    <button style={styles.searchAddButton}>Search/Add</button>
                </div>
            </div>
            <div style={styles.formGroup}>
                <label style={styles.label}>Samples Distributed</label>
                <div style={styles.inputWithButton}>
                    <input
                        type="text"
                        name="samplesDistributed"
                        value={formState.samplesDistributed}
                        onChange={handleInputChange}
                        placeholder="No samples added."
                        style={styles.input}
                    />
                    <button style={styles.searchAddButton}>Add Sample</button>
                </div>
            </div>
        </div>

        {/* HCP Sentiment */}
        <div style={styles.section}>
            <h2 style={styles.sectionHeader}>Observed/Inferred HCP Sentiment</h2>
            <div style={styles.sentimentRadios}>
                {['Positive', 'Neutral', 'Negative'].map((sentiment) => (
                <label key={sentiment} style={styles.sentimentLabel}>
                    <input
                    type="radio"
                    name="hcpSentiment"
                    value={sentiment}
                    checked={formState.hcpSentiment === sentiment}
                    onChange={handleInputChange}
                    style={styles.sentimentRadioInput}
                    />
                    {sentiment}
                </label>
                ))}
            </div>
        </div>

        {/* Outcomes */}
        <div style={styles.section}>
            <h2 style={styles.sectionHeader}>Outcomes</h2>
            <textarea
                name="outcomes"
                value={formState.outcomes}
                onChange={handleInputChange}
                placeholder="Key outcomes or agreements..."
                style={{ ...styles.input, ...styles.textarea }}
            />
        </div>

        {/* Follow-up Actions */}
        <div style={styles.section}>
            <h2 style={styles.sectionHeader}>Follow-up Actions</h2>
            <textarea
                name="followUpActions"
                value={formState.followUpActions}
                onChange={handleInputChange}
                placeholder="Enter next steps or tasks..."
                style={{ ...styles.input, ...styles.textarea }}
            />
        </div>

        {/* AI Suggested Follow-ups (from screenshot) */}
        <div style={styles.section}>
            <h2 style={styles.sectionHeader}>AI Suggested Follow-ups:</h2>
            <ul className="ai-suggested-list"> {/* Using className for external CSS */}
                <li>Schedule follow-up meeting in 2 weeks</li>
                <li>Send Oncoboost Phase III PDF</li>
                <li>Add Dr. Sharma to advisory board invite list</li>
            </ul>
        </div>


        <button
            type="submit"
            onClick={handleSubmit}
            style={styles.submitButton}
        >
            Log Interaction
        </button>
    
        {/* Create New HCP Modal */}
        {showCreateHCPModal && (
            <div style={styles.modalOverlay}> 
            <div style={styles.modalContent}> 
                <h2>Create New HCP</h2>
                {createHCPError && <p style={{ color: 'red' }}>{createHCPError}</p>}
                <form onSubmit={handleCreateHCPSubmit}>
                <div style={styles.formGroup}>
                    <label style={styles.label}>Name:</label>
                    <input
                    type="text"
                    value={newHCPName}
                    onChange={(e) => setNewHCPName(e.target.value)}
                    style={styles.input}
                    required
                    />
                </div>
                <div style={styles.formGroup}>
                    <label style={styles.label}>Specialty (Optional):</label>
                    <input
                    type="text"
                    value={newHCPSpecialty}
                    onChange={(e) => setNewHCPSpecialty(e.target.value)}
                    style={styles.input}
                    />
                </div>
                <div style={styles.formGroup}>
                    <label style={styles.label}>Contact Info (Optional):</label>
                    <input
                    type="text"
                    value={newHCPContact}
                    onChange={(e) => setNewHCPContact(e.target.value)}
                    style={styles.input}
                    />
                </div>
                <div style={styles.modalActions}> 
                    <button type="submit" style={styles.modalButton}>Create HCP</button> 
                    <button type="button" onClick={() => setShowCreateHCPModal(false)} style={{ ...styles.modalButton, backgroundColor: '#ccc' }}>Cancel</button> 
                </div>
                </form>
            </div>
            </div>
        )}
    </div>
  );
};

const styles = {
    // outerContainer and chatPanel styles are removed from here.
    // They are now managed by the parent App.jsx and ChatInterface.jsx respectively.
    formPanel: { // Left section containing the form
        flex: '2', // Takes up more space within the App.jsx's crmContainer
        padding: '25px', // Form content padding
        backgroundColor: '#ffffff', // White background for the form side
        overflowY: 'auto', // Scroll if content is too long
    },
    
    header: {
        fontSize: '22px', 
        borderBottom: '1px solid #eee',
        paddingBottom: '15px',
        marginBottom: '20px',
        color: '#333',
        fontWeight: '600',
    },
    section: {
        marginBottom: '25px', 
        paddingBottom: '20px',
        borderBottom: '1px solid #f0f0f0', 
    },
    sectionHeader: {
        fontSize: '16px', 
        marginBottom: '12px',
        color: '#555',
        fontWeight: 'bold',
    },
    formRow: {
        display: 'flex',
        gap: '20px',
        marginBottom: '15px',
    },
    formGroupHalf: {
        flex: 1,
    },
    formGroup: {
        marginBottom: '15px'
    },
    label: {
        display: 'block',
        marginBottom: '6px', 
        fontWeight: 'bold',
        fontSize: '13px', 
        color: '#444',
    },
    input: {
        width: '100%',
        padding: '9px 12px', 
        border: '1px solid #ced4da', 
        borderRadius: '4px',
        boxSizing: 'border-box',
        fontSize: '14px',
        color: '#333',
        backgroundColor: '#fdfdff', 
    },
    textarea: {
        minHeight: '100px',
        resize: 'vertical',
    },
    submitButton: {
        backgroundColor: '#28a745', 
        color: 'white',
        padding: '12px 25px', 
        border: 'none',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '16px',
        marginTop: '20px',
        fontWeight: 'bold',
        boxShadow: '0 2px 5px rgba(40,167,69,0.2)',
    },
    inputWithButton: {
      display: 'flex',
      gap: '10px',
    },
    searchAddButton: {
      backgroundColor: '#f0f2f5', 
      color: '#555',
      padding: '8px 12px',
      border: '1px solid #dee2e6',
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: '12px',
      whiteSpace: 'nowrap', 
    },
    sentimentRadios: {
      display: 'flex',
      gap: '25px', 
    },
    sentimentLabel: {
      display: 'flex',
      alignItems: 'center',
      fontSize: '14px',
      color: '#333',
    },
    sentimentRadioInput: {
      marginRight: '8px',
      transform: 'scale(1.1)', 
    },
    textareaContainer: {
        position: 'relative',
        marginBottom: '5px',
    },
    voiceNoteButton: {
      position: 'absolute',
      top: '8px', 
      right: '8px', 
      backgroundColor: 'transparent',
      border: 'none',
      cursor: 'pointer',
      padding: '4px',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'background-color 0.2s ease',
    },
    voiceNoteIcon: {
        fontSize: '18px',
        color: '#6c757d', 
    },
    voiceNoteText: {
        fontSize: '12px',
        color: '#6c757d',
        marginTop: '5px',
        textAlign: 'right',
        cursor: 'pointer',
    },
    aiSuggestedList: {
        // This object is technically not needed here anymore as all its styles are in CSS.
        // Keeping it as a placeholder just in case, but its properties are commented out
        // in the LogInteractionForm.css.
    },
    modalOverlay: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000,
    },
    modalContent: {
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '8px',
        width: '450px',
        boxShadow: '0 8px 16px rgba(0, 0, 0, 0.2)',
        position: 'relative',
    },
    modalActions: {
        marginTop: '25px',
        display: 'flex',
        justifyContent: 'flex-end',
        gap: '10px',
    },
    modalButton: {
        padding: '10px 20px',
        border: 'none',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '15px',
        fontWeight: 'bold',
        transition: 'background-color 0.2s ease',
    },
    optionNewHCP: {
      fontWeight: 'bold',
      color: '#007bff',
    },
};

export default LogInteractionForm;