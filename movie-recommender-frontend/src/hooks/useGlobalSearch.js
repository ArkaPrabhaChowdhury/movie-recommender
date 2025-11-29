import { useState } from 'react';
import ApiService from '../services/api';
import { API_CONFIG } from '../config/constants';

export const useGlobalSearch = () => {
  const [globalSearchResults, setGlobalSearchResults] = useState([]);
  const [isGlobalSearch, setIsGlobalSearch] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);

  const handleGlobalSearch = async (query) => {
    const trimmedQuery = query.trim();
    
    if (trimmedQuery.length < API_CONFIG.MIN_SEARCH_LENGTH) {
      setIsGlobalSearch(false);
      setGlobalSearchResults([]);
      return;
    }

    setSearchLoading(true);
    setIsGlobalSearch(true);

    try {
      const data = await ApiService.globalSearch(trimmedQuery);
      setGlobalSearchResults(data.content || []);
    } catch (err) {
      console.error('Error in global search:', err);
      setGlobalSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const clearSearch = () => {
    setGlobalSearchResults([]);
    setIsGlobalSearch(false);
  };

  return {
    globalSearchResults,
    isGlobalSearch,
    searchLoading,
    handleGlobalSearch,
    clearSearch
  };
};
