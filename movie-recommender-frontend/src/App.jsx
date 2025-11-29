import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header/Header';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import { useGlobalSearch } from './hooks/useGlobalSearch';
import { useUserPreferences } from './hooks/useUserPreferences';
import { API_CONFIG } from './config/constants';

function App() {
  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  // AI and personalization state
  const [isAIRecommendationMode, setIsAIRecommendationMode] = useState(false);
  const [isPersonalizedMode, setIsPersonalizedMode] = useState(false);
  const [aiRecommendations, setAiRecommendations] = useState([]);
  const [aiResponse, setAiResponse] = useState('');

  // Custom hooks
  const {
    globalSearchResults,
    isGlobalSearch,
    searchLoading,
    handleGlobalSearch,
    clearSearch
  } = useGlobalSearch();

  // User preferences hook
  const {
    userId,
    userProfile,
    personalizedRecommendations,
    loading: preferencesLoading,
    likeContent,
    dislikeContent,
    addToWatchlist,
    markAsWatched,
    getPersonalizedRecommendations,
    hasPreferences
  } = useUserPreferences();

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    setIsAIRecommendationMode(false);
    setIsPersonalizedMode(false);

    if (query.trim().length >= API_CONFIG.MIN_SEARCH_LENGTH) {
      clearTimeout(window.searchTimeout);
      window.searchTimeout = setTimeout(() => {
        handleGlobalSearch(query);
      }, API_CONFIG.SEARCH_DEBOUNCE_DELAY);
    } else {
      clearSearch();
    }
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setIsAIRecommendationMode(false);
    setIsPersonalizedMode(false);
    clearSearch();
  };

  // Handle personalized recommendations
  const handlePersonalizedRecommendations = async () => {
    const response = await getPersonalizedRecommendations();

    if (response.recommendations && response.recommendations.length > 0) {
      setIsPersonalizedMode(true);
      setIsAIRecommendationMode(false);
      setSearchQuery('');
      clearSearch();

      console.log(`✨ Loaded ${response.recommendations.length} personalized recommendations`);
    }
  };

  return (
    <Router>
      <div className="min-h-screen text-white">
        <Header
          searchQuery={searchQuery}
          onSearchChange={handleSearchChange}
          onClearSearch={handleClearSearch}
          isGlobalSearch={isGlobalSearch}
          globalSearchResults={globalSearchResults}
          userId={userId}
        />

        <Routes>
          <Route
            path="/"
            element={
              <HomePage
                searchQuery={searchQuery}
                onClearSearch={handleClearSearch}
                isGlobalSearch={isGlobalSearch}
                globalSearchResults={globalSearchResults}
                searchLoading={searchLoading}
                userId={userId}
                userProfile={userProfile}
                personalizedRecommendations={personalizedRecommendations}
                preferencesLoading={preferencesLoading}
                likeContent={likeContent}
                dislikeContent={dislikeContent}
                addToWatchlist={addToWatchlist}
                markAsWatched={markAsWatched}
                isPersonalizedMode={isPersonalizedMode}
                setIsPersonalizedMode={setIsPersonalizedMode}
                isAIRecommendationMode={isAIRecommendationMode}
                setIsAIRecommendationMode={setIsAIRecommendationMode}
                aiRecommendations={aiRecommendations}
                setAiRecommendations={setAiRecommendations}
                aiResponse={aiResponse}
                setAiResponse={setAiResponse}
              />
            }
          />
          <Route
            path="/profile"
            element={
              <ProfilePage
                userProfile={userProfile}
                onGetPersonalizedRecommendations={handlePersonalizedRecommendations}
                hasPreferences={hasPreferences}
                loading={preferencesLoading}
              />
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
