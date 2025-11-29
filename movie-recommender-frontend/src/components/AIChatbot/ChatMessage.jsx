const ChatMessage = ({ message }) => {
  const isUser = message.type === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-lg p-3 ${
        isUser 
          ? 'bg-blue-600 text-white' 
          : message.isError 
            ? 'bg-red-900 text-red-100'
            : 'bg-gray-800 text-gray-100'
      }`}>
        {/* Message content */}
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        
        {/* Show accurate recommendations count for AI messages */}
        {!isUser && message.recommendations && message.recommendations.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-600">
            <p className="text-xs text-gray-400">
              🎬 Found {message.recommendations.length} recommendations
            </p>
          </div>
        )}
        
        {/* Timestamp */}
        <p className="text-xs opacity-70 mt-1">
          {message.timestamp.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </p>
      </div>
    </div>
  );
};

export default ChatMessage;
