import React, { useState, useRef, useEffect } from 'react';

/**
 * ChatInterface Component - Care Navigation Assistant (Gen AI)
 * 
 * CONDITIONAL RENDERING LOGIC:
 * - The chat interface is LOCKED (disabled with tooltip) until valid patient data exists
 * - Valid patient data requires: successful CSV/XLSX upload OR completed form submission
 * - This ensures the Gen AI assistant only activates when proper patient context is available
 * 
 * @param {Object} props
 * @param {Object} props.patientData - Patient data including form and prediction results
 * @param {Function} props.onSendMessage - Callback to send message to Gen AI backend
 * @param {boolean} props.loading - Loading state for API calls
 * @param {boolean} props.isLocked - Whether the chat should be locked (no valid patient data)
 */
const ChatInterface = ({ patientData, onSendMessage, loading, isLocked = false }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [fallbackMode, setFallbackMode] = useState(false);
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const buildContext = () => {
    if (!patientData) return '';
    
    const contextParts = [];
    
    if (patientData.prediction) {
      const { clinical_severity_score, urgency_level, raw_probability, risk_category } = patientData.prediction;
      contextParts.push(`Clinical Severity Score: ${clinical_severity_score}/100`);
      contextParts.push(`Urgency Level: ${urgency_level}`);
      contextParts.push(`Risk Category: ${risk_category}`);
      contextParts.push(`Readmission Probability: ${(raw_probability * 100).toFixed(1)}%`);
    }
    
    if (patientData.form) {
      const { age, chas_tier, symptoms, comorbidities, prior_admissions, num_medications } = patientData.form;
      if (age) contextParts.push(`Age: ${age}`);
      if (chas_tier) contextParts.push(`CHAS Tier: ${chas_tier}`);
      if (symptoms && symptoms.length > 0) contextParts.push(`Symptoms: ${symptoms.join(', ')}`);
      if (comorbidities) contextParts.push(`Comorbidities: ${comorbidities}`);
      if (prior_admissions) contextParts.push(`Prior Admissions: ${prior_admissions}`);
      if (num_medications) contextParts.push(`Medications: ${num_medications}`);
    }
    
    return contextParts.join('\n');
  };

  const handleSend = async () => {
    if (!input.trim() || isLocked) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const response = await onSendMessage({}, input);
      const aiMessage = { role: 'assistant', content: response.response || response.message || 'No response received' };
      
      // Check if response indicates fallback mode (offline protocols)
      if (response.is_fallback || (response.response && response.response.includes('[System Note: Operating on offline clinical protocols'))) {
        setFallbackMode(true);
      }
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = { role: 'assistant', content: 'Error: Unable to get a response from the AI service.' };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Render locked state when no valid patient data exists
  if (isLocked) {
    return (
      <div className="flex flex-col h-full bg-gray-800 rounded-lg shadow-lg border border-gray-700 items-center justify-center p-8 text-center">
        <div className="bg-gray-700/50 p-6 rounded-lg max-w-md">
          <svg className="w-12 h-12 mx-auto text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-300 mb-2">Care Navigation Assistant Locked</h3>
          <p className="text-sm text-gray-400 mb-4">
            The AI Care Navigation Assistant requires patient data to provide personalized recommendations.
          </p>
          <p className="text-xs text-gray-500">
            Please upload a patient CSV/XLSX file or manually enter patient information in the Risk Assessment tab to unlock this feature.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-800 rounded-lg shadow-lg border border-gray-700">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-8">
            <p>Start a conversation about this patient's care plan.</p>
            <p className="text-sm mt-2">Patient context is automatically included.</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-2 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-100'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-700 p-4">
        {/* Fallback Mode Warning Banner */}
        {fallbackMode && (
          <div className="mb-3 p-2 bg-yellow-900/30 border border-yellow-700 rounded-md">
            <p className="text-xs text-yellow-300">
              Live Gen AI disabled. Displaying standard care protocols.
            </p>
          </div>
        )}
        
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about care recommendations..."
            className="flex-1 px-4 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
