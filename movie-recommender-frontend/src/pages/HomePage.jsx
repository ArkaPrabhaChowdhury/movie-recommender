import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Sparkles, Bot, ArrowLeft } from 'lucide-react';
import FilterSection from '../components/Filters/FilterSection';
import ContentGrid from '../components/ContentGrid/ContentGrid';
import SearchResults from '../components/Search/SearchResults';
import ChatBot from '../components/AIChatbot/ChatBot';
import { useContent } from '../hooks/useContent';
import { DEFAULTS } from '../config/constants';

const HomePage = ({
    searchQuery,
    onClearSearch,
    isGlobalSearch,
    globalSearchResults,
    searchLoading,
    userId,
    userName,
    userProfile,
    personalizedRecommendations,
    preferencesLoading,
    likeContent,
    dislikeContent,
    addToWatchlist,
    markAsWatched,
    isPersonalizedMode,
    setIsPersonalizedMode,
    isAIRecommendationMode,
    setIsAIRecommendationMode,
    aiRecommendations,
    setAiRecommendations,
    aiResponse,
    setAiResponse,
    onGetPersonalizedRecommendations,
    hasPreferences
}) => {
    // Filter state
    const [selectedLanguage, setSelectedLanguage] = useState(DEFAULTS.LANGUAGE);
    const [selectedGenre, setSelectedGenre] = useState(DEFAULTS.GENRE);
    const [selectedContentType, setSelectedContentType] = useState(DEFAULTS.CONTENT_TYPE);
    const [selectedReleasePeriod, setSelectedReleasePeriod] = useState(DEFAULTS.RELEASE_PERIOD);
    const [selectedSortBy, setSelectedSortBy] = useState(DEFAULTS.SORT_BY);
    
    const { contentType, contentId } = useParams();
    const navigate = useNavigate();

    const resetFilters = () => {
        setSelectedLanguage(DEFAULTS.LANGUAGE);
        setSelectedGenre(DEFAULTS.GENRE);
        setSelectedContentType(DEFAULTS.CONTENT_TYPE);
        setSelectedReleasePeriod(DEFAULTS.RELEASE_PERIOD);
        setSelectedSortBy(DEFAULTS.SORT_BY);
    };

    // Custom hooks
    const filters = (!isAIRecommendationMode && !isPersonalizedMode) ? {
        selectedLanguage,
        selectedGenre,
        selectedContentType,
        selectedReleasePeriod,
        sortBy: selectedSortBy
    } : null;

    const {
        content,
        loading,
        loadingMore,
        hasMore,
        loadMore
    } = useContent(filters, userId);

    const handleAIRecommendations = (recommendations, response) => {
        console.log('Received AI recommendations:', recommendations.length);
        setAiRecommendations(recommendations);
        setAiResponse(response);
        setIsAIRecommendationMode(true);
        setIsPersonalizedMode(false);
    };

    // Determine what content to display
    let displayContent = [];
    let isDisplayLoading = false;
    let displayMode = 'normal';

    if (isPersonalizedMode) {
        displayContent = personalizedRecommendations;
        isDisplayLoading = preferencesLoading;
        displayMode = 'personalized';
    } else if (isAIRecommendationMode) {
        displayContent = aiRecommendations;
        isDisplayLoading = false;
        displayMode = 'ai';
    } else if (isGlobalSearch) {
        displayContent = globalSearchResults;
        isDisplayLoading = searchLoading;
        displayMode = 'search';
    } else {
        displayContent = content || [];
        isDisplayLoading = loading;
        displayMode = 'normal';
    }

    return (
        <main className="max-w-7xl mx-auto px-4 py-8">
            {/* Show filters only in normal browsing mode */}
            {displayMode === 'normal' && (
                <>
                    {hasPreferences && (
                        <div className="mb-8 flex flex-wrap items-center justify-between p-1.5 rounded-2xl bg-[#161b22] border border-gray-800 shadow-xl overflow-hidden group">
                            <div className="flex items-center gap-4 px-5 py-3 flex-1 min-w-[300px]">
                                <div className="relative">
                                    <div className="absolute -inset-1 bg-teal-500/30 rounded-full blur group-hover:blur-md transition-all duration-300"></div>
                                    <div className="relative p-2.5 rounded-full bg-teal-500 text-white shadow-inner">
                                        <Sparkles size={22} />
                                    </div>
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-white tracking-tight">
                                        {userName ? `Welcome, ${userName.split(' ')[0]}!` : 'Your Daily Discoveries'}
                                    </h3>
                                    <p className="text-sm text-gray-400">
                                        {userName ? "Here are your top-picked discoveries for today." : "Fresh recommendations based on your unique interests"}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={onGetPersonalizedRecommendations}
                                disabled={preferencesLoading}
                                className="m-1.5 px-8 py-3.5 rounded-xl bg-white hover:bg-teal-50 text-black font-bold text-sm transition-all shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2.5"
                            >
                                {preferencesLoading ? (
                                    <div className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                                ) : <Sparkles size={18} className="text-teal-600" />}
                                {preferencesLoading ? 'Generating...' : 'Refresh My Picks'}
                            </button>
                        </div>
                    )}
                    <FilterSection
                        selectedLanguage={selectedLanguage}
                        setSelectedLanguage={setSelectedLanguage}
                        selectedContentType={selectedContentType}
                        setSelectedContentType={setSelectedContentType}
                        selectedReleasePeriod={selectedReleasePeriod}
                        setSelectedReleasePeriod={setSelectedReleasePeriod}
                        selectedGenre={selectedGenre}
                        setSelectedGenre={setSelectedGenre}
                        selectedSortBy={selectedSortBy}
                        setSelectedSortBy={setSelectedSortBy}
                        onReset={resetFilters}
                    />
                </>
            )}

            {/* Headers for different modes */}
            {displayMode === 'search' && !isDisplayLoading && (
                <SearchResults
                    query={searchQuery}
                    resultCount={globalSearchResults.length}
                    onBackToBrowse={onClearSearch}
                />
            )}

            {displayMode === 'ai' && (
                <div className="mb-8">
                    <h2 className="text-2xl font-semibold text-white mb-2 flex items-center gap-2">
                        <Bot size={24} className="text-teal-500" /> AI Recommendations
                    </h2>
                    <p className="text-gray-400 mb-2">{aiResponse}</p>
                    <p className="text-gray-500 text-sm">
                        Found {aiRecommendations.length} AI-curated recommendations
                    </p>
                    <button
                        onClick={onClearSearch}
                        className="mt-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-md text-sm text-gray-300"
                    >
                        ← Back to Browse
                    </button>
                </div>
            )}

            {displayMode === 'personalized' && (
                <div className="mb-8">
                    <h2 className="text-2xl font-semibold text-white mb-2 flex items-center gap-2">
                        <Sparkles size={24} className="text-teal-500" /> Your Personalized Recommendations
                    </h2>
                    <p className="text-gray-400 mb-2">
                        Based on your viewing preferences and liked content
                    </p>
                    <p className="text-gray-500 text-sm">
                        {personalizedRecommendations.length} recommendations tailored for you
                    </p>
                    <button
                        onClick={onClearSearch}
                        className="mt-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-md text-sm text-gray-300"
                    >
                        ← Back to Browse
                    </button>
                </div>
            )}

            {/* Content Grid with Interaction Buttons */}
            <ContentGrid
                content={displayContent}
                loading={isDisplayLoading}
                loadingMore={displayMode === 'normal' ? loadingMore : false}
                hasMore={displayMode === 'normal' ? hasMore : false}
                onLoadMore={displayMode === 'normal' ? loadMore : null}
                isGlobalSearch={displayMode === 'search'}
                isAIRecommendationMode={displayMode === 'ai'}
                isPersonalizedMode={displayMode === 'personalized'}
                searchQuery={searchQuery}
                showInteractionButtons={userId ? true : false}
                onLike={likeContent}
                onDislike={dislikeContent}
                onWatchlist={addToWatchlist}
                onWatched={markAsWatched}
                userInteractions={userProfile?.recent_activity || []}
                interactionMap={userProfile?.interaction_map || {}}
                subscribedProviders={userProfile?.profile?.subscribed_providers || []}
                initialContentType={contentType}
                initialContentId={contentId}
                onCloseModal={() => navigate('/')}
            />

            {/* AI Chat Bot */}
            <ChatBot onRecommendationsReceived={handleAIRecommendations} />
        </main>
    );
};

export default HomePage;
