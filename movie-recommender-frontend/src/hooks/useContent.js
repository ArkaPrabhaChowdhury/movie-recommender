import { useState, useEffect, useCallback, useRef } from 'react';
import ApiService from '../services/api';

export const useContent = (filters) => {
  const [content, setContent] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Use a ref to track the last filters used to avoid race conditions
  const lastFiltersRef = useRef(null);

  const fetchContent = useCallback(async (pageNum = 1, isLoadMore = false) => {
    if (!filters || !filters.selectedLanguage || !filters.selectedGenre || !filters.selectedContentType) {
      return;
    }

    if (isLoadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setPage(1);
      setHasMore(true);
    }
    setError(null);

    try {
      const data = await ApiService.discover(filters, pageNum);
      const newContent = data.content || [];

      if (isLoadMore) {
        setContent(prev => {
          // Avoid duplicates by ID
          const existingIds = new Set(prev.map(item => item.id));
          const uniqueNew = newContent.filter(item => !existingIds.has(item.id));
          return [...prev, ...uniqueNew];
        });
      } else {
        setContent(newContent);
      }

      // If we got fewer results than a typical "page", we might be at the end
      // However, TMDB results are filtered by OTT availability, so this is tricky.
      // But if we got 0, we definitely are.
      setHasMore(newContent.length > 0);
      setPage(pageNum);
    } catch (err) {
      console.error('Error fetching content:', err);
      setError('Failed to fetch content');
      if (!isLoadMore) setContent([]);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [filters]);

  const loadMore = useCallback(() => {
    if (!loading && !loadingMore && hasMore) {
      fetchContent(page + 1, true);
    }
  }, [loading, loadingMore, hasMore, page, fetchContent]);

  useEffect(() => {
    // Reset and fetch when filters change
    const filterString = JSON.stringify(filters);
    if (lastFiltersRef.current !== filterString) {
      lastFiltersRef.current = filterString;
      fetchContent(1, false);
    }
  }, [filters, fetchContent]);

  return {
    content,
    loading,
    loadingMore,
    error,
    hasMore,
    loadMore,
    refetch: () => fetchContent(1, false)
  };
};
