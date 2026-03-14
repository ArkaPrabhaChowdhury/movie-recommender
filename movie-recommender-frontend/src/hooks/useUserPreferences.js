import { useState, useEffect } from 'react';
import ApiService from '../services/api';
import ApiCache from '../services/apiCache';
import { supabase } from '../services/supabaseClient';


export const useUserPreferences = () => {
  const [userId, setUserId] = useState(null);
  const [userName, setUserName] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [personalizedRecommendations, setPersonalizedRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  // Initialize user ID from Supabase Auth, fallback to anonymous local storage
  useEffect(() => {
    const setAnonymousId = () => {
      let storedUserId = localStorage.getItem('movie_app_user_id');
      if (!storedUserId) {
        storedUserId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('movie_app_user_id', storedUserId);
      }
      setUserId(storedUserId);
      setUserName(null);
    };

    const initializeAuth = async () => {
      if (!supabase) {
        setAnonymousId();
        return;
      }

      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user) {
        setUserId(session.user.id);
        const fullName = session.user.user_metadata?.full_name || session.user.email?.split('@')[0];
        setUserName(fullName);
      } else {
        setAnonymousId();
      }

      const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
        if (session?.user) {
          setUserId(session.user.id);
          const fullName = session.user.user_metadata?.full_name || session.user.email?.split('@')[0];
          setUserName(fullName);
        } else {
          setAnonymousId();
          setUserProfile(null); // Clear profile on logout
        }
      });

      return () => subscription?.unsubscribe();
    };

    initializeAuth();
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

    const contentKey = `${contentData.content_type}_${contentData.id}`;
    const currentActions = userProfile?.interaction_map?.[contentKey] || [];
    const isUndoing = Array.isArray(currentActions) ? currentActions.includes(action) : currentActions === action;

    // Optimistic update for instant UI feedback
    if (userProfile) {
      setUserProfile(prev => {
        const newMap = { ...(prev?.interaction_map || {}) };
        if (isUndoing) {
          // Remove from list
          if (Array.isArray(newMap[contentKey])) {
            newMap[contentKey] = newMap[contentKey].filter(a => a !== action);
          } else {
            delete newMap[contentKey];
          }
        } else {
          // Add to list
          if (!Array.isArray(newMap[contentKey])) {
            newMap[contentKey] = [];
          }
          if (!newMap[contentKey].includes(action)) {
            newMap[contentKey] = [...newMap[contentKey], action];
          }
        }
        return {
          ...prev,
          interaction_map: newMap
        };
      });
    }

    try {
      if (isUndoing) {
        console.log(`🗑️ Removing ${action} (undo) for:`, contentData.title);
        await ApiService.removeInteraction(userId, contentData.id, contentData.content_type, action);
      } else {
        console.log(`📝 Recording ${action} for:`, contentData.title);
        await ApiService.recordInteraction(userId, contentData, action, rating);
      }

      // Reload full profile to sync everything (stats, recent_activity, etc)
      await loadUserProfile();

      return true;
    } catch (error) {
      console.error(`Error ${isUndoing ? 'removing' : 'recording'} interaction:`, error);
      // Revert optimistic update by reloading
      await loadUserProfile();
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

  const updateSubscriptions = async (providerIds) => {
    if (!userId) return false;
    // Optimistic update
    setUserProfile(prev => prev ? {
      ...prev,
      profile: { ...prev.profile, subscribed_providers: providerIds }
    } : prev);
    try {
      await ApiService.saveUserSubscriptions(userId, providerIds);
      // Bust discover cache so home page re-fetches with the new filter
      ApiCache.clear();
      return true;
    } catch (err) {
      console.error('Failed to save subscriptions:', err);
      loadUserProfile(); // revert
      return false;
    }
  };

  return {
    userId,
    userName,
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
    updateSubscriptions,
    hasPreferences: userProfile?.profile?.preferred_genres?.length > 0
  };
};
