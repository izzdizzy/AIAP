import ReactMarkdown from 'react-markdown';

export default function ChatMessage({ role, content }) {
  const isAssistant = role === 'assistant';

  return (
    <div
      className={`chat-message ${
        isAssistant
          ? 'chat-message--assistant'
          : 'chat-message--user'
      }`}
    >
      <div className="chat-message__label">
        {isAssistant ? 'AI Assistant' : 'You'}
      </div>

      <div className="chat-message__bubble">
        <ReactMarkdown>
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}