import { UI_CONFIG } from '../../config/constants';
import { isRecentRelease } from '../../config/constants';
import InteractionButtons from '../ContentCard/InteractionButtons';

const ContentCard = ({
  item,
  onLike,
  onDislike,
  onWatchlist,
  onWatched,
  userInteractions = [],
  showInteractionButtons = false
}) => {
  // Add debug logging
  console.log('ContentCard props:', {
    title: item.title,
    showInteractionButtons,
    hasOnLike: !!onLike,
    hasOnDislike: !!onDislike,
    hasOnWatchlist: !!onWatchlist,
    hasOnWatched: !!onWatched
  });

  return (
    <div className={`group cursor-pointer transition-all duration-${UI_CONFIG.ANIMATION_DURATION.NORMAL} hover:scale-105`}>
      <div className="relative aspect-[2/3] overflow-hidden rounded-lg shadow-lg" style={{ background: 'var(--color-bg-card)' }}>
        {item.poster ? (
          <img
            src={item.poster}
            alt={item.title}
            className={`w-full h-full object-cover group-hover:scale-110 group-hover:opacity-40 transition-transform duration-${UI_CONFIG.ANIMATION_DURATION.SLOW}`}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center" style={{ background: 'var(--color-bg-secondary)' }}>
            <span className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>No Image</span>
          </div>
        )}

        {/* Interaction buttons */}
        {showInteractionButtons && (
          <InteractionButtons
            item={item}
            onLike={onLike}
            onDislike={onDislike}
            onWatchlist={onWatchlist}
            onWatched={onWatched}
            userInteractions={userInteractions}
          />
        )}

        {/* ... rest of the card JSX remains the same ... */}
        <div className={`absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-${UI_CONFIG.ANIMATION_DURATION.NORMAL}`}>
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <h3 className="font-semibold text-white text-sm mb-1 line-clamp-2">
              {item.title}
            </h3>
            <p className="text-xs text-gray-300 mb-2">{item.year}</p>

            {item.streaming && item.streaming.available_on && item.streaming.available_on.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-gray-400 mb-1">Watch on:</p>
                <div className="flex flex-wrap gap-1">
                  {item.streaming.available_on.slice(0, 3).map((platform, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 text-xs rounded-full text-white font-medium"
                      style={{ backgroundColor: platform.color }}
                    >
                      {platform.name}
                    </span>
                  ))}
                  {item.streaming.available_on.length > 3 && (
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-600 text-white">
                      +{item.streaming.available_on.length - 3}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="absolute top-2 right-2">
          {item.rating > 0 && (
            <span className="px-2 py-1 text-xs rounded-full" style={{ background: 'rgba(0,0,0,0.8)', color: 'var(--color-accent-400)' }}>
              ⭐ {item.rating.toFixed(1)}
            </span>
          )}
        </div>

        <div className={`absolute ${showInteractionButtons ? 'top-12' : 'top-2'} right-2 flex flex-col gap-1`}>
          <span className="px-2 py-1 text-white text-xs rounded-full font-medium" style={{ background: 'var(--color-primary-600)' }}>
            {item.content_type === 'movie' ? '🎬' : '📺'} {item.content_type.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="mt-3">
        <h3 className="font-medium text-sm line-clamp-2 transition-colors" style={{ color: 'var(--color-text-primary)' }} onMouseEnter={(e) => e.target.style.color = 'var(--color-primary-400)'} onMouseLeave={(e) => e.target.style.color = 'var(--color-text-primary)'}>
          {item.title}
        </h3>
        <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>{item.year}</p>

        {item.streaming && item.streaming.available_on && item.streaming.available_on.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {item.streaming.available_on.slice(0, 2).map((platform, index) => (
              <span
                key={index}
                className="text-xs px-1 py-0.5 rounded text-white"
                style={{ backgroundColor: platform.color }}
              >
                {platform.name}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ContentCard;
