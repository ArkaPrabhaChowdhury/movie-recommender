import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Film, User, Heart, Bookmark, Zap, Theater, Globe, Smartphone,
    ThumbsDown, CheckCircle, ArrowLeft, Tv, Check
} from 'lucide-react';
import ApiService from '../services/api';

const ProfilePage = ({
    userProfile,
    userName,
    onGetPersonalizedRecommendations,
    hasPreferences,
    loading,
    updateSubscriptions
}) => {
    const navigate = useNavigate();

    // ── Watch Providers state ──────────────────────────────────────────────────
    const [watchProviders, setWatchProviders] = useState([]);
    const [selectedProviders, setSelectedProviders] = useState([]);
    const [providersLoading, setProvidersLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [savedOk, setSavedOk] = useState(false);

    // Fetch the provider list from TMDB (via backend) once on mount
    useEffect(() => {
        (async () => {
            setProvidersLoading(true);
            try {
                const providers = await ApiService.getWatchProviders('IN');
                setWatchProviders(Array.isArray(providers) ? providers : []);
            } catch (err) {
                console.error('Could not load watch providers:', err);
            } finally {
                setProvidersLoading(false);
            }
        })();
    }, []);

    // Seed local selection from the saved profile whenever it loads/changes
    useEffect(() => {
        const saved = userProfile?.profile?.subscribed_providers;
        if (Array.isArray(saved)) setSelectedProviders(saved);
    }, [userProfile]);

    const handleToggleProvider = (id) => {
        setSavedOk(false);
        setSelectedProviders(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
    };

    const handleSave = async () => {
        if (!updateSubscriptions) return;
        setIsSaving(true);
        const ok = await updateSubscriptions(selectedProviders);
        setIsSaving(false);
        if (ok) setSavedOk(true);
    };

    // Whether local selection differs from what's persisted
    const savedProviders = userProfile?.profile?.subscribed_providers || [];
    const isDirty = JSON.stringify([...selectedProviders].sort()) !==
        JSON.stringify([...savedProviders].sort());

    // ── Early return ───────────────────────────────────────────────────────────
    if (!userProfile) {
        return (
            <div className="min-h-screen text-white flex items-center justify-center">
                <div className="text-center">
                    <div className="mb-4 flex justify-center"><Film size={64} className="text-teal-500" /></div>
                    <h2 className="text-2xl font-bold mb-2">No Profile Found</h2>
                    <p className="text-gray-400 mb-4">Start interacting with content to build your profile!</p>
                    <button
                        onClick={() => navigate('/')}
                        className="px-6 py-3 rounded-md text-white font-medium transition-all duration-200"
                        style={{ background: 'var(--color-primary-500)' }}
                        onMouseEnter={e => e.target.style.background = 'var(--color-primary-600)'}
                        onMouseLeave={e => e.target.style.background = 'var(--color-primary-500)'}
                    >
                        ← Back to Home
                    </button>
                </div>
            </div>
        );
    }

    const { profile, stats } = userProfile;

    return (
        <div className="min-h-screen text-white">
            {/* ── Sticky page header ─────────────────────────────────────────────── */}
            <div className="sticky top-0 z-50 backdrop-blur-sm border-b"
                style={{ background: 'var(--color-bg-elevated)', borderColor: 'var(--color-border-primary)' }}>
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <button
                            onClick={() => navigate('/')}
                            className="flex items-center gap-2 transition-colors"
                            style={{ color: 'var(--color-text-secondary)' }}
                            onMouseEnter={e => e.currentTarget.style.color = 'var(--color-primary-500)'}
                            onMouseLeave={e => e.currentTarget.style.color = 'var(--color-text-secondary)'}
                        >
                            <ArrowLeft size={20} />
                            <span className="font-medium hidden md:block">Back to Home</span>
                        </button>
                        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-primary-500)' }}>
                            Your Profile
                        </h1>
                        <div className="md:w-32" />
                    </div>
                </div>
            </div>

            <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">
                {/* ── User card + stats ─────────────────────────────────────────────── */}
                <div className="rounded-2xl p-8 border border-gray-800"
                    style={{ background: 'var(--color-bg-elevated)' }}>
                    <div className="flex items-center gap-6 mb-6">
                        <div className="w-24 h-24 rounded-full items-center justify-center hidden md:flex"
                            style={{ background: 'var(--color-bg-secondary)' }}>
                            <User size={48} className="text-teal-500" />
                        </div>
                        <div>
                            <h2 className="text-3xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
                                {userName ? `Welcome, ${userName.split(' ')[0]}!` : (hasPreferences ? 'Welcome Back!' : 'New User')}
                            </h2>
                            <p className="text-lg" style={{ color: 'var(--color-text-secondary)' }}>
                                {hasPreferences
                                    ? 'Your personalized movie & TV show companion'
                                    : 'Start liking content to get personalized recommendations'}
                            </p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div
                            className="rounded-xl p-6 text-center transition-all hover:scale-105 cursor-pointer hover:bg-white/5 border border-transparent hover:border-red-500/30"
                            style={{ background: 'var(--color-bg-secondary)' }}
                            onClick={() => navigate('/my-list?tab=watchlist')}
                        >
                            <div className="text-4xl font-bold mb-2" style={{ color: 'var(--color-accent-red)' }}>
                                {stats?.liked_content || 0}
                            </div>
                            <div className="text-sm flex items-center justify-center gap-2" style={{ color: 'var(--color-text-secondary)' }}>
                                <Heart size={16} className="text-red-400" /> Liked Content
                            </div>
                        </div>
                        <div
                            className="rounded-xl p-6 text-center transition-all hover:scale-105 cursor-pointer hover:bg-white/5 border border-transparent hover:border-blue-500/30"
                            style={{ background: 'var(--color-bg-secondary)' }}
                            onClick={() => navigate('/my-list?tab=watchlist')}
                        >
                            <div className="text-4xl font-bold mb-2" style={{ color: 'var(--color-primary-400)' }}>
                                {stats?.watchlist_items || 0}
                            </div>
                            <div className="text-sm flex items-center justify-center gap-2" style={{ color: 'var(--color-text-secondary)' }}>
                                <Bookmark size={16} className="text-blue-400" /> Watchlist Items
                            </div>
                        </div>
                        <div
                            className="rounded-xl p-6 text-center transition-all hover:scale-105 cursor-pointer hover:bg-white/5 border border-transparent hover:border-green-500/30"
                            style={{ background: 'var(--color-bg-secondary)' }}
                            onClick={() => navigate('/my-list?tab=history')}
                        >
                            <div className="text-4xl font-bold mb-2" style={{ color: 'var(--color-accent-green)' }}>
                                {stats?.watched_items || 0}
                            </div>
                            <div className="text-sm flex items-center justify-center gap-2" style={{ color: 'var(--color-text-secondary)' }}>
                                <Check size={16} className="text-green-400" /> Watched Items
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── Streaming Subscriptions ───────────────────────────────────────── */}
                <div className="rounded-2xl p-6 sm:p-8 border border-gray-800 shadow-xl"
                    style={{ background: 'var(--color-bg-elevated)' }}>
                    {/* section header */}
                    <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-6">
                        <div>
                            <h3 className="text-xl font-bold flex items-center gap-3"
                                style={{ color: 'var(--color-text-primary)' }}>
                                <Tv className="text-teal-400" size={22} />
                                Streaming Subscriptions
                            </h3>
                            <p className="text-sm mt-1 max-w-lg" style={{ color: 'var(--color-text-secondary)' }}>
                                Select the platforms you're subscribed to — the app will only show you content
                                available on those services.
                            </p>
                        </div>

                        {/* Save button — only visible when selection has changed */}
                        {(isDirty || savedOk) && (
                            <button
                                onClick={handleSave}
                                disabled={isSaving || !isDirty}
                                className={`shrink-0 px-5 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center gap-2
                  ${savedOk && !isDirty
                                        ? 'bg-green-600/20 text-green-400 border border-green-600/40 cursor-default'
                                        : 'bg-teal-500 hover:bg-teal-600 text-white shadow-lg shadow-teal-500/20 active:scale-95 disabled:opacity-50'}`}
                            >
                                {isSaving ? (
                                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                ) : <Check size={16} />}
                                {isSaving ? 'Saving…' : savedOk && !isDirty ? 'Saved!' : 'Save Changes'}
                            </button>
                        )}
                    </div>

                    {/* Selected count badge */}
                    {selectedProviders.length > 0 && (
                        <div className="mb-4 flex items-center gap-2">
                            <span className="px-3 py-1 rounded-full text-xs font-bold bg-teal-500/15 text-teal-400 border border-teal-500/30">
                                {selectedProviders.length} platform{selectedProviders.length !== 1 ? 's' : ''} selected
                            </span>
                            <button
                                onClick={() => { setSelectedProviders([]); setSavedOk(false); }}
                                className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
                            >
                                Clear all
                            </button>
                        </div>
                    )}

                    {/* Provider grid */}
                    {providersLoading ? (
                        <div className="flex flex-col items-center justify-center py-16">
                            <div className="w-10 h-10 border-4 border-teal-500/20 border-t-teal-500 rounded-full animate-spin mb-3" />
                            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                                Fetching available platforms…
                            </p>
                        </div>
                    ) : watchProviders.length === 0 ? (
                        <p className="text-center py-8 text-gray-500">Could not load platforms. Please try again later.</p>
                    ) : (
                        <div
                            className="grid gap-3"
                            style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))' }}
                        >
                            {watchProviders.map(provider => {
                                const isSelected = selectedProviders.includes(provider.id);
                                return (
                                    <button
                                        key={provider.id}
                                        onClick={() => handleToggleProvider(provider.id)}
                                        title={provider.name}
                                        className={`group relative flex flex-col items-center gap-2 p-3 rounded-2xl border transition-all duration-200
                      ${isSelected
                                                ? 'bg-teal-500/10 border-teal-500/50 shadow-md shadow-teal-500/10'
                                                : 'bg-gray-900/50 border-gray-800 hover:border-gray-600 hover:bg-gray-800/70'}`}
                                    >
                                        {/* Logo */}
                                        <div className={`w-12 h-12 rounded-xl overflow-hidden flex-shrink-0 transition-all duration-200
                      ${isSelected ? '' : 'grayscale opacity-50 group-hover:grayscale-0 group-hover:opacity-80'}`}>
                                            {provider.logo ? (
                                                <img
                                                    src={provider.logo}
                                                    alt={provider.name}
                                                    className="w-full h-full object-cover"
                                                    loading="lazy"
                                                />
                                            ) : (
                                                <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                                                    <Tv size={20} className="text-gray-600" />
                                                </div>
                                            )}
                                        </div>

                                        {/* Check badge */}
                                        {isSelected && (
                                            <div className="absolute -top-1 -right-1 w-5 h-5 bg-teal-500 rounded-full flex items-center justify-center border-2 border-[#0d1117]">
                                                <Check size={11} className="text-white" strokeWidth={3} />
                                            </div>
                                        )}

                                        {/* Name */}
                                        <span
                                            className={`text-[10px] font-semibold text-center leading-tight line-clamp-2 w-full
                        ${isSelected ? 'text-teal-400' : 'text-gray-500 group-hover:text-gray-300'}`}
                                        >
                                            {provider.name}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* ── Taste Profile (genres + languages) ────────────────────────────── */}
                {hasPreferences ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {profile?.preferred_genres?.length > 0 && (
                            <div className="rounded-2xl p-6 border border-gray-800" style={{ background: 'var(--color-bg-elevated)' }}>
                                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                                    <Theater size={20} /> Favorite Genres
                                </h3>
                                <div className="flex flex-wrap gap-3">
                                    {profile.preferred_genres.map(genre => (
                                        <span
                                            key={genre}
                                            className="px-4 py-2 rounded-full text-sm font-medium transition-transform hover:scale-105"
                                            style={{ background: 'var(--color-primary-500)', color: 'white' }}
                                        >
                                            {genre.charAt(0).toUpperCase() + genre.slice(1)}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {profile?.preferred_languages?.length > 0 && (
                            <div className="rounded-2xl p-6 border border-gray-800" style={{ background: 'var(--color-bg-elevated)' }}>
                                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                                    <Globe size={20} /> Preferred Languages
                                </h3>
                                <div className="flex flex-wrap gap-3">
                                    {profile.preferred_languages.map(lang => {
                                        const langNames = {
                                            'en': 'English',
                                            'hi': 'Hindi',
                                            'ta': 'Tamil',
                                            'te': 'Telugu',
                                            'ml': 'Malayalam',
                                            'kn': 'Kannada'
                                        };
                                        const displayName = langNames[lang.toLowerCase()] || (lang.charAt(0).toUpperCase() + lang.slice(1));
                                        return (
                                            <span
                                                key={lang}
                                                className="px-4 py-2 rounded-full text-sm font-medium transition-transform hover:scale-105"
                                                style={{ background: 'var(--color-accent-blue)', color: 'white' }}
                                            >
                                                {displayName}
                                            </span>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="rounded-2xl p-12 text-center border border-gray-800" style={{ background: 'var(--color-bg-elevated)' }}>
                        <div className="mb-4 flex justify-center"><Film size={64} className="text-teal-500" /></div>
                        <h3 className="text-2xl font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>
                            Start Building Your Profile
                        </h3>
                        <p className="text-lg mb-6" style={{ color: 'var(--color-text-secondary)' }}>
                            Like, dislike, or add content to your watchlist to get personalized recommendations!
                        </p>
                        <button
                            onClick={() => navigate('/')}
                            className="px-6 py-3 rounded-xl text-white font-medium transition-all duration-200"
                            style={{ background: 'var(--color-primary-500)' }}
                            onMouseEnter={e => e.target.style.background = 'var(--color-primary-600)'}
                            onMouseLeave={e => e.target.style.background = 'var(--color-primary-500)'}
                        >
                            Browse Content
                        </button>
                    </div>
                )}

            </main>
        </div>
    );
};

export default ProfilePage;
