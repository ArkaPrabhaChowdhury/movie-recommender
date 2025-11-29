import { useState, useEffect } from 'react';
import ApiService from '../services/api';

export const useContent = (filters) => {
  const [content, setContent] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchContent = async () => {
    // Check if filters exist and have required properties
    if (!filters || !filters.selectedLanguage || !filters.selectedGenre || !filters.selectedContentType) {
      console.log('Filters not ready yet, skipping fetch');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await ApiService.discover(filters);
      setContent(data.content || []);
    } catch (err) {
      console.error('Error fetching content:', err);
      setError('Failed to fetch content');
      setContent([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if filters are properly defined
    if (filters && filters.selectedLanguage && filters.selectedGenre && filters.selectedContentType) {
      fetchContent();
    }
  }, [
    filters?.selectedLanguage, 
    filters?.selectedGenre, 
    filters?.selectedContentType, 
    filters?.selectedReleasePeriod
  ]);

  return { content, loading, error, refetch: fetchContent };
};
