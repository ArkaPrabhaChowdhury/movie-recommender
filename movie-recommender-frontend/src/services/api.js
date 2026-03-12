import { API_CONFIG } from '../config/constants';
import ApiCache from './apiCache';

// Prune any expired entries once when the module loads
ApiCache.pruneExpired();

const SIX_HOURS_MS = 6 * 60 * 60 * 1000;
const TWELVE_HOURS_MS = 12 * 60 * 60 * 1000;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

class ApiService {
  static async request(endpoint, options = {}) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    const defaultOptions = {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Movie / TV details — cached for 24 h (rarely changes)
  static async getDetails(contentType, contentId) {
    const cacheKey = ApiCache.makeKey('details', contentType, contentId);
    const cached = ApiCache.get(cacheKey);
    if (cached) {
      console.log(`[Cache HIT] details:${contentType}/${contentId}`);
      return cached;
    }
    const data = await this.request(`/details/${contentType}/${contentId}`);
    ApiCache.set(cacheKey, data, ONE_DAY_MS);
    return data;
  }
  // Browse / discover — cached for 6 h per unique filter combo
  static async discover(filters, page = 1, userId = null) {
    const contentDescription = this.getContentDescription(filters.selectedContentType);
    const prompt = `suggest ${filters.selectedGenre} ${contentDescription} in ${filters.selectedLanguage}`;
    const payload = {
      user_id: userId,
      prompt,
      genre: filters.selectedGenre,
      language: filters.selectedLanguage,
      content_type: filters.selectedContentType,
      release_period: filters.selectedReleasePeriod,
      sort_by: filters.sortBy || 'rating',
      page
    };

    const cacheKey = ApiCache.makeKey('discover', payload);
    const cached = ApiCache.get(cacheKey);
    if (cached) {
      console.log(`[Cache HIT] discover: p${page}`, filters.selectedGenre, filters.selectedLanguage);
      return cached;
    }

    const data = await this.request(API_CONFIG.ENDPOINTS.DISCOVER, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    ApiCache.set(cacheKey, data, SIX_HOURS_MS);
    return data;
  }

  // Global search — cached for 12 h per unique query string
  static async globalSearch(query) {
    const cacheKey = ApiCache.makeKey('search', query.toLowerCase().trim());
    const cached = ApiCache.get(cacheKey);
    if (cached) {
      console.log('[Cache HIT] search:', query);
      return cached;
    }
    const data = await this.request(API_CONFIG.ENDPOINTS.SEARCH, {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
    ApiCache.set(cacheKey, data, TWELVE_HOURS_MS);
    return data;
  }

  static async aiChat(message, conversationHistory = []) {
    return this.request('/ai-chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_history: conversationHistory
      }),
    });
  }

  static async recordInteraction(userId, contentData, action, rating = null) {
    console.log('📤 Recording interaction with data:', contentData);

    // Genres can come in two formats:
    //  1. Card object from discover: genre_ids: [28, 18, ...]  (raw IDs)
    //  2. Details modal object:      genres: [{id: 18, name: "Drama"}, ...]
    let genreNames = [];
    if (contentData.genres && Array.isArray(contentData.genres) && contentData.genres.length > 0) {
      if (typeof contentData.genres[0] === 'object') {
        // Modal format: [{id, name}]
        genreNames = contentData.genres.map(g => g.name).filter(Boolean);
      } else {
        // Already strings
        genreNames = contentData.genres.filter(g => typeof g === 'string');
      }
    } else if (contentData.genre_ids && Array.isArray(contentData.genre_ids)) {
      // Card format: convert IDs to names
      genreNames = this.getGenreNames(contentData.genre_ids, contentData.content_type);
    }

    const enhancedContentData = {
      user_id: userId,
      content_id: contentData.id,
      content_type: contentData.content_type,
      title: contentData.title || contentData.name,
      action: action,
      rating: rating,

      genres: genreNames,

      // Language: prefer original_language (ISO code like "hi"), fallback to language field
      language: contentData.original_language || contentData.language || 'en',

      // Overview text — critical for TF-IDF recommendations
      overview: contentData.overview || '',

      // Additional TMDB data
      release_date: contentData.release_date || contentData.first_air_date || '',
      tmdb_rating: contentData.rating || contentData.vote_average || 0,
      popularity: contentData.popularity || 0,
      poster: contentData.poster || null,

      actors: contentData.actors || [],
      directors: contentData.directors || []
    };

    console.log('📊 Enhanced interaction data:', {
      title: enhancedContentData.title,
      language: enhancedContentData.language,
      genres: enhancedContentData.genres,
      hasOverview: !!enhancedContentData.overview
    });

    return this.request('/user/interaction', {
      method: 'POST',
      body: JSON.stringify(enhancedContentData),
    });
  }

  // Helper method to convert genre IDs to names
  static getGenreNames(genreIds, contentType) {
    if (!genreIds || !Array.isArray(genreIds)) return [];

    // Genre mapping based on TMDB
    const movieGenres = {
      28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
      80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
      14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
      9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
      10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
    };

    const tvGenres = {
      10759: "Action & Adventure", 16: "Animation", 35: "Comedy",
      80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
      10762: "Kids", 9648: "Mystery", 10763: "News", 10764: "Reality",
      10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk",
      10768: "War & Politics", 37: "Western"
    };

    const genreMap = contentType === 'tv' ? tvGenres : movieGenres;

    const genreNames = genreIds.map(id => genreMap[id]).filter(Boolean);
    console.log(`🎭 Converted genre IDs ${genreIds} to names:`, genreNames);

    return genreNames;
  }

  static async getUserProfile(userId) {
    return this.request(`/user/${userId}/profile`);
  }

  static async getWatchlist(userId) {
    return this.request(`/user/${userId}/watchlist`);
  }

  static async getHistory(userId) {
    return this.request(`/user/${userId}/history`);
  }

  static async getPersonalizedRecommendations(userId, options = {}) {
    return this.request('/user/recommendations', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        limit: options.limit || 15,
        exclude_seen: options.excludeSeen !== false,
        mood: options.mood,
        specific_request: options.specificRequest
      }),
    });
  }

  static async removeInteraction(userId, contentId, contentType, action = null) {
    let url = `/user/${userId}/interaction/${contentId}?content_type=${contentType}`;
    if (action) {
      url += `&action=${action}`;
    }
    return this.request(url, { method: 'DELETE' });
  }

  /** Fetch streaming platforms available in a region (cached 24 h). */
  static async getWatchProviders(region = 'IN') {
    const cacheKey = `watch_providers_${region}`;
    const cached = ApiCache.get(cacheKey);
    if (cached) return cached;
    const data = await this.request(`/watch/providers?region=${region}`);
    ApiCache.set(cacheKey, data, 24 * 60 * 60 * 1000);
    return data;
  }

  /** Persist a user's chosen OTT platform IDs on the backend. */
  static async saveUserSubscriptions(userId, providerIds) {
    return this.request(`/user/${userId}/subscriptions`, {
      method: 'POST',
      body: JSON.stringify(providerIds),
    });
  }

  static getContentDescription(contentType) {
    switch (contentType) {
      case 'both': return 'movies and shows';
      case 'movie': return 'movies only';
      case 'tv': return 'shows only';
      default: return 'movies and shows';
    }
  }
}

export default ApiService;
