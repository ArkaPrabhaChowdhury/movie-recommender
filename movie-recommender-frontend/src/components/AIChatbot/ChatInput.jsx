import { useState, useRef } from 'react';

const ChatInput = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input);
      setInput('');
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700">
      <div className="flex space-x-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me what you want to watch..."
          disabled={disabled}
          rows={2}
          className="flex-1 px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50 resize-none text-sm"
        />
        <button
          type="submit"
          disabled={!input.trim() || disabled}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-md text-white text-sm font-medium transition-colors"
        >
          Send
        </button>
      </div>
      
      {/* Quick suggestion buttons */}
      <div className="flex flex-wrap gap-1 mt-2">
        {[
          "I want to laugh but cry a little",
          "Something dark & psychological", 
          "Family movie night",
          "I need motivation"
        ].map((suggestion, index) => (
          <button
            key={index}
            type="button"
            onClick={() => setInput(suggestion)}
            disabled={disabled}
            className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded border-gray-600 transition-colors disabled:opacity-50"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </form>
  );
};

export default ChatInput;
