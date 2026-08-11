import { UI_CONFIG } from '../../config/constants';
import InteractionButtons from '../ContentCard/InteractionButtons';
import { Star, Film, Tv } from 'lucide-react';

const ContentCard = ({
  item,
  onLike,
  onDislike,
  onWatchlist,
  onWatched,
  onWatching,
  userInteractions = [],
  interactionMap = {},
  showInteractionButtons = false,
  subscribedProviders = []
}) => {
  const displayedPlatforms = item.streaming?.available_on?.filter(p =>
    subscribedProviders.length === 0 || subscribedProviders.includes(p.id)
  ) || [];

  console.log(item)
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
            onWatching={onWatching}
            userInteractions={userInteractions}
            interactionMap={interactionMap}
          />
        )}

        {/* ... rest of the card JSX remains the same ... */}
        <div className={`absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-${UI_CONFIG.ANIMATION_DURATION.NORMAL}`}>
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <h3 className="font-semibold text-white text-sm mb-1 line-clamp-2">
              {item.title}
            </h3>
            <p className="text-xs text-gray-300 mb-2">{item.year}</p>

            {displayedPlatforms.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-gray-400 mb-1">Watch on:</p>
                <div className="flex flex-wrap gap-1">
                  {displayedPlatforms.slice(0, 3).map((platform, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 text-xs rounded-full text-white font-medium"
                      style={{ backgroundColor: platform.color }}
                    >
                      {platform.name}
                    </span>
                  ))}
                  {displayedPlatforms.length > 3 && (
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-600 text-white">
                      +{displayedPlatforms.length - 3}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="absolute top-2 right-2">
          {item.rating > 0 && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full font-bold shadow-lg border border-black/20" style={{ background: 'rgba(0,0,0,0.85)', color: 'var(--color-accent-400)' }}>
              <Star size={12} fill="currentColor" />
              <span>{item.rating.toFixed(1)}</span>
            </span>
          )}
        </div>

        <div className={`absolute ${showInteractionButtons ? 'top-10.5' : 'top-2'} right-2 flex flex-col gap-1 items-end`}>
          <span className="flex items-center gap-1.5 px-2.5 py-1 text-white text-[10px] rounded-full font-bold shadow-lg border border-black/20 tracking-wider" style={{ background: 'var(--color-primary-600)' }}>
            {item.content_type === 'movie' ? <Film size={10} /> : <Tv size={10} />}
            {item.content_type.toUpperCase()}
          </span>
          {item.action && (
            <span className={`px-2 py-0.5 text-[9px] rounded-full font-black uppercase tracking-widest border border-white/20 shadow-xl ${item.action === 'liked' ? 'bg-red-500 text-white' :
                item.action === 'watchlisted' ? 'bg-blue-600 text-white' :
                  item.action === 'watched' ? 'bg-green-600 text-white' :
                    'bg-gray-700 text-gray-200'
              }`}>
              {item.action}
            </span>
          )}
        </div>
      </div>

      <div className="mt-3">
        <h3 className="font-medium text-sm line-clamp-2 transition-colors" style={{ color: 'var(--color-text-primary)' }} onMouseEnter={(e) => e.target.style.color = 'var(--color-primary-400)'} onMouseLeave={(e) => e.target.style.color = 'var(--color-text-primary)'}>
          {item.title}
        </h3>
        <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>{item.year}</p>

        {displayedPlatforms.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {displayedPlatforms.slice(0, 2).map((platform, index) => (
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

        {/* Recommendation reason tag below title */}
        {item.recommendation_reason && (
          <p className="text-[10px] mt-1.5 line-clamp-1 font-medium"
            style={{ color: 'var(--color-primary-400)' }}>
            ✦ {item.recommendation_reason}
          </p>
        )}
      </div>
    </div>
  );
};

export default ContentCard;
