import { useState } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { useAIChat } from '../../hooks/useAIChat';

const ChatBot = ({ onRecommendationsReceived }) => {
  const {
    isChatOpen,
    chatMessages,
    chatLoading,
    sendMessage,
    clearChat,
    toggleChat
  } = useAIChat();

  const handleSendMessage = async (message) => {
    const response = await sendMessage(message);

    // If we get recommendations, pass them up to parent
    if (response && response.recommendations && response.recommendations.length > 0) {
      onRecommendationsReceived(response.recommendations, response.ai_response);
    }
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={toggleChat}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg transition-all duration-300"
        style={{
          background: isChatOpen ? 'var(--color-accent-500)' : 'var(--color-primary-600)',
          transform: isChatOpen ? 'rotate(45deg)' : 'none'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = isChatOpen ? 'var(--color-accent-600)' : 'var(--color-primary-700)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = isChatOpen ? 'var(--color-accent-500)' : 'var(--color-primary-600)';
        }}
      >
        {isChatOpen ? (
          <span className="text-white text-2xl">✕</span>
        ) : (
          <span className="text-white text-2xl">🤖</span>
        )}
      </button >

      {/* Chat Window */}
      {
        isChatOpen && (
          <div className="fixed bottom-24 right-6 z-40 w-96 h-[500px] rounded-lg shadow-2xl flex flex-col" style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border-primary)' }}>
            {/* Chat Header */}
            <div className="p-4 border-b flex justify-between items-center" style={{ borderColor: 'var(--color-border-primary)' }}>
              <div>
                <h3 className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>AI Movie Assistant</h3>
                <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Ask me what you want to watch!</p>
              </div>
              <button
                onClick={clearChat}
                className="text-sm transition-colors"
                style={{ color: 'var(--color-text-tertiary)' }}
                onMouseEnter={(e) => e.target.style.color = 'var(--color-text-primary)'}
                onMouseLeave={(e) => e.target.style.color = 'var(--color-text-tertiary)'}
              >
                Clear
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.length === 0 && (
                <div className="text-center mt-8" style={{ color: 'var(--color-text-tertiary)' }}>
                  <p className="mb-2">👋 Hi! I'm your AI movie assistant.</p>
                  <p className="text-sm">Try saying things like:</p>
                  <div className="mt-2 space-y-1 text-xs">
                    <p>"I want to laugh but also cry a little"</p>
                    <p>"Show me something dark and psychological"</p>
                    <p>"I need motivation"</p>
                  </div>
                </div>
              )}

              {chatMessages.map((message, index) => (
                <ChatMessage key={index} message={message} />
              ))}

              {chatLoading && (
                <div className="flex items-center space-x-2" style={{ color: 'var(--color-text-secondary)' }}>
                  <div className="animate-spin rounded-full h-4 w-4 border-2" style={{ borderColor: 'var(--color-primary-500)', borderTopColor: 'transparent' }}></div>
                  <span className="text-sm">AI is thinking...</span>
                </div>
              )}
            </div>

            {/* Chat Input */}
            <ChatInput onSendMessage={handleSendMessage} disabled={chatLoading} />
          </div>
        )
      }
    </>
  );
};

export default ChatBot;
