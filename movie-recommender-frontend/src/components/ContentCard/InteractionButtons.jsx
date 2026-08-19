import { useState } from 'react';
import { Heart, ThumbsDown, Bookmark, CheckCircle, BellRing, Plus, X } from 'lucide-react';

const InteractionButtons = ({
  item,
  onLike,
  onDislike,
  onWatchlist,
  onWatched,
  onWatching,
  userInteractions = [],
  interactionMap = {}
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  // Check if user has already interacted with this content
  const getUserAction = () => {
    // Check map first for high performance and full coverage
    if (interactionMap && Object.keys(interactionMap).length > 0) {
      const key = `${item.content_type}_${item.id}`;
      if (interactionMap[key]) return interactionMap[key];
    }

    // Fallback to recent list
    const interaction = userInteractions.find(
      inter => inter.content_id === item.id && inter.content_type === item.content_type
    );
    return interaction?.action || null;
  };

  const handleInteraction = async (e, action, rating = null) => {
    e.stopPropagation();
    console.log('🎯 Button clicked:', action, 'for', item?.title);

    if (loading) {
      console.log('❌ Already loading, ignoring click');
      return;
    }

    setLoading(true);
    try {
      let result;
      switch (action) {
        case 'liked':
          console.log('Calling onLike...');
          result = await onLike(item, rating);
          break;
        case 'disliked':
          console.log('Calling onDislike...');
          result = await onDislike(item);
          break;
        case 'watchlisted':
          console.log('Calling onWatchlist...');
          result = await onWatchlist(item);
          break;
        case 'watched':
          console.log('Calling onWatched...');
          result = await onWatched(item, rating);
          break;
        case 'watching':
          result = await onWatching(item);
          break;
      }

      console.log('✅ Interaction result:', result);

      if (result) {
        console.log(`✅ ${action} recorded for ${item.title}`);
        setIsExpanded(false);
      } else {
        console.log(`❌ ${action} failed for ${item.title}`);
      }
    } catch (error) {
      console.error(`❌ Error recording ${action}:`, error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleExpanded = (e) => {
    e.stopPropagation();
    console.log('🎯 Toggle button clicked, expanded:', !isExpanded);
    setIsExpanded(!isExpanded);
  };

  const userAction = getUserAction();
  const hasAction = (action) => Array.isArray(userAction) ? userAction.includes(action) : userAction === action;

  return (
    <div className="absolute top-2 left-2 z-10">
      {/* Main interaction button */}
      <button
        onClick={handleToggleExpanded}
        disabled={loading}
        className="w-10 h-10 bg-black/60 backdrop-blur-md hover:bg-black/80 rounded-full flex items-center justify-center text-white border border-white/10 transition-all duration-300 shadow-lg z-20 group"
      >
        {loading ? (
          <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
        ) : userAction && (Array.isArray(userAction) ? userAction.length > 0 : true) ? (
          <div className="flex items-center justify-center transition-transform group-hover:scale-110">
            {hasAction('liked') ? <Heart size={18} fill="currentColor" className="text-red-500" /> :
              hasAction('watchlisted') ? <Bookmark size={18} fill="currentColor" className="text-blue-500" /> :
              hasAction('watched') ? <CheckCircle size={18} className="text-green-500" /> :
              hasAction('watching') ? <BellRing size={18} className="text-amber-400" /> :
                  hasAction('disliked') ? <ThumbsDown size={18} className="text-gray-400" /> :
                    <Plus size={20} />}
          </div>
        ) : (
          <Plus size={20} className="transition-transform group-hover:rotate-90" />
        )}
      </button>

      {/* Expanded interaction options */}
      {isExpanded && (
        <div className="absolute top-12 left-0 bg-[#0d1117] backdrop-blur-xl rounded-xl p-1.5 flex flex-col gap-1 min-w-[140px] z-[60] shadow-2xl border border-gray-800 animate-in fade-in slide-in-from-top-2 duration-200">
          <button
            onClick={(e) => handleInteraction(e, 'liked')}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${hasAction('liked') ? 'bg-red-500/10 text-red-500 font-medium' : 'text-gray-300 hover:bg-white/5'
              }`}
          >
            <Heart size={16} fill={hasAction('liked') ? "currentColor" : "none"} />
            <span>Like</span>
          </button>

          <button
            onClick={(e) => handleInteraction(e, 'disliked')}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${hasAction('disliked') ? 'bg-gray-500/20 text-gray-400 font-medium' : 'text-gray-300 hover:bg-white/5'
              }`}
          >
            <ThumbsDown size={16} fill={hasAction('disliked') ? "currentColor" : "none"} />
            <span>Dislike</span>
          </button>

          <button
            onClick={(e) => handleInteraction(e, 'watchlisted')}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${hasAction('watchlisted') ? 'bg-blue-500/10 text-blue-400 font-medium' : 'text-gray-300 hover:bg-white/5'
              }`}
          >
            <Bookmark size={16} fill={hasAction('watchlisted') ? "currentColor" : "none"} />
            <span>Watchlist</span>
          </button>

          <button
            onClick={(e) => handleInteraction(e, 'watched')}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${hasAction('watched') ? 'bg-green-500/10 text-green-400 font-medium' : 'text-gray-300 hover:bg-white/5'
              }`}
          >
            <CheckCircle size={16} />
            <span>Watched</span>
          </button>

          {item.content_type === 'tv' && (
            <button
              onClick={(e) => handleInteraction(e, 'watching')}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${hasAction('watching') ? 'bg-amber-500/10 text-amber-400 font-medium' : 'text-gray-300 hover:bg-white/5'}`}
              title="Email me when a new episode airs"
            >
              <BellRing size={16} />
              <span>Watching</span>
            </button>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(false);
            }}
            className="flex items-center justify-center gap-2 text-xs text-gray-500 hover:text-white mt-1 py-2 border-t border-gray-800/50"
          >
            <X size={12} />
            <span>Cancel</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default InteractionButtons;
