import httpx
import asyncio
from config.constants import (
    TMDB_API_KEY, TMDB_API_URL, API_CONFIG, 
    IMAGE_CONFIG, get_genre_id, get_date_range
)

class TMDBService:
    @staticmethod
    async def fetch_movies(language_code: str, genre: str, date_from: str, date_to: str):
        """Fetch movies with date filtering and correct genre ID"""
        movies = []
        movie_genre_id = get_genre_id(genre, 'movie')
        
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                print(f"Fetching movies from {date_from} to {date_to} with genre ID {movie_genre_id}")
                
                # Popular movies within date range
                popular_response = await client.get(f"{TMDB_API_URL}/discover/movie", params={
                    "api_key": TMDB_API_KEY,
                    "with_genres": movie_genre_id,
                    "with_original_language": language_code,
                    "primary_release_date.gte": date_from,
                    "primary_release_date.lte": date_to,
                    "sort_by": "popularity.desc",
                    "vote_count.gte": API_CONFIG['MIN_VOTE_COUNT']['POPULAR'],
                    "page": 1
                })
                
                if popular_response.status_code == 200:
                    popular_movies = popular_response.json().get('results', [])
                    print(f"Found {len(popular_movies)} movies in date range")
                    
                    for movie in popular_movies:
                        movies.append({
                            "id": movie['id'],
                            "title": movie['title'],
                            "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{movie['poster_path']}" if movie.get('poster_path') else None,
                            "rating": movie.get('vote_average', 0),
                            "year": movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                            "overview": movie.get('overview', ''),
                            "content_type": "movie",
                            "release_date": movie.get('release_date', ''),
                            "genre_ids": movie.get('genre_ids', []),
                            "original_language": movie.get('original_language', 'en'),
                            "popularity": movie.get('popularity', 0),
                            "vote_count": movie.get('vote_count', 0)
                        })
                
                # If not enough movies, try with recent releases
                if len(movies) < 10:
                    recent_response = await client.get(f"{TMDB_API_URL}/discover/movie", params={
                        "api_key": TMDB_API_KEY,
                        "with_genres": movie_genre_id,
                        "with_original_language": language_code,
                        "primary_release_date.gte": date_from,
                        "primary_release_date.lte": date_to,
                        "sort_by": "release_date.desc",
                        "vote_count.gte": API_CONFIG['MIN_VOTE_COUNT']['RECENT'],
                        "page": 1
                    })
                    
                    if recent_response.status_code == 200:
                        recent_movies = recent_response.json().get('results', [])
                        print(f"Found {len(recent_movies)} additional movies")
                        
                        existing_ids = {movie['id'] for movie in movies}
                        for movie in recent_movies:
                            if movie['id'] not in existing_ids:
                                movies.append({
                                    "id": movie['id'],
                                    "title": movie['title'],
                                    "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{movie['poster_path']}" if movie.get('poster_path') else None,
                                    "rating": movie.get('vote_average', 0),
                                    "year": movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                                    "overview": movie.get('overview', ''),
                                    "content_type": "movie",
                                    "release_date": movie.get('release_date', '')
                                })
            
            except Exception as e:
                print(f"Error fetching movies: {e}")
        
        return movies[:API_CONFIG['MAX_RESULTS_PER_TYPE']]

    @staticmethod
    async def fetch_tv_shows(language_code: str, genre: str, date_from: str, date_to: str):
        """Fetch TV shows with recent episodes/seasons using hybrid approach"""
        tv_shows = []
        tv_shows_dict = {}  # Use dict to avoid duplicates
        tv_genre_id = get_genre_id(genre, 'tv')
        
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                print(f"Fetching TV shows from {date_from} to {date_to} with genre ID {tv_genre_id}")
                
                # Approach 1: Get shows currently on the air
                try:
                    on_air_response = await client.get(f"{TMDB_API_URL}/tv/on_the_air", params={
                        "api_key": TMDB_API_KEY,
                        "page": 1
                    })
                    
                    if on_air_response.status_code == 200:
                        on_air_shows = on_air_response.json().get('results', [])
                        print(f"Found {len(on_air_shows)} shows currently on the air")
                        
                        for show in on_air_shows:
                            if show.get('original_language') == language_code and tv_genre_id in show.get('genre_ids', []):
                                tv_shows_dict[show['id']] = show
                except Exception as e:
                    print(f"Error fetching on_the_air shows: {e}")
                
                # Approach 2: Use discover with air_date to catch shows with recent episodes
                try:
                    discover_response = await client.get(f"{TMDB_API_URL}/discover/tv", params={
                        "api_key": TMDB_API_KEY,
                        "with_genres": tv_genre_id,
                        "with_original_language": language_code,
                        "air_date.gte": date_from,
                        "air_date.lte": date_to,
                        "sort_by": "popularity.desc",
                        "page": 1
                    })
                    
                    if discover_response.status_code == 200:
                        discover_shows = discover_response.json().get('results', [])
                        print(f"Found {len(discover_shows)} shows from discover with air_date filter")
                        
                        for show in discover_shows:
                            tv_shows_dict[show['id']] = show
                except Exception as e:
                    print(f"Error fetching discover shows: {e}")
                
                # Approach 3: Get recently aired shows (airing_today)
                try:
                    airing_today_response = await client.get(f"{TMDB_API_URL}/tv/airing_today", params={
                        "api_key": TMDB_API_KEY,
                        "page": 1
                    })
                    
                    if airing_today_response.status_code == 200:
                        airing_today_shows = airing_today_response.json().get('results', [])
                        print(f"Found {len(airing_today_shows)} shows airing today")
                        
                        for show in airing_today_shows:
                            if show.get('original_language') == language_code and tv_genre_id in show.get('genre_ids', []):
                                tv_shows_dict[show['id']] = show
                except Exception as e:
                    print(f"Error fetching airing_today shows: {e}")
                
                # Now fetch details for each unique show and check last_air_date
                print(f"Checking {len(tv_shows_dict)} unique shows for last_air_date")
                
                for show_id, show in tv_shows_dict.items():
                    try:
                        details_response = await client.get(f"{TMDB_API_URL}/tv/{show_id}", params={
                            "api_key": TMDB_API_KEY
                        })
                        
                        if details_response.status_code == 200:
                            details = details_response.json()
                            last_air_date = details.get('last_air_date', '')
                            
                            # Check if last air date is within our date range
                            if last_air_date and last_air_date >= date_from and last_air_date <= date_to:
                                tv_shows.append({
                                    "id": show['id'],
                                    "title": show.get('name', show.get('title', 'Unknown')),
                                    "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{show['poster_path']}" if show.get('poster_path') else None,
                                    "rating": show.get('vote_average', 0),
                                    "year": show.get('first_air_date', '')[:4] if show.get('first_air_date') else '',
                                    "overview": show.get('overview', ''),
                                    "content_type": "tv",
                                    "release_date": show.get('first_air_date', ''),
                                    "last_air_date": last_air_date,
                                    "genre_ids": show.get('genre_ids', []),
                                    "original_language": show.get('original_language', 'en'),
                                    "popularity": show.get('popularity', 0),
                                    "vote_count": show.get('vote_count', 0)
                                })
                                print(f"✓ Added: {show.get('name')} (last aired: {last_air_date})")
                            else:
                                print(f"✗ Skipped: {show.get('name')} (last aired: {last_air_date}, outside range {date_from} to {date_to})")
                    except Exception as e:
                        print(f"Error fetching details for show {show_id}: {e}")
                        continue
                
                # If still not enough shows, add new shows from discover (by first_air_date)
                if len(tv_shows) < 10:
                    print(f"Only found {len(tv_shows)} shows with recent episodes, supplementing with new shows")
                    new_shows_response = await client.get(f"{TMDB_API_URL}/discover/tv", params={
                        "api_key": TMDB_API_KEY,
                        "with_genres": tv_genre_id,
                        "with_original_language": language_code,
                        "first_air_date.gte": date_from,
                        "first_air_date.lte": date_to,
                        "sort_by": "popularity.desc",
                        "vote_count.gte": API_CONFIG['MIN_VOTE_COUNT']['RECENT'],
                        "page": 1
                    })
                    
                    if new_shows_response.status_code == 200:
                        new_shows = new_shows_response.json().get('results', [])
                        existing_ids = {show['id'] for show in tv_shows}
                        
                        for show in new_shows:
                            if show['id'] not in existing_ids:
                                tv_shows.append({
                                    "id": show['id'],
                                    "title": show.get('name', show.get('title', 'Unknown')),
                                    "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{show['poster_path']}" if show.get('poster_path') else None,
                                    "rating": show.get('vote_average', 0),
                                    "year": show.get('first_air_date', '')[:4] if show.get('first_air_date') else '',
                                    "overview": show.get('overview', ''),
                                    "content_type": "tv",
                                    "release_date": show.get('first_air_date', ''),
                                    "genre_ids": show.get('genre_ids', []),
                                    "original_language": show.get('original_language', 'en'),
                                    "popularity": show.get('popularity', 0),
                                    "vote_count": show.get('vote_count', 0)
                                })
            
            except Exception as e:
                print(f"Error fetching TV shows: {e}")
        
        # Sort by popularity and return top results
        tv_shows.sort(key=lambda x: x.get('popularity', 0), reverse=True)
        print(f"Returning {len(tv_shows[:API_CONFIG['MAX_RESULTS_PER_TYPE']])} TV shows")
        return tv_shows[:API_CONFIG['MAX_RESULTS_PER_TYPE']]

    @staticmethod
    async def search_movies_globally(query: str):
        """Search movies globally using TMDB search API"""
        movies = []
        
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                print(f"Global search for movies: {query}")
                
                search_response = await client.get(f"{TMDB_API_URL}/search/movie", params={
                    "api_key": TMDB_API_KEY,
                    "query": query,
                    "page": 1,
                    "include_adult": False
                })
                
                if search_response.status_code == 200:
                    search_results = search_response.json().get('results', [])
                    print(f"Found {len(search_results)} movies in global search")
                    
                    for movie in search_results[:API_CONFIG['MAX_SEARCH_RESULTS']]:
                        if IMAGE_CONFIG['REQUIRE_POSTER'] and not movie.get('poster_path'):
                            continue
                            
                        movies.append({
                            "id": movie['id'],
                            "title": movie['title'],
                            "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{movie['poster_path']}" if movie.get('poster_path') else None,
                            "rating": movie.get('vote_average', 0),
                            "year": movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                            "overview": movie.get('overview', ''),
                            "content_type": "movie",
                            "release_date": movie.get('release_date', '')
                        })
            
            except Exception as e:
                print(f"Error in global movie search: {e}")
        
        return movies

    @staticmethod
    async def search_tv_shows_globally(query: str):
        """Search TV shows globally using TMDB search API"""
        tv_shows = []
        
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                print(f"Global search for TV shows: {query}")
                
                search_response = await client.get(f"{TMDB_API_URL}/search/tv", params={
                    "api_key": TMDB_API_KEY,
                    "query": query,
                    "page": 1,
                    "include_adult": False
                })
                
                if search_response.status_code == 200:
                    search_results = search_response.json().get('results', [])
                    print(f"Found {len(search_results)} TV shows in global search")
                    
                    for show in search_results[:API_CONFIG['MAX_SEARCH_RESULTS']]:
                        if IMAGE_CONFIG['REQUIRE_POSTER'] and not show.get('poster_path'):
                            continue
                            
                        tv_shows.append({
                            "id": show['id'],
                            "title": show.get('name', show.get('title', 'Unknown')),
                            "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{show['poster_path']}" if show.get('poster_path') else None,
                            "rating": show.get('vote_average', 0),
                            "year": show.get('first_air_date', '')[:4] if show.get('first_air_date') else '',
                            "overview": show.get('overview', ''),
                            "content_type": "tv",
                            "release_date": show.get('first_air_date', '')
                        })
            
            except Exception as e:
                print(f"Error in global TV search: {e}")
        
        return tv_shows
