import { API_CONFIG } from '../config/constants';

export const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

export const formatDate = (dateString) => {
  if (!dateString) return 'Unknown';
  const date = new Date(dateString);
  return date.getFullYear();
};

export const truncateText = (text, maxLength = 100) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substr(0, maxLength).trim() + '...';
};

export const getSearchDebounced = debounce((query, callback) => {
  if (query.trim().length >= API_CONFIG.MIN_SEARCH_LENGTH) {
    callback(query);
  }
}, API_CONFIG.SEARCH_DEBOUNCE_DELAY);
