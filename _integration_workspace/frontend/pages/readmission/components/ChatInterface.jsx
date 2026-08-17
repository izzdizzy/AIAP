import React, { useState, useRef, useEffect } from 'react';

/**
 * Simple markdown renderer for assistant messages.
 * Converts a subset of markdown to HTML safely.
 * 
 * Features (applied in fixed order after escaping):
 * 1. Escapes HTML entities first (& < > " ')
 * 2. {red: text}, {amber: text}, {green: text} -> coloured spans (whitelist only)
 * 3. **bold** -> <strong>
 * 4. *italic* -> <em>
 * 5. [text](url) -> <a href="..." target="_blank" rel="noopener noreferrer">
 *   Only allows http:// and https:// URLs (blocks javascript: and other schemes)
 * 6. "- " lines -> bullet list items
 * 7. "1. " lines -> numbered list items
 * 8. "### " -> <h4> heading
 * 9. Blank line -> paragraph break
 * 
 * @param {string} markdown - The markdown text to render
 * @returns {string} - Safe HTML string
 */
function renderMarkdown(markdown) {
  try {
    if (!markdown || typeof markdown !== 'string') {
      return '';
    }

    let html = markdown;

    // Step 1: Escape HTML entities to prevent XSS
    html = html
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');

    // Step 2: Convert colour emphasis {red: text}, {amber: text}, {green: text}
    // Only these three colours are allowed - any other colour name renders as plain text
    // This must run AFTER escaping but BEFORE other markdown conversions
    html = html.replace(/\{red:\s*([^}]+)\}/g, '<span class="chat-red">$1</span>');
    html = html.replace(/\{amber:\s*([^}]+)\}/g, '<span class="chat-amber">$1</span>');
    html = html.replace(/\{green:\s*([^}]+)\}/g, '<span class="chat-green">$1</span>');

    // Step 3: Convert markdown links [text](url) to HTML anchors
    // Only allow http:// and https:// URLs for security
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
      const trimmedUrl = url.trim();
      // Only allow http:// and https:// URLs
      if (trimmedUrl.startsWith('http://') || trimmedUrl.startsWith('https://')) {
        return `<a href="${trimmedUrl}" target="_blank" rel="noopener noreferrer">${text}</a>`;
      } else {
        // Block javascript:, data:, and other potentially dangerous schemes
        // Return just the link text (no parentheses)
        return text;
      }
    });

    // Step 4: Convert **bold** to <strong>
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Step 5: Convert *italic* to <em>
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Step 6: Convert ### headings to <h4>
    html = html.replace(/^### (.+)$/gm, '<h4 class="text-lg font-semibold mt-4 mb-2">$1</h4>');

    // Step 7: Convert bullet lists "- " to <li>
    html = html.replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>');

    // Step 8: Convert numbered lists "1. " to <li>
    html = html.replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>');

    // Step 9: Convert blank lines to paragraph breaks
    // Split by double newlines and wrap non-empty paragraphs
    const paragraphs = html.split(/\n\n+/);
    html = paragraphs.map(para => {
      const trimmed = para.trim();
      if (!trimmed) return '';
      // Don't wrap if already wrapped in block elements
      if (trimmed.startsWith('<h4') || trimmed.startsWith('<li') || trimmed.startsWith('<ul') || trimmed.startsWith('<ol')) {
        return trimmed;
      }
      return `<p class="mb-2">${trimmed.replace(/\n/g, '<br/>')}</p>`;
    }).join('');

    return html;
  } catch (error) {
    // Fallback: return escaped plain text if anything fails
    console.error('Markdown rendering failed:', error);
    try {
      return String(markdown)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
    } catch {
      return 'Error rendering message';
    }
  }
}

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
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isWaitingForResponse]);

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
    
    // Add typing indicator bubble inside the chat stream
    setIsWaitingForResponse(true);
    const typingMessageId = Date.now();
    setMessages(prev => [...prev, { role: 'typing', id: typingMessageId }]);

    try {
      const response = await onSendMessage({}, input);
      
      // Remove typing indicator and add actual AI response
      setMessages(prev => prev.filter(msg => msg.id !== typingMessageId));
      const aiMessage = { role: 'assistant', content: response.response || response.message || 'No response received' };
      
      // Check if response indicates fallback mode (offline protocols)
      if (response.is_fallback || (response.response && response.response.includes('[System Note: Operating on offline clinical protocols'))) {
        setFallbackMode(true);
      }
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      // Remove typing indicator and show error
      setMessages(prev => prev.filter(msg => msg.id !== typingMessageId));
      const errorMessage = { role: 'assistant', content: 'Error: Unable to get a response from the AI service.' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsWaitingForResponse(false);
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
              {/* Render assistant messages with markdown, user messages as plain text */}
              {msg.role === 'assistant' ? (
                <p 
                  className="text-sm prose prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                />
              ) : msg.role === 'typing' ? (
                // Typing indicator with animated three dots (pure CSS animation)
                <div className="typing-indicator">
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                </div>
              ) : (
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              )}
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
