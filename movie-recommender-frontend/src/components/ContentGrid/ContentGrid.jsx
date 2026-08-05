import React, { useState, useEffect, useRef } from 'react';
import ContentCard from './ContentCard';
import SkeletonCard from './SkeletonCard';
import ContentDetailsModal from '../ContentCard/ContentDetailsModal';
import EmptyState from '../UI/EmptyState';
import { UI_CONFIG } from '../../config/constants';

// Number of skeleton cards to show while loading
const SKELETON_COUNT = 20;

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
  onWatching,
  userInteractions,
  interactionMap = {},
  subscribedProviders = [],
  initialContentType,
  initialContentId,
  onCloseModal,
  error
}) => {
  const [selectedContent, setSelectedContent] = useState(null);

  // Set up initial content from deep link if present
  useEffect(() => {
    if (initialContentType && initialContentId) {
      setSelectedContent({ id: initialContentId, content_type: initialContentType });
    }
  }, [initialContentType, initialContentId]);
  const observerRef = useRef(null);

  // Set up intersection observer for infinite scroll
  useEffect(() => {
    if (loading || !onLoadMore || !hasMore || error) return;

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

  return (
    <>
      {loading && !selectedContent ? (
        <div className={`grid grid-cols-2 ${UI_CONFIG.GRID_BREAKPOINTS.SM} ${UI_CONFIG.GRID_BREAKPOINTS.MD} ${UI_CONFIG.GRID_BREAKPOINTS.LG} ${UI_CONFIG.GRID_BREAKPOINTS.XL} gap-6`}>
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : error && content.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="p-4 rounded-full bg-red-500/10 text-red-500 mb-4">
            <Bot size={40} />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Connection Issues</h3>
          <p className="text-gray-400 max-w-md">
            We're having trouble reaching the scouting server. It might be starting up or under heavy load. Please wait a few seconds.
          </p>
        </div>
      ) : content.length === 0 ? (
        <EmptyState message={
          isGlobalSearch ? `No OTT content found for "${searchQuery}". Try a different search term.` :
          isAIRecommendationMode ? "No AI recommendations found. Try asking the AI assistant something else." :
          isPersonalizedMode ? "No personalized recommendations available. Like more content to improve recommendations." :
          "No content found. Try different filters."
        } />
      ) : (
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
                onWatching={onWatching}
                userInteractions={userInteractions}
                interactionMap={interactionMap}
                subscribedProviders={subscribedProviders}
              />
            </div>
          ))}
        </div>
      )}

      {/* Sentinel for infinite scroll */}
      {hasMore && !loading && (
        <div ref={observerRef} className="py-12 flex justify-center">
          {loadingMore && (
            <div className={`grid grid-cols-2 ${UI_CONFIG.GRID_BREAKPOINTS.SM} ${UI_CONFIG.GRID_BREAKPOINTS.MD} ${UI_CONFIG.GRID_BREAKPOINTS.LG} ${UI_CONFIG.GRID_BREAKPOINTS.XL} gap-6 w-full`}>
              {Array.from({ length: 8 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          )}
        </div>
      )}

      {selectedContent && (
        <ContentDetailsModal
          isOpen={!!selectedContent}
          onClose={() => {
            setSelectedContent(null);
            if (onCloseModal) onCloseModal();
          }}
          contentId={selectedContent.id}
          contentType={selectedContent.content_type}
          onLike={onLike}
          onDislike={onDislike}
          onWatchlist={onWatchlist}
          onWatched={onWatched}
          onWatching={onWatching}
          userInteractions={userInteractions}
          interactionMap={interactionMap}
          subscribedProviders={subscribedProviders}
        />
      )}
    </>
  );
};

export default ContentGrid;
