import ChatMessage from './ChatMessage';

export default function ChatWindow({
  messages,
  loading,
  messagesEndRef
}) {
  return (
    <div className="chat-window">
      {messages.map((message, index) => (
        <ChatMessage
          key={index}
          role={message.role}
          content={message.content}
        />
      ))}

      {loading && (
        <ChatMessage
          role="assistant"
          content="Thinking..."
        />
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}