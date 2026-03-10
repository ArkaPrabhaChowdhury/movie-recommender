import React, { useState, useEffect, useRef } from 'react';
import ContentCard from './ContentCard';
import ContentDetailsModal from '../ContentCard/ContentDetailsModal';
import LoadingSpinner from '../UI/LoadingSpinner';
import EmptyState from '../UI/EmptyState';
import { UI_CONFIG } from '../../config/constants';

const ContentGrid = ({
  content,
  loading,
  loadingMore,
  hasMore,
  onLoadMore,
  isGlobalSearch,
  isAIRecommendationMode,
  isPersonalizedMode,
  searchQuery,
  showInteractionButtons,
  onLike,
  onDislike,
  onWatchlist,
  onWatched,
  userInteractions,
  interactionMap = {},
  subscribedProviders = []
}) => {
  const [selectedContent, setSelectedContent] = useState(null);
  const observerRef = useRef(null);

  // Set up intersection observer for infinite scroll
  useEffect(() => {
    if (loading || !onLoadMore || !hasMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          onLoadMore();
        }
      },
      { threshold: 1.0 }
    );

    if (observerRef.current) {
      observer.observe(observerRef.current);
    }

    return () => {
      if (observerRef.current) {
        observer.unobserve(observerRef.current);
      }
    };
  }, [loading, loadingMore, hasMore, onLoadMore]);

  if (loading && content.length === 0) {
    return <LoadingSpinner />;
  }

  if (content.length === 0 && !loading) {
    let emptyMessage;
    if (isGlobalSearch) {
      emptyMessage = `No OTT content found for "${searchQuery}". Try a different search term.`;
    } else if (isAIRecommendationMode) {
      emptyMessage = "No AI recommendations found. Try asking the AI assistant something else.";
    } else if (isPersonalizedMode) {
      emptyMessage = "No personalized recommendations available. Like more content to improve recommendations.";
    } else {
      emptyMessage = "No content found. Try different filters.";
    }

    return <EmptyState message={emptyMessage} />;
  }

  return (
    <>
      <div className={`grid grid-cols-2 ${UI_CONFIG.GRID_BREAKPOINTS.SM} ${UI_CONFIG.GRID_BREAKPOINTS.MD} ${UI_CONFIG.GRID_BREAKPOINTS.LG} ${UI_CONFIG.GRID_BREAKPOINTS.XL} gap-6`}>
        {content.map((item, index) => (
          <div key={`${item.content_type}-${item.id}-${index}`} onClick={() => setSelectedContent(item)}>
            <ContentCard
              item={item}
              showInteractionButtons={showInteractionButtons}
              onLike={onLike}
              onDislike={onDislike}
              onWatchlist={onWatchlist}
              onWatched={onWatched}
              userInteractions={userInteractions}
              interactionMap={interactionMap}
              subscribedProviders={subscribedProviders}
            />
          </div>
        ))}
      </div>

      {/* Sentinel for infinite scroll */}
      {hasMore && (
        <div ref={observerRef} className="py-12 flex justify-center">
          {loadingMore && <LoadingSpinner size="sm" />}
        </div>
      )}

      {selectedContent && (
        <ContentDetailsModal
          isOpen={!!selectedContent}
          onClose={() => setSelectedContent(null)}
          contentId={selectedContent.id}
          contentType={selectedContent.content_type}
          onLike={onLike}
          onDislike={onDislike}
          onWatchlist={onWatchlist}
          onWatched={onWatched}
          userInteractions={userInteractions}
          interactionMap={interactionMap}
          subscribedProviders={subscribedProviders}
        />
      )}
    </>
  );
};

export default ContentGrid;
