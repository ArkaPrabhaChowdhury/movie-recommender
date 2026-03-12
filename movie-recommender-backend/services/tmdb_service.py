import httpx
import asyncio
from config.constants import (
    TMDB_API_KEY, TMDB_API_URL, API_CONFIG, 
    IMAGE_CONFIG, get_genre_id, get_date_range
)

class TMDBService:
    @staticmethod
    async def fetch_movies(language_code: str, genre: str, date_from: str, date_to: str, page: int = 1):
        """Fetch movies with date filtering and correct genre ID"""
        movies = []
        movie_genre_id = get_genre_id(genre, 'movie')
        
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                print(f"Fetching movies from {date_from} to {date_to} with genre ID {movie_genre_id}")
                
                print(f"Fetching movies from {date_from} to {date_to} with genre ID {movie_genre_id} and lang {language_code}")
                
                # Fetch multiple pages to ensure enough OTT-available content survives the filter
                all_raw_movies = []
                # Fetch 3-page chunks based on overall requested page
                start_tmdb_page = (page - 1) * 3 + 1
                for tmdb_page in range(start_tmdb_page, start_tmdb_page + 3): 
                    params = {
                        "api_key": TMDB_API_KEY,
                        "with_genres": movie_genre_id,
                        "with_original_language": language_code,
                        "primary_release_date.gte": date_from,
                        "primary_release_date.lte": date_to,
                        "sort_by": "popularity.desc",
                        "vote_count.gte": API_CONFIG['MIN_VOTE_COUNT']['POPULAR'],
                        "page": tmdb_page
                    }
                    params = {k: v for k, v in params.items() if v is not None}
                    url = f"{TMDB_API_URL}/discover/movie"
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        all_raw_movies.extend(response.json().get('results', []))
                    else:
                        break

                print(f"Total raw movies fetched: {len(all_raw_movies)}")
                
                for movie in all_raw_movies:
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
                
                # If not enough movies, try with recent releases (already covered by 3 pages of popular mostly, but depth helps)
                if len(movies) < 15:
                    params = {
                        "api_key": TMDB_API_KEY,
                        "with_genres": movie_genre_id,
                        "with_original_language": language_code,
                        "primary_release_date.gte": date_from,
                        "primary_release_date.lte": date_to,
                        "sort_by": "release_date.desc",
                        "vote_count.gte": API_CONFIG['MIN_VOTE_COUNT']['RECENT'],
                        "page": 1
                    }
                    params = {k: v for k, v in params.items() if v is not None}
                    recent_response = await client.get(f"{TMDB_API_URL}/discover/movie", params=params)
                    
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
    async def fetch_tv_shows(language_code: str, genre: str, date_from: str, date_to: str, page: int = 1):
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
                        "page": page
                    })
                    
                    if on_air_response.status_code == 200:
                        on_air_shows = on_air_response.json().get('results', [])
                        print(f"Found {len(on_air_shows)} shows currently on the air")
                        
                        for show in on_air_shows:
                            lang_match = language_code is None or show.get('original_language') == language_code
                            genre_match = tv_genre_id is None or tv_genre_id in show.get('genre_ids', [])
                            if lang_match and genre_match:
                                tv_shows_dict[show['id']] = show
                except Exception as e:
                    print(f"Error fetching on_the_air shows: {e}")
                
                # Approach 2: Use discover with air_date to catch shows with recent episodes
                try:
                    params = {
                        "api_key": TMDB_API_KEY,
                        "with_genres": tv_genre_id,
                        "with_original_language": language_code,
                        "air_date.gte": date_from,
                        "air_date.lte": date_to,
                        "sort_by": "popularity.desc",
                        "page": page
                    }
                    params = {k: v for k, v in params.items() if v is not None}
                    discover_response = await client.get(f"{TMDB_API_URL}/discover/tv", params=params)
                    
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
                        "page": page
                    })
                    
                    if airing_today_response.status_code == 200:
                        airing_today_shows = airing_today_response.json().get('results', [])
                        print(f"Found {len(airing_today_shows)} shows airing today")
                        
                        for show in airing_today_shows:
                            lang_match = language_code is None or show.get('original_language') == language_code
                            genre_match = tv_genre_id is None or tv_genre_id in show.get('genre_ids', [])
                            if lang_match and genre_match:
                                tv_shows_dict[show['id']] = show
                except Exception as e:
                    print(f"Error fetching airing_today shows: {e}")
                
                # Now fetch details for each unique show and check last_air_date
                print(f"Checking {len(tv_shows_dict)} unique shows for last_air_date")
                
                async def fetch_show_details(show_id, show):
                    try:
                        details_response = await client.get(f"{TMDB_API_URL}/tv/{show_id}", params={
                            "api_key": TMDB_API_KEY
                        })
                        
                        if details_response.status_code == 200:
                            details = details_response.json()
                            last_air_date = details.get('last_air_date', '')
                            
                            # Check if last air date is within our date range
                            if last_air_date and last_air_date >= date_from and last_air_date <= date_to:
                                return {
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
                                }
                        return None
                    except Exception as e:
                        print(f"Error fetching details for show {show_id}: {e}")
                        return None

                # Parallel fetch details
                details_tasks = [fetch_show_details(sid, s) for sid, s in tv_shows_dict.items()]
                details_results = await asyncio.gather(*details_tasks)
                
                # Filter out None results and add to tv_shows
                for result in details_results:
                    if result:
                        tv_shows.append(result)
                
                # If still not enough shows or specifically requested, add popular shows from discover
                if len(tv_shows) < 30:
                    print(f"Supplementing with popular TV shows for language {language_code}")
                    params = {
                        "api_key": TMDB_API_KEY,
                        "with_genres": tv_genre_id,
                        "with_original_language": language_code,
                        "sort_by": "popularity.desc",
                        "vote_count.gte": 5 if language_code != 'hi' else 0, # Hindi content sometimes has very few votes
                        "page": page
                    }
                    params = {k: v for k, v in params.items() if v is not None}
                    pop_response = await client.get(f"{TMDB_API_URL}/discover/tv", params=params)
                    
                    if pop_response.status_code == 200:
                        pop_shows = pop_response.json().get('results', [])
                        existing_ids = {show['id'] for show in tv_shows}
                        
                        for show in pop_shows:
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

    @staticmethod
    async def get_content_details(content_id: int, content_type: str):
        """Get detailed information, credits, and videos for a specific movie or TV show"""
        if content_type not in ['movie', 'tv']:
            raise ValueError("content_type must be 'movie' or 'tv'")
            
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                print(f"Fetching details for {content_type} {content_id}")
                
                # Fetch details, credits, videos, and similar all in one request using append_to_response
                response = await client.get(
                    f"{TMDB_API_URL}/{content_type}/{content_id}", 
                    params={
                        "api_key": TMDB_API_KEY,
                        "append_to_response": "credits,videos,similar"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format the response
                    videos = [v for v in data.get('videos', {}).get('results', []) if v['site'] == 'YouTube' and v['type'] in ['Trailer', 'Teaser']]
                    cast = data.get('credits', {}).get('cast', [])[:10]  # Get top 10 cast
                    director = []
                    if content_type == 'movie':
                        director = [crew for crew in data.get('credits', {}).get('crew', []) if crew['job'] == 'Director']
                    else:
                        director = [crew for crew in data.get('created_by', [])]
                        
                    similar_raw = data.get('similar', {}).get('results', [])[:6]
                    similar = []
                    for item in similar_raw:
                        similar.append({
                            "id": item['id'],
                            "title": item.get('title') if content_type == 'movie' else item.get('name'),
                            "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{item['poster_path']}" if item.get('poster_path') else None,
                            "rating": item.get('vote_average', 0),
                            "year": item.get('release_date', '')[:4] if item.get('release_date', '') else (item.get('first_air_date', '')[:4] if item.get('first_air_date', '') else ''),
                            "content_type": content_type
                        })
                        
                    return {
                        "id": data['id'],
                        "title": data.get('title') if content_type == 'movie' else data.get('name'),
                        "original_title": data.get('original_title') if content_type == 'movie' else data.get('original_name'),
                        "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{data['poster_path']}" if data.get('poster_path') else None,
                        "backdrop": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{data['backdrop_path']}" if data.get('backdrop_path') else None,
                        "rating": data.get('vote_average', 0),
                        "vote_count": data.get('vote_count', 0),
                        "year": data.get('release_date', '')[:4] if content_type == 'movie' and data.get('release_date') else (data.get('first_air_date', '')[:4] if data.get('first_air_date') else ''),
                        "release_date": data.get('release_date', '') if content_type == 'movie' else data.get('first_air_date', ''),
                        "runtime": data.get('runtime', 0) if content_type == 'movie' else (data.get('episode_run_time', [0])[0] if data.get('episode_run_time') else 0),
                        "status": data.get('status', ''),
                        "genres": data.get('genres', []),
                        "overview": data.get('overview', ''),
                        "tagline": data.get('tagline', ''),
                        "content_type": content_type,
                        "cast": [
                            {
                                "id": c['id'],
                                "name": c['name'],
                                "character": c.get('character', ''),
                                "profile_path": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{c['profile_path']}" if c.get('profile_path') else None
                            } for c in cast
                        ],
                        "director": [
                            {
                                "id": d['id'],
                                "name": d.get('name', '')
                            } for d in director
                        ],
                        "videos": videos,
                        "similar": similar,
                        "number_of_seasons": data.get('number_of_seasons') if content_type == 'tv' else None,
                        "number_of_episodes": data.get('number_of_episodes') if content_type == 'tv' else None,
                    }
                else:
                    return None
            except Exception as e:
                print(f"Error fetching details: {e}")
                return None

    @staticmethod
    async def get_watch_providers(region: str = "IN"):
        """Fetch all streaming platforms available in a region from TMDB."""
        logo_base = "https://image.tmdb.org/t/p/w92"
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                movie_resp, tv_resp = await asyncio.gather(
                    client.get(f"{TMDB_API_URL}/watch/providers/movie",
                               params={"api_key": TMDB_API_KEY, "watch_region": region}),
                    client.get(f"{TMDB_API_URL}/watch/providers/tv",
                               params={"api_key": TMDB_API_KEY, "watch_region": region})
                )

                providers: dict = {}

                for resp in (movie_resp, tv_resp):
                    if resp.status_code == 200:
                        for p in resp.json().get("results", []):
                            pid = p["provider_id"]
                            if pid not in providers:
                                providers[pid] = {
                                    "id": pid,
                                    "name": p["provider_name"],
                                    "logo": f"{logo_base}{p['logo_path']}" if p.get("logo_path") else None,
                                    "display_priorities": p.get("display_priorities", {})
                                }

                sorted_providers = sorted(
                    providers.values(),
                    key=lambda x: x["display_priorities"].get(region, 999)
                )
                # Strip internal field before returning
                for p in sorted_providers:
                    p.pop("display_priorities", None)

                print(f"✅ Fetched {len(sorted_providers)} watch providers for region {region}")
                return sorted_providers

            except Exception as e:
                print(f"❌ Error fetching watch providers: {e}")
                return []

