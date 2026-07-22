import React, { useState, useRef, useEffect } from 'react';

const ChatInterface = ({ patientData, onSendMessage, loading }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
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
      const { age, chas_tier, symptoms, comorbidities, prior_admissions } = patientData.form;
      if (age) contextParts.push(`Age: ${age}`);
      if (chas_tier) contextParts.push(`CHAS Tier: ${chas_tier}`);
      if (symptoms && symptoms.length > 0) contextParts.push(`Symptoms: ${symptoms.join(', ')}`);
      if (comorbidities) contextParts.push(`Comorbidities: ${comorbidities}`);
      if (prior_admissions) contextParts.push(`Prior Admissions: ${prior_admissions}`);
    }
    
    return contextParts.join('\n');
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    // Context is now built in App.jsx handleSendMessage using patientData state
    // Pass empty context since the actual context is constructed from patientData there
    try {
      const response = await onSendMessage({}, input);
      const aiMessage = { role: 'assistant', content: response.response || response.message || 'No response received' };
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
