import { useState } from 'react';
import { Sparkles } from 'lucide-react';
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
    setAiResponse
}) => {
    // Filter state
    const [selectedLanguage, setSelectedLanguage] = useState(DEFAULTS.LANGUAGE);
    const [selectedGenre, setSelectedGenre] = useState(DEFAULTS.GENRE);
    const [selectedContentType, setSelectedContentType] = useState(DEFAULTS.CONTENT_TYPE);
    const [selectedReleasePeriod, setSelectedReleasePeriod] = useState(DEFAULTS.RELEASE_PERIOD);

    // Custom hooks
    const filters = (!isAIRecommendationMode && !isPersonalizedMode) ? {
        selectedLanguage,
        selectedGenre,
        selectedContentType,
        selectedReleasePeriod
    } : null;

    const { content, loading } = useContent(filters);

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
                <FilterSection
                    selectedLanguage={selectedLanguage}
                    setSelectedLanguage={setSelectedLanguage}
                    selectedContentType={selectedContentType}
                    setSelectedContentType={setSelectedContentType}
                    selectedReleasePeriod={selectedReleasePeriod}
                    setSelectedReleasePeriod={setSelectedReleasePeriod}
                    selectedGenre={selectedGenre}
                    setSelectedGenre={setSelectedGenre}
                />
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
                    <h2 className="text-2xl font-semibold text-white mb-2">
                        🤖 AI Recommendations
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
            />

            {/* AI Chat Bot */}
            <ChatBot onRecommendationsReceived={handleAIRecommendations} />
        </main>
    );
};

export default HomePage;
