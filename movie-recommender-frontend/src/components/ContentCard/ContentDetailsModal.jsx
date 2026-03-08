import React, { useState, useEffect } from 'react';
import { X, Play, Star, Calendar, Clock, Film, Tv, ChevronLeft, ChevronRight } from 'lucide-react';
import ApiService from '../../services/api';
import { UI_CONFIG } from '../../config/constants';
import InteractionButtons from './InteractionButtons';

const ContentDetailsModal = ({ isOpen, onClose, contentId, contentType, onLike, onDislike, onWatchlist, onWatched, userInteractions, interactionMap = {} }) => {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeVideo, setActiveVideo] = useState(null);

    useEffect(() => {
        if (isOpen && contentId && contentType) {
            setLoading(true);
            setError(null);
            setDetails(null);
            setActiveVideo(null);

            ApiService.getDetails(contentType, contentId)
                .then(data => {
                    setDetails(data);
                    // Set first trailer as active if available
                    if (data.videos && data.videos.length > 0) {
                        setActiveVideo(data.videos[0]);
                    }
                })
                .catch(err => {
                    console.error("Failed to load details:", err);
                    setError("Failed to load content details");
                })
                .finally(() => {
                    setLoading(false);
                });
        }
    }, [isOpen, contentId, contentType]);

    // Prevent scrolling on body when modal is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 md:p-10 bg-black/80 backdrop-blur-sm">
            {/* Click outside to close */}
            <div className="absolute inset-0" onClick={onClose} />

            <div className="relative w-full max-w-5xl max-h-full bg-[#0d1117] rounded-2xl border border-gray-800 shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">

                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 z-50 p-2 bg-black/50 hover:bg-black/80 rounded-full text-white backdrop-blur-md transition-colors"
                >
                    <X size={24} />
                </button>

                {loading ? (
                    <div className="p-12 flex flex-col items-center justify-center min-h-[400px]">
                        <div className="w-12 h-12 border-4 border-teal-500/30 border-t-teal-500 rounded-full animate-spin mb-4" />
                        <p className="text-gray-400">Loading details...</p>
                    </div>
                ) : error ? (
                    <div className="p-12 flex flex-col items-center justify-center min-h-[400px] text-center">
                        <div className="text-red-500 mb-4"><X size={48} /></div>
                        <h3 className="text-xl font-bold text-white mb-2">Oops!</h3>
                        <p className="text-gray-400">{error}</p>
                        <button onClick={onClose} className="mt-6 px-6 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition">Go Back</button>
                    </div>
                ) : details ? (
                    <div className="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar">

                        {/* Header / Backdrop Section */}
                        <div className="relative w-full aspect-video md:aspect-[21/9] bg-black">
                            {activeVideo ? (
                                <iframe
                                    src={`https://www.youtube.com/embed/${activeVideo.key}?autoplay=0&mute=0&controls=1`}
                                    title={activeVideo.name}
                                    className="w-full h-full object-cover"
                                    allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowFullScreen
                                ></iframe>
                            ) : details.backdrop ? (
                                <>
                                    <img src={details.backdrop} alt={details.title} className="w-full h-full object-cover opacity-60" />
                                    <div className="absolute inset-0 bg-gradient-to-t from-[#0d1117] via-[#0d1117]/60 to-transparent" />
                                </>
                            ) : (
                                <div className="w-full h-full bg-gray-900 flex items-center justify-center">
                                    <span className="text-gray-600">No media available</span>
                                </div>
                            )}
                        </div>

                        {/* Content Info Container */}
                        <div className="relative px-6 pb-10 sm:px-10 pt-8 z-10">
                            <div className="flex flex-col md:flex-row gap-8 items-start">

                                {/* Poster */}
                                <div className="hidden md:block w-56 shrink-0 rounded-xl overflow-hidden shadow-xl border border-gray-800 bg-[#161b22]">
                                    {details.poster ? (
                                        <img src={details.poster} alt={details.title} className="w-full h-auto object-cover aspect-[2/3]" />
                                    ) : (
                                        <div className="w-full aspect-[2/3] flex items-center justify-center"><Film className="text-gray-600" size={48} /></div>
                                    )}
                                </div>

                                {/* Main Details */}
                                <div className="flex-1 w-full max-w-3xl overflow-hidden pt-1">
                                    <div className="flex flex-wrap items-center gap-3 mb-4">
                                        {details.rating > 0 && (
                                            <span className="flex items-center gap-1 text-yellow-500 font-semibold bg-yellow-500/10 px-2.5 py-1 rounded-md text-sm">
                                                <Star size={14} fill="currentColor" /> {details.rating.toFixed(1)}
                                            </span>
                                        )}
                                        {details.year && (
                                            <span className="flex items-center gap-1.5 text-gray-300 text-sm bg-gray-800/50 px-2.5 py-1 rounded-md">
                                                <Calendar size={14} className="text-gray-400" /> {details.year}
                                            </span>
                                        )}
                                        {details.runtime > 0 && (
                                            <span className="flex items-center gap-1.5 text-gray-300 text-sm bg-gray-800/50 px-2.5 py-1 rounded-md">
                                                <Clock size={14} className="text-gray-400" /> {details.runtime} min
                                            </span>
                                        )}
                                        {details.content_type === 'tv' && details.number_of_seasons > 0 && (
                                            <span className="flex items-center gap-1.5 text-gray-300 text-sm bg-gray-800/50 px-2.5 py-1 rounded-md">
                                                <Tv size={14} className="text-gray-400" /> {details.number_of_seasons} Seasons {details.number_of_episodes > 0 ? `(${details.number_of_episodes} Episodes)` : ''}
                                            </span>
                                        )}
                                        {details.content_type && (
                                            <span className="flex items-center gap-1.5 text-teal-400 bg-teal-500/10 px-2.5 py-1 rounded-md text-sm font-medium">
                                                {details.content_type === 'movie' ? <Film size={14} /> : <Tv size={14} />}
                                                {details.content_type.toUpperCase()}
                                            </span>
                                        )}
                                    </div>

                                    <h1 className="text-3xl md:text-5xl font-extrabold text-white mb-3 leading-tight tracking-tight">
                                        {details.title}
                                    </h1>

                                    {details.tagline && (
                                        <p className="text-gray-400 text-lg italic mb-6">"{details.tagline}"</p>
                                    )}

                                    {/* Actions / Buttons */}
                                    <div className="flex flex-wrap items-center gap-4 mb-6 relative h-10">
                                        <InteractionButtons
                                            item={details}
                                            onLike={onLike}
                                            onDislike={onDislike}
                                            onWatchlist={onWatchlist}
                                            onWatched={onWatched}
                                            userInteractions={userInteractions}
                                            interactionMap={interactionMap}
                                        />
                                    </div>

                                    {/* Genres */}
                                    {details.genres && details.genres.length > 0 && (
                                        <div className="flex flex-wrap gap-2.5 mb-8">
                                            {details.genres.map(g => (
                                                <span key={g.id} className="px-3.5 py-1.5 bg-white/5 border border-white/10 rounded-full text-xs font-medium text-gray-200 shadow-sm backdrop-blur-sm">
                                                    {g.name}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    {/* Overview */}
                                    <div className="mb-8">
                                        <h3 className="text-white font-semibold mb-2">Overview</h3>
                                        <p className="text-gray-300 leading-relaxed max-w-full whitespace-normal break-words">
                                            {details.overview || "No overview available."}
                                        </p>
                                    </div>

                                    {/* Available On */}
                                    {details.streaming && details.streaming.available_on && details.streaming.available_on.length > 0 && (
                                        <div className="mb-10">
                                            <h3 className="text-white text-lg font-semibold mb-4">Available On</h3>
                                            <div className="flex flex-wrap gap-3">
                                                {details.streaming.available_on.map((platform, idx) => (
                                                    <div key={idx} className="flex items-center gap-2 px-4 py-2 rounded-lg backdrop-blur-sm hover:scale-105 transition-transform" style={{ backgroundColor: `${platform.color}15`, border: `1px solid ${platform.color}30` }}>
                                                        <span className="font-medium text-sm text-white">{platform.name}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Cast */}
                                    {details.cast && details.cast.length > 0 && (
                                        <div className="mb-10 overflow-hidden">
                                            <h3 className="text-white text-lg font-semibold mb-5">Top Cast</h3>
                                            <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
                                                {details.cast.map(person => (
                                                    <div key={person.id} className="shrink-0 w-24 text-center">
                                                        <div className="w-20 h-20 mx-auto rounded-full overflow-hidden bg-gray-800 mb-3 border-2 border-gray-800 shadow-md">
                                                            {person.profile_path ? (
                                                                <img src={person.profile_path} alt={person.name} className="w-full h-full object-cover" loading="lazy" />
                                                            ) : (
                                                                <div className="w-full h-full flex items-center justify-center text-gray-500"><Star size={24} /></div>
                                                            )}
                                                        </div>
                                                        <p className="text-gray-100 text-xs font-semibold line-clamp-1">{person.name}</p>
                                                        <p className="text-gray-400 text-[10px] mt-0.5 line-clamp-1">{person.character}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Trailers/Videos */}
                                    {details.videos && details.videos.length > 1 && (
                                        <div className="mb-6">
                                            <h3 className="text-white text-lg font-semibold mb-5">More Videos</h3>
                                            <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
                                                {details.videos.filter(v => v.id !== activeVideo?.id).map(video => (
                                                    <button
                                                        key={video.id}
                                                        onClick={() => setActiveVideo(video)}
                                                        className="shrink-0 group relative w-48 aspect-video rounded-xl overflow-hidden border border-gray-700 hover:border-teal-500 transition-colors"
                                                    >
                                                        <img src={`https://img.youtube.com/vi/${video.key}/mqdefault.jpg`} alt={video.name} className="w-full h-full object-cover opacity-70 group-hover:opacity-100 transition-opacity" />
                                                        <div className="absolute inset-0 flex items-center justify-center">
                                                            <div className="w-10 h-10 rounded-full bg-black/60 backdrop-blur text-white flex items-center justify-center group-hover:bg-teal-500 group-hover:scale-110 transition-all">
                                                                <Play size={18} className="translate-x-[1px]" />
                                                            </div>
                                                        </div>
                                                        <div className="absolute bottom-0 inset-x-0 p-2 bg-gradient-to-t from-black/90 to-transparent">
                                                            <p className="text-[10px] text-white font-medium line-clamp-1">{video.name}</p>
                                                        </div>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                </div>
                            </div>
                        </div>

                    </div>
                ) : null}
            </div>
        </div>
    );
};

export default ContentDetailsModal;
