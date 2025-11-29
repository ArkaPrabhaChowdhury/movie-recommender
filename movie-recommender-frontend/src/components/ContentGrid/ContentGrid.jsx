import ContentCard from './ContentCard';
import LoadingSpinner from '../UI/LoadingSpinner';
import EmptyState from '../UI/EmptyState';
import { UI_CONFIG } from '../../config/constants';

const ContentGrid = ({ 
  content, 
  loading, 
  isGlobalSearch, 
  isAIRecommendationMode,
  isPersonalizedMode,
  searchQuery,
  showInteractionButtons,
  onLike,
  onDislike,
  onWatchlist,
  onWatched,
  userInteractions
}) => {
  if (loading) {
    return <LoadingSpinner />;
  }

  if (content.length === 0) {
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
    <div className={`grid grid-cols-2 ${UI_CONFIG.GRID_BREAKPOINTS.SM} ${UI_CONFIG.GRID_BREAKPOINTS.MD} ${UI_CONFIG.GRID_BREAKPOINTS.LG} ${UI_CONFIG.GRID_BREAKPOINTS.XL} gap-6`}>
      {content.map((item) => (
        <ContentCard 
          key={`${item.content_type}-${item.id}`} 
          item={item}
          showInteractionButtons={showInteractionButtons}
          onLike={onLike}
          onDislike={onDislike}
          onWatchlist={onWatchlist}
          onWatched={onWatched}
          userInteractions={userInteractions}
        />
      ))}
    </div>
  );
};

export default ContentGrid;
