import { useNavigate } from 'react-router-dom';
import { Film, User, Heart, Bookmark, Zap, Sparkles, Theater, Globe, Smartphone, ThumbsDown, CheckCircle, ArrowLeft } from 'lucide-react';

const ProfilePage = ({
    userProfile,
    onGetPersonalizedRecommendations,
    hasPreferences,
    loading
}) => {
    const navigate = useNavigate();

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
                        onMouseEnter={(e) => e.target.style.background = 'var(--color-primary-600)'}
                        onMouseLeave={(e) => e.target.style.background = 'var(--color-primary-500)'}
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
            {/* Header */}
            <div className="sticky top-0 z-50 backdrop-blur-sm border-b" style={{ background: 'var(--color-bg-elevated)', borderColor: 'var(--color-border-primary)' }}>
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <button
                            onClick={() => navigate('/')}
                            className="flex items-center gap-2 transition-colors"
                            style={{ color: 'var(--color-text-secondary)' }}
                            onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-primary-500)'}
                            onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-secondary)'}
                        >
                            <ArrowLeft size={20} />
                            <span className="font-medium">Back to Home</span>
                        </button>
                        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-primary-500)' }}>
                            Your Profile
                        </h1>
                        <div className="w-32"></div> {/* Spacer for centering */}
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-8">
                {/* Profile Header */}
                <div className="rounded-lg p-8 mb-8" style={{ background: 'var(--color-bg-elevated)' }}>
                    <div className="flex items-center gap-6 mb-6">
                        <div className="w-24 h-24 rounded-full flex items-center justify-center" style={{ background: 'var(--color-bg-secondary)' }}>
                            <User size={48} className="text-teal-500" />
                        </div>
                        <div>
                            <h2 className="text-3xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
                                {hasPreferences ? 'Welcome Back!' : 'New User'}
                            </h2>
                            <p className="text-lg" style={{ color: 'var(--color-text-secondary)' }}>
                                {hasPreferences
                                    ? 'Your personalized movie & TV show companion'
                                    : 'Start liking content to get personalized recommendations'}
                            </p>
                        </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="rounded-lg p-6 text-center transition-transform hover:scale-105" style={{ background: 'var(--color-bg-secondary)' }}>
                            <div className="text-4xl font-bold mb-2" style={{ color: 'var(--color-accent-red)' }}>
                                {stats?.liked_content || 0}
                            </div>
                            <div className="text-sm flex items-center justify-center gap-2" style={{ color: 'var(--color-text-secondary)' }}>
                                <Heart size={16} className="text-red-400" /> Liked Content
                            </div>
                        </div>
                        <div className="rounded-lg p-6 text-center transition-transform hover:scale-105" style={{ background: 'var(--color-bg-secondary)' }}>
                            <div className="text-4xl font-bold mb-2" style={{ color: 'var(--color-primary-400)' }}>
                                {stats?.watchlist_items || 0}
                            </div>
                            <div className="text-sm flex items-center justify-center gap-2" style={{ color: 'var(--color-text-secondary)' }}>
                                <Bookmark size={16} className="text-blue-400" /> Watchlist Items
                            </div>
                        </div>
                        <div className="rounded-lg p-6 text-center transition-transform hover:scale-105" style={{ background: 'var(--color-bg-secondary)' }}>
                            <div className="text-4xl font-bold mb-2" style={{ color: 'var(--color-accent-green)' }}>
                                {stats?.total_interactions || 0}
                            </div>
                            <div className="text-sm flex items-center justify-center gap-2" style={{ color: 'var(--color-text-secondary)' }}>
                                <Zap size={16} className="text-yellow-400" /> Total Interactions
                            </div>
                        </div>
                    </div>

                    {/* Get Recommendations Button */}
                    {hasPreferences && (
                        <div className="mt-6 text-center">
                            <button
                                onClick={() => {
                                    onGetPersonalizedRecommendations();
                                    navigate('/');
                                }}
                                disabled={loading}
                                className="px-8 py-3 rounded-md text-white font-medium transition-all duration-200 flex items-center gap-3 mx-auto disabled:opacity-50 disabled:cursor-not-allowed"
                                style={{ background: 'var(--color-primary-500)' }}
                                onMouseEnter={(e) => !loading && (e.target.style.background = 'var(--color-primary-600)')}
                                onMouseLeave={(e) => !loading && (e.target.style.background = 'var(--color-primary-500)')}
                            >
                                {loading ? (
                                    <>
                                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                        Getting Recommendations...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles size={20} /> Get Personalized Recommendations
                                    </>
                                )}
                            </button>
                        </div>
                    )}
                </div>

                {/* Preferences Section */}
                {hasPreferences ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Preferred Genres */}
                        {profile.preferred_genres && profile.preferred_genres.length > 0 && (
                            <div className="rounded-lg p-6" style={{ background: 'var(--color-bg-elevated)' }}>
                                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                                    <Theater size={20} /> Favorite Genres
                                </h3>
                                <div className="flex flex-wrap gap-3">
                                    {profile.preferred_genres.map((genre, index) => (
                                        <span
                                            key={genre}
                                            className="px-4 py-2 rounded-full text-sm font-medium transition-transform hover:scale-105"
                                            style={{
                                                background: 'var(--color-primary-500)',
                                                color: 'white'
                                            }}
                                        >
                                            {genre.charAt(0).toUpperCase() + genre.slice(1)}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Preferred Languages */}
                        {profile.preferred_languages && profile.preferred_languages.length > 0 && (
                            <div className="rounded-lg p-6" style={{ background: 'var(--color-bg-elevated)' }}>
                                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                                    <Globe size={20} /> Preferred Languages
                                </h3>
                                <div className="flex flex-wrap gap-3">
                                    {profile.preferred_languages.map((language) => (
                                        <span
                                            key={language}
                                            className="px-4 py-2 rounded-full text-sm font-medium transition-transform hover:scale-105"
                                            style={{
                                                background: 'var(--color-accent-blue)',
                                                color: 'white'
                                            }}
                                        >
                                            {language.charAt(0).toUpperCase() + language.slice(1)}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="rounded-lg p-12 text-center" style={{ background: 'var(--color-bg-elevated)' }}>
                        <div className="mb-4 flex justify-center"><Film size={64} className="text-teal-500" /></div>
                        <h3 className="text-2xl font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>
                            Start Building Your Profile
                        </h3>
                        <p className="text-lg mb-6" style={{ color: 'var(--color-text-secondary)' }}>
                            Like, dislike, or add content to your watchlist to get personalized recommendations!
                        </p>
                        <button
                            onClick={() => navigate('/')}
                            className="px-6 py-3 rounded-md text-white font-medium transition-all duration-200"
                            style={{ background: 'var(--color-primary-500)' }}
                            onMouseEnter={(e) => e.target.style.background = 'var(--color-primary-600)'}
                            onMouseLeave={(e) => e.target.style.background = 'var(--color-primary-500)'}
                        >
                            Browse Content
                        </button>
                    </div>
                )}

                {/* Recent Activity */}
                {userProfile.recent_activity && userProfile.recent_activity.length > 0 && (
                    <div className="mt-8 rounded-lg p-6" style={{ background: 'var(--color-bg-elevated)' }}>
                        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                            <Smartphone size={20} /> Recent Activity
                        </h3>
                        <div className="space-y-3">
                            {userProfile.recent_activity.map((activity, index) => (
                                <div
                                    key={index}
                                    className="flex items-center gap-4 p-4 rounded-lg transition-all hover:scale-[1.02]"
                                    style={{ background: 'var(--color-bg-secondary)' }}
                                >
                                    <span className="text-2xl">
                                        {activity.action === 'liked' && <Heart size={24} className="text-red-400" />}
                                        {activity.action === 'disliked' && <ThumbsDown size={24} className="text-gray-400" />}
                                        {activity.action === 'watchlisted' && <Bookmark size={24} className="text-blue-400" />}
                                        {activity.action === 'watched' && <CheckCircle size={24} className="text-green-400" />}
                                    </span>
                                    <div className="flex-1">
                                        <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                                            {activity.action.charAt(0).toUpperCase() + activity.action.slice(1)}
                                        </span>
                                        <span style={{ color: 'var(--color-text-secondary)' }}> "{activity.title}"</span>
                                    </div>
                                    <span className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
                                        {new Date(activity.timestamp).toLocaleDateString()}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default ProfilePage;
