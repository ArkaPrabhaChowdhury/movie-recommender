// Frontend Configuration Constants

// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || (import.meta.env.MODE === 'production' ? '/api' : 'http://127.0.0.1:8000'),
  ENDPOINTS: {
    DISCOVER: '/discover',
    SEARCH: '/search',
    HEALTH: '/health'
  },
  SEARCH_DEBOUNCE_DELAY: 500,
  MIN_SEARCH_LENGTH: 2
};

// UI Configuration
export const UI_CONFIG = {
  APP_NAME: 'OTT SCOUT',
  GRID_BREAKPOINTS: {
    SM: 'sm:grid-cols-3',
    MD: 'md:grid-cols-4',
    LG: 'lg:grid-cols-5',
    XL: 'xl:grid-cols-6'
  },
  ANIMATION_DURATION: {
    FAST: '200',
    NORMAL: '300',
    SLOW: '500'
  }
};

// Content Configuration
export const LANGUAGES = [
  { id: 'any', name: 'Any' },
  { id: 'hindi', name: 'Hindi' },
  { id: 'english', name: 'English' },
  { id: 'tamil', name: 'Tamil' },
  { id: 'telugu', name: 'Telugu' },
];

export const GENRES = ['All', 'Action', 'Comedy', 'Drama', 'Thriller', 'Romance', 'Horror', 'Sci-Fi'];

export const CONTENT_TYPES = [
  { id: 'both', name: 'All' },
  { id: 'movie', name: 'Movies' },
  { id: 'tv', name: 'TV Shows' },
];

export const RELEASE_PERIODS = [
  { id: '6months', name: 'Last 6 months', months: 6 },
  { id: '1year', name: 'Last 1 year', months: 12 },
  { id: '2years', name: 'Last 2 years', months: 24 },
  { id: '3years', name: 'Last 3 years', months: 36 },
  { id: 'all', name: 'All time', months: null },
];

export const SORT_OPTIONS = [
  { id: 'rating', name: 'Rating' },
  { id: 'release_date', name: 'Date' },
];

// Default Values
export const DEFAULTS = {
  LANGUAGE: 'any',
  GENRE: 'all',
  CONTENT_TYPE: 'both',
  RELEASE_PERIOD: '6months',
  SORT_BY: 'Date'
};

// CSS Classes & Inline Styles
export const STYLES = {
  FILTER_BUTTON: {
    BASE: 'px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
    ACTIVE: 'text-white shadow-lg',
    INACTIVE: 'hover:text-white',
    // Inline style functions for dynamic colors
    getActiveStyle: () => ({
      background: 'var(--color-primary-600)',
      color: 'white',
    }),
    getInactiveStyle: () => ({
      background: 'var(--color-bg-card)',
      color: 'var(--color-text-secondary)',
    }),
    getHoverStyle: () => ({
      background: 'var(--color-bg-card-hover)',
      color: 'var(--color-text-primary)'
    })
  },
  COLORS: {
    PRIMARY: 'bg-teal-600 shadow-teal-600/25',
    SECONDARY: 'bg-blue-600 shadow-blue-600/25',
    SUCCESS: 'bg-green-600',
    WARNING: 'bg-yellow-600',
    DANGER: 'bg-teal-600'
  }
};

// Utility Functions
export const getContentDescription = (contentType) => {
  switch (contentType) {
    case 'both': return 'movies and shows';
    case 'movie': return 'movies only';
    case 'tv': return 'shows only';
    default: return 'movies and shows';
  }
};

export const isRecentRelease = (year) => {
  const currentYear = new Date().getFullYear();
  const releaseYear = parseInt(year);
  return currentYear - releaseYear <= 1;
};

export const getLanguageName = (code) => {
  if (!code) return 'Any';
  const lang = LANGUAGES.find(l => l.id.toLowerCase() === code.toLowerCase() || (code.length === 2 && l.id === code));
  if (lang) return lang.name;
  
  // Extra mapping for common ISO codes
  const isoMap = {
    'en': 'English',
    'hi': 'Hindi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ml': 'Malayalam',
    'kn': 'Kannada'
  };
  return isoMap[code.toLowerCase()] || code.charAt(0).toUpperCase() + code.slice(1);
};
