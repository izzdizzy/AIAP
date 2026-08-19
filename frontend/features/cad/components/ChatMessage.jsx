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
        <ReactMarkdown
          components={{
            ul: ({ node, ...props }) => <ul style={{ margin: '8px 0', paddingLeft: '20px', listStyleType: 'disc' }} {...props} />,
            ol: ({ node, ...props }) => <ol style={{ margin: '8px 0', paddingLeft: '20px', listStyleType: 'decimal' }} {...props} />,
            li: ({ node, ...props }) => <li style={{ marginBottom: '4px' }} {...props} />,
            p: ({ node, ...props }) => <p style={{ margin: '6px 0', lineHeight: '1.5' }} {...props} />
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}