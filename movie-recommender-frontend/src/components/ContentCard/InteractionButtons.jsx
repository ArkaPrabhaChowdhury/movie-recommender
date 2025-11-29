import { useState } from 'react';

const InteractionButtons = ({
  item,
  onLike,
  onDislike,
  onWatchlist,
  onWatched,
  userInteractions = []
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  // Debug logging
  console.log('InteractionButtons props:', {
    itemTitle: item?.title,
    hasOnLike: !!onLike,
    hasOnDislike: !!onDislike,
    hasOnWatchlist: !!onWatchlist,
    hasOnWatched: !!onWatched,
    userInteractionsCount: userInteractions.length
  });

  // Check if user has already interacted with this content
  const getUserAction = () => {
    const interaction = userInteractions.find(
      inter => inter.content_id === item.id && inter.content_type === item.content_type
    );
    return interaction?.action || null;
  };

  const handleInteraction = async (action, rating = null) => {
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

  const handleToggleExpanded = () => {
    console.log('🎯 Toggle button clicked, expanded:', !isExpanded);
    setIsExpanded(!isExpanded);
  };

  const userAction = getUserAction();

  return (
    <div className="absolute top-2 left-2 z-10">
      {/* Debug indicator */}
      <div className="absolute -top-6 left-0 bg-green-600 text-white text-xs px-1 rounded">
        DEBUG
      </div>

      {/* Main interaction button */}
      <button
        onClick={handleToggleExpanded}
        className="w-8 h-8 bg-black/80 hover:bg-black/90 rounded-full flex items-center justify-center text-white transition-all duration-200 z-20"
        disabled={loading}
      >
        {loading ? (
          <div className="w-4 h-4 border border-white border-t-transparent rounded-full animate-spin" />
        ) : userAction ? (
          <span className="text-sm">
            {userAction === 'liked' && '❤️'}
            {userAction === 'disliked' && '👎'}
            {userAction === 'watchlisted' && '📌'}
            {userAction === 'watched' && '✅'}
          </span>
        ) : (
          <span className="text-lg">+</span>
        )}
      </button>

      {/* Expanded interaction options */}
      {isExpanded && (
        <div className="absolute top-10 left-0 bg-black/95 backdrop-blur-sm rounded-lg p-2 flex flex-col gap-1 min-w-[120px] z-50 shadow-lg border border-gray-700">
          <button
            onClick={() => handleInteraction('liked')}
            className={`flex items-center gap-2 px-3 py-2 rounded text-sm hover:bg-white/10 transition-colors ${userAction === 'liked' ? 'bg-teal-600/30 text-red-400' : 'text-white'
              }`}
          >
            ❤️ Like
          </button>

          <button
            onClick={() => handleInteraction('disliked')}
            className={`flex items-center gap-2 px-3 py-2 rounded text-sm hover:bg-white/10 transition-colors ${userAction === 'disliked' ? 'bg-gray-600/30 text-gray-400' : 'text-white'
              }`}
          >
            👎 Dislike
          </button>

          <button
            onClick={() => handleInteraction('watchlisted')}
            className={`flex items-center gap-2 px-3 py-2 rounded text-sm hover:bg-white/10 transition-colors ${userAction === 'watchlisted' ? 'bg-blue-600/30 text-blue-400' : 'text-white'
              }`}
          >
            📌 Watchlist
          </button>

          <button
            onClick={() => handleInteraction('watched')}
            className={`flex items-center gap-2 px-3 py-2 rounded text-sm hover:bg-white/10 transition-colors ${userAction === 'watched' ? 'bg-green-600/30 text-green-400' : 'text-white'
              }`}
          >
            ✅ Watched
          </button>

          <button
            onClick={() => setIsExpanded(false)}
            className="text-xs text-gray-400 hover:text-white mt-1 px-3 py-1"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};

export default InteractionButtons;
