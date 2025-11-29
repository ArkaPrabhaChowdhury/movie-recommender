import { useState } from 'react';
import ApiService from '../services/api';

export const useAIChat = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);

  const sendMessage = async (message) => {
    if (!message.trim()) return null;

    const userMessage = { 
      type: 'user', 
      content: message.trim(), 
      timestamp: new Date() 
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setChatLoading(true);

    try {
      const response = await ApiService.aiChat(message, conversationHistory);
      
      // Log what we received from backend
      console.log('🎯 Frontend received from backend:');
      console.log('  - AI Response:', response.ai_response);
      console.log('  - Recommendations count:', response.recommendations?.length || 0);
      if (response.recommendations && response.recommendations.length > 0) {
        const titles = response.recommendations.map(item => item.title);
        console.log('  - Titles received:', titles);
      }
      
      const aiMessage = {
        type: 'ai',
        content: response.ai_response,
        timestamp: new Date(),
        recommendations: response.recommendations || [],
        queryAnalysis: response.query_analysis || {}
      };

      setChatMessages(prev => [...prev, aiMessage]);
      setConversationHistory(response.conversation_context || []);
      
      return response;
    } catch (error) {
      console.error('Error in AI chat:', error);
      
      const errorMessage = {
        type: 'ai',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        isError: true
      };
      
      setChatMessages(prev => [...prev, errorMessage]);
      return null;
    } finally {
      setChatLoading(false);
    }
  };

  const clearChat = () => {
    setChatMessages([]);
    setConversationHistory([]);
  };

  const toggleChat = () => {
    setIsChatOpen(prev => !prev);
  };

  return {
    isChatOpen,
    chatMessages,
    chatLoading,
    sendMessage,
    clearChat,
    toggleChat,
    conversationHistory
  };
};
