import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    Bookmark,
    CheckCircle,
    ArrowLeft,
    Filter,
    Search,
    SortAsc,
    Trash2,
    Film,
    Tv,
    TrendingUp
} from 'lucide-react';
import ApiService from '../services/api';
import ContentGrid from '../components/ContentGrid/ContentGrid';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const MyListPage = ({
    userId,
    userProfile,
    likeContent,
    dislikeContent,
    addToWatchlist,
    markAsWatched
}) => {
    const navigate = useNavigate();
    const location = useLocation();

    // Parse tab from query param if available
    const searchParams = new URLSearchParams(location.search);
    const initialTab = searchParams.get('tab') === 'history' ? 'history' : 'watchlist';

    const [activeTab, setActiveTab] = useState(initialTab); // 'watchlist' or 'history'
    const [isLoading, setIsLoading] = useState(true);
    const [listContent, setListContent] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('newest'); // 'newest', 'rating', 'title'
    const [filterType, setFilterType] = useState('all'); // 'all', 'movie', 'tv'

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const urlTab = params.get('tab');
        if (urlTab && (urlTab === 'watchlist' || urlTab === 'history') && urlTab !== activeTab) {
            setActiveTab(urlTab);
        }
        fetchListData();
    }, [activeTab, userId, userProfile?.updated_at, location.search]);

    const fetchListData = async () => {
        if (!userId) return;
        setIsLoading(true);
        try {
            const data = activeTab === 'watchlist'
                ? await ApiService.getWatchlist(userId)
                : await ApiService.getHistory(userId);

            const content = activeTab === 'watchlist' ? data.watchlist : data.history;

            // Format for ContentGrid (ensure poster is present if possible)
            const formattedContent = (content || []).map(item => ({
                ...item,
                id: item.content_id, // Map back for grid compatibility
                // Fallback for poster and rating if missing in interaction
                poster: item.poster || null,
                rating: item.tmdb_rating || item.rating || 0
            }));

            setListContent(formattedContent);
        } catch (error) {
            console.error(`Error fetching ${activeTab}:`, error);
        } finally {
            setIsLoading(false);
        }
    };

    // Filter and Sort Logic
    const filteredContent = listContent
        .filter(item => {
            const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesType = filterType === 'all' || item.content_type === filterType;
            return matchesSearch && matchesType;
        })
        .sort((a, b) => {
            if (sortBy === 'newest') {
                return new Date(b.timestamp) - new Date(a.timestamp);
            } else if (sortBy === 'rating') {
                return (b.rating || 0) - (a.rating || 0);
            } else if (sortBy === 'title') {
                return a.title.localeCompare(b.title);
            }
            return 0;
        });

    return (
        <div className="min-h-screen text-white bg-[#0d1117]">
            {/* Header */}
            <div className="sticky top-0 z-50 backdrop-blur-md border-b border-gray-800 bg-[#0d1117]/80">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => navigate('/')}
                                className="p-2 hover:bg-gray-800 rounded-full transition-colors group"
                                title="Back to Home"
                            >
                                <ArrowLeft size={24} className="text-gray-400 group-hover:text-teal-400" />
                            </button>
                            <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                                My Collections
                            </h1>
                        </div>

                        {/* Tabs */}
                        <div className="flex p-1 bg-gray-900/50 rounded-xl border border-gray-800">
                            {[
                                { id: 'watchlist', label: 'Watchlist', icon: Bookmark },
                                { id: 'history', label: 'History', icon: CheckCircle }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center justify-center gap-2 px-6 py-2 w-1/2 rounded-lg text-sm font-semibold transition-all duration-300 ${activeTab === tab.id
                                        ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/20'
                                        : 'text-gray-400 hover:text-white'
                                        }`}
                                >
                                    <tab.icon size={16} />
                                    {tab.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Subheader: Filters and Sort */}
            <div className="border-b border-gray-900 bg-[#0d1117]/50">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex flex-col lg:flex-row gap-4 justify-between items-center">
                        {/* Search */}
                        <div className="relative w-full lg:max-w-md group">
                            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-teal-400 transition-colors" />
                            <input
                                type="text"
                                placeholder={`Search in ${activeTab}...`}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-10 pr-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500/50 transition-all text-sm"
                            />
                        </div>

                        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
                            {/* Type Filter */}
                            <div className="flex items-center gap-1 bg-gray-900 p-1 rounded-xl border border-gray-800">
                                {[
                                    { id: 'all', label: 'All' },
                                    { id: 'movie', label: 'Movies', icon: Film },
                                    { id: 'tv', label: 'TV Shows', icon: Tv }
                                ].map((type) => (
                                    <button
                                        key={type.id}
                                        onClick={() => setFilterType(type.id)}
                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all ${filterType === type.id
                                            ? 'bg-gray-800 text-teal-400 border border-teal-500/20 shadow-sm'
                                            : 'text-gray-500 hover:text-gray-300'
                                            }`}
                                    >
                                        {type.icon && <type.icon size={12} />}
                                        {type.label}
                                    </button>
                                ))}
                            </div>

                            {/* Sort */}
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value)}
                                className="bg-gray-900 border border-gray-800 rounded-xl px-2 py-2 text-xs font-bold text-gray-400 focus:outline-none focus:border-teal-500/50 uppercase tracking-widest cursor-pointer"
                            >
                                <option value="newest">Newest Added</option>
                                <option value="rating">Top Rated</option>
                                <option value="title">A-Z</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <main className="max-w-7xl mx-auto px-4 py-8 pb-20">
                {isLoading ? (
                    <div className="py-20 flex flex-col items-center gap-4">
                        <LoadingSpinner size="lg" />
                        <p className="text-gray-500 animate-pulse text-sm font-medium tracking-wide">Retrieving your {activeTab}...</p>
                    </div>
                ) : filteredContent.length > 0 ? (
                    <ContentGrid
                        content={filteredContent}
                        showInteractionButtons={true}
                        onLike={likeContent}
                        onDislike={dislikeContent}
                        onWatchlist={addToWatchlist}
                        onWatched={markAsWatched}
                        userInteractions={userProfile?.recent_activity || []}
                        interactionMap={userProfile?.interaction_map || {}}
                        subscribedProviders={userProfile?.profile?.subscribed_providers || []}
                    />
                ) : (
                    <div className="py-20 flex flex-col items-center justify-center text-center max-w-sm mx-auto">
                        <div className="relative mb-8">
                            <div className="absolute -inset-4 bg-teal-500/5 blur-2xl rounded-full"></div>
                            {activeTab === 'watchlist' ? (
                                <Bookmark size={64} className="text-gray-800 relative" strokeWidth={1} />
                            ) : (
                                <CheckCircle size={64} className="text-gray-800 relative" strokeWidth={1} />
                            )}
                        </div>
                        <h3 className="text-xl font-bold text-gray-300 mb-2">
                            {searchQuery ? 'No matches found' : `Your ${activeTab === 'history' ? 'History' : activeTab} is empty`}
                        </h3>
                        <p className="text-gray-500 text-sm mb-8 leading-relaxed">
                            {searchQuery
                                ? "We couldn't find anything matching your search. Try different keywords!"
                                : `Start building your ${activeTab === 'history' ? 'History' : activeTab} by browsing our collection and marking your favorite content.`}
                        </p>
                        <button
                            onClick={() => navigate('/')}
                            className="group flex items-center gap-2 px-8 py-3 bg-teal-500 text-black font-bold rounded-xl hover:bg-teal-400 transition-all active:scale-95 shadow-lg shadow-teal-500/20"
                        >
                            <TrendingUp size={18} className="group-hover:translate-y-[-2px] transition-transform" />
                            Discover Content
                        </button>
                    </div>
                )}
            </main>
        </div>
    );
};

export default MyListPage;
