import { API_CONFIG } from '../config/constants';

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

  // Existing methods...
  static async discover(filters) {
    const contentDescription = this.getContentDescription(filters.selectedContentType);
    const prompt = `suggest ${filters.selectedGenre} ${contentDescription} in ${filters.selectedLanguage}`;
    
    return this.request(API_CONFIG.ENDPOINTS.DISCOVER, {
      method: 'POST',
      body: JSON.stringify({
        prompt,
        genre: filters.selectedGenre,
        language: filters.selectedLanguage,
        content_type: filters.selectedContentType,
        release_period: filters.selectedReleasePeriod
      }),
    });
  }

  static async globalSearch(query) {
    return this.request(API_CONFIG.ENDPOINTS.SEARCH, {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
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
    
    // Extract comprehensive content data
    const enhancedContentData = {
      user_id: userId,
      content_id: contentData.id,
      content_type: contentData.content_type,
      title: contentData.title,
      action: action,
      rating: rating,
      
      // Extract genres using genre_ids if available
      genres: contentData.genre_ids ? 
        this.getGenreNames(contentData.genre_ids, contentData.content_type) : 
        [],
      
      // Language information
      language: contentData.original_language || 'en',
      
      // Additional TMDB data
      release_date: contentData.release_date || contentData.first_air_date || '',
      tmdb_rating: contentData.rating || contentData.vote_average || 0,
      overview: contentData.overview || '',
      popularity: contentData.popularity || 0,
      
      // Placeholder for cast/crew (would need additional TMDB API calls)
      actors: contentData.actors || [],
      directors: contentData.directors || []
    };

    console.log('📊 Enhanced interaction data:', enhancedContentData);

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
