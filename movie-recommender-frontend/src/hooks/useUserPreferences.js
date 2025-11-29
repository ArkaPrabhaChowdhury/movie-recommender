import { useState, useEffect } from 'react';
import ApiService from '../services/api';

export const useUserPreferences = () => {
  const [userId, setUserId] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [personalizedRecommendations, setPersonalizedRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  // Initialize user ID (in real app, this would come from authentication)
  useEffect(() => {
    let storedUserId = localStorage.getItem('movie_app_user_id');
    if (!storedUserId) {
      storedUserId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('movie_app_user_id', storedUserId);
    }
    setUserId(storedUserId);
  }, []);

  // Load user profile when userId is available
  useEffect(() => {
    if (userId) {
      loadUserProfile();
    }
  }, [userId]);

  const loadUserProfile = async () => {
    if (!userId) return;
    
    try {
      setLoading(true);
      const profile = await ApiService.getUserProfile(userId);
      setUserProfile(profile);
      console.log('👤 Loaded user profile:', profile);
    } catch (error) {
      console.error('Error loading user profile:', error);
      setUserProfile(null);
    } finally {
      setLoading(false);
    }
  };

  const recordInteraction = async (contentData, action, rating = null) => {
    if (!userId || !contentData) return false;

    try {
      console.log(`📝 Recording ${action} for:`, contentData.title);
      
      const result = await ApiService.recordInteraction(userId, contentData, action, rating);
      
      // Reload profile after interaction
      setTimeout(() => loadUserProfile(), 500);
      
      return result;
    } catch (error) {
      console.error('Error recording interaction:', error);
      return false;
    }
  };

  const getPersonalizedRecommendations = async (options = {}) => {
    if (!userId) return [];

    try {
      setLoading(true);
      console.log('🎯 Getting personalized recommendations for:', userId);
      
      const response = await ApiService.getPersonalizedRecommendations(userId, options);
      
      const recommendations = response.recommendations || [];
      setPersonalizedRecommendations(recommendations);
      
      console.log(`✨ Got ${recommendations.length} personalized recommendations`);
      console.log('Personalization level:', response.personalization_level);
      
      return response;
    } catch (error) {
      console.error('Error getting personalized recommendations:', error);
      return { recommendations: [], personalization_level: 'none' };
    } finally {
      setLoading(false);
    }
  };

  // Convenience methods for different actions
  const likeContent = (contentData, rating = null) => recordInteraction(contentData, 'liked', rating);
  const dislikeContent = (contentData) => recordInteraction(contentData, 'disliked');
  const addToWatchlist = (contentData) => recordInteraction(contentData, 'watchlisted');
  const markAsWatched = (contentData, rating = null) => recordInteraction(contentData, 'watched', rating);

  return {
    userId,
    userProfile,
    personalizedRecommendations,
    loading,
    recordInteraction,
    likeContent,
    dislikeContent,
    addToWatchlist,
    markAsWatched,
    getPersonalizedRecommendations,
    loadUserProfile,
    hasPreferences: userProfile?.profile?.preferred_genres?.length > 0
  };
};
