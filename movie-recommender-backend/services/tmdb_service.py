import httpx
import asyncio
from typing import Dict, List
from config.constants import (
    TMDB_API_KEY, TMDB_API_URL, API_CONFIG, 
    IMAGE_CONFIG, get_genre_id, get_date_range, SEARCH_CONTENT_OVERRIDES
)

class TMDBService:
    @staticmethod
    async def get_tv_episode_status(content_id: int) -> Dict:
        """Return TMDB's latest and upcoming episode records for a TV show."""
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                response = await client.get(
                    f"{TMDB_API_URL}/tv/{content_id}",
                    params={"api_key": TMDB_API_KEY}
                )
                if response.status_code != 200:
                    return {}

                data = response.json()
                return {
                    "show_title": data.get("name", "Unknown show"),
                    "status": data.get("status", ""),
                    "last_episode": data.get("last_episode_to_air"),
                    "next_episode": data.get("next_episode_to_air")
                }
            except Exception as e:
                print(f"Error fetching episode status for TV {content_id}: {e}")
                return {}

    @staticmethod
    async def fetch_movies(language_code: str, genre: str, date_from: str, date_to: str, page: int = 1):
        """Fetch movies with date filtering and correct genre ID"""
        movies = []
        movie_genre_id = get_genre_id(genre, 'movie')
        
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                print(f"Fetching movies from {date_from} to {date_to} with genre ID {movie_genre_id} and lang {language_code}")
                
                # Fetch multiple pages to ensure enough OTT-available content survives the filter
                all_raw_movies = []
                # Fetch 2-page chunks based on overall requested page (reduced from 3 to be faster but still deep)
                start_tmdb_page = (page - 1) * 2 + 1
                for tmdb_page in range(start_tmdb_page, start_tmdb_page + 2): 
                    params = {
                        "api_key": TMDB_API_KEY,
                        "with_genres": movie_genre_id,
                        "with_original_language": language_code,
                        "primary_release_date.gte": date_from,
                        "primary_release_date.lte": date_to,
                        "sort_by": "popularity.desc",
                        "vote_count.gte": API_CONFIG['MIN_VOTE_COUNT']['POPULAR'] if language_code != 'hi' else 0,
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
                
                # If not enough movies, supplement with popular movies (ignoring dates)
                if len(movies) < 20:
                    print(f"Supplementing with popular movies for language {language_code}")
                    params = {
                        "api_key": TMDB_API_KEY,
                        "with_genres": movie_genre_id,
                        "with_original_language": language_code,
                        "sort_by": "popularity.desc",
                        "vote_count.gte": 0,
                        "page": page
                    }
                    params = {k: v for k, v in params.items() if v is not None}
                    pop_response = await client.get(f"{TMDB_API_URL}/discover/movie", params=params)
                    
                    if pop_response.status_code == 200:
                        pop_movies = pop_response.json().get('results', [])
                        existing_ids = {movie['id'] for movie in movies}
                        for movie in pop_movies:
                            if movie['id'] not in existing_ids:
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
            
            except Exception as e:
                print(f"Error fetching movies: {e}")
        
        return movies[:API_CONFIG['MAX_RESULTS_PER_TYPE']]

    @staticmethod
    async def fetch_tv_shows(language_code: str, genre: str, date_from: str, date_to: str, page: int = 1):
        """Fetch TV shows with a robust multi-source approach"""
        tv_shows = []
        tv_shows_dict = {}
        tv_genre_id = get_genre_id(genre, 'tv')
        
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                print(f"Fetching TV shows with genre ID {tv_genre_id} and lang {language_code}")
                
                # Approach 1: Discover with broad air_date filter (essential for language-specific TV)
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
                        for show in discover_shows:
                            tv_shows_dict[show['id']] = show
                except Exception as e:
                    print(f"Error fetching discover shows: {e}")
                
                # Approach 2: Get shows currently on the air (often misses language specifics unless filtered)
                try:
                    on_air_response = await client.get(f"{TMDB_API_URL}/tv/on_the_air", params={
                        "api_key": TMDB_API_KEY,
                        "page": page
                    })
                    
                    if on_air_response.status_code == 200:
                        on_air_shows = on_air_response.json().get('results', [])
                        for show in on_air_shows:
                            # Strict filtering if language_code is provided
                            if language_code and show.get('original_language') != language_code:
                                continue
                            if tv_genre_id and tv_genre_id not in show.get('genre_ids', []):
                                continue
                            tv_shows_dict[show['id']] = show
                except Exception as e:
                    print(f"Error fetching on_the_air shows: {e}")

                # Convert to list for easier processing
                tv_shows = []
                for show in tv_shows_dict.values():
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
                
                # If still not enough shows, supplement with popular shows (ignoring dates)
                # VERY important for Hindi because many shows have old first_air_date but are still popular
                if len(tv_shows) < 20:
                    print(f"Supplementing with popular TV shows for language {language_code}")
                    params = {
                        "api_key": TMDB_API_KEY,
                        "with_genres": tv_genre_id,
                        "with_original_language": language_code,
                        "sort_by": "popularity.desc",
                        "vote_count.gte": 0,
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
        
        # Sort by popularity
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
    async def search_person_globally(query: str):
        """Search for a person and return their movie/TV credits"""
        credits = []
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                # 1. Find the person
                person_resp = await client.get(f"{TMDB_API_URL}/search/person", params={
                    "api_key": TMDB_API_KEY,
                    "query": query,
                    "include_adult": False
                })
                
                if person_resp.status_code == 200:
                    results = person_resp.json().get('results', [])
                    if not results: return []
                    
                    person = results[0] # Take the most popular match
                    person_id = person['id']
                    
                    # 2. Get their combined credits (movies + tv)
                    credits_resp = await client.get(f"{TMDB_API_URL}/person/{person_id}/combined_credits", params={
                        "api_key": TMDB_API_KEY
                    })
                    
                    if credits_resp.status_code == 200:
                        all_credits = credits_resp.json().get('cast', []) + credits_resp.json().get('crew', [])
                        # Deduplicate by ID
                        seen = set()
                        for c in all_credits:
                            if c['id'] in seen: continue
                            if IMAGE_CONFIG['REQUIRE_POSTER'] and not c.get('poster_path'): continue
                            
                            seen.add(c['id'])
                            credits.append({
                                "id": c['id'],
                                "title": c.get('title', c.get('name', 'Unknown')),
                                "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{c['poster_path']}" if c.get('poster_path') else None,
                                "rating": c.get('vote_average', 0),
                                "year": (c.get('release_date') or c.get('first_air_date') or '')[:4],
                                "overview": c.get('overview', ''),
                                "content_type": c['media_type'],
                                "popularity": c.get('popularity', 0)
                            })
                        
                        # Sort by popularity or release date
                        credits.sort(key=lambda x: x.get('popularity', 0), reverse=True)
            except Exception as e:
                print(f"Error in person search: {e}")
        
        return credits[:20]

    @staticmethod
    async def search_tv_shows_globally(query: str):
        """Search TV shows globally using TMDB search API"""
        tv_shows = []
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                search_response = await client.get(f"{TMDB_API_URL}/search/tv", params={
                    "api_key": TMDB_API_KEY,
                    "query": query,
                    "page": 1,
                    "include_adult": False
                })
                if search_response.status_code == 200:
                    results = search_response.json().get('results', [])
                    for show in results[:API_CONFIG['MAX_SEARCH_RESULTS']]:
                        if IMAGE_CONFIG['REQUIRE_POSTER'] and not show.get('poster_path'): continue
                        tv_shows.append({
                            "id": show['id'],
                            "title": show.get('name', 'Unknown'),
                            "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{show['poster_path']}" if show.get('poster_path') else None,
                            "rating": show.get('vote_average', 0),
                            "year": show.get('first_air_date', '')[:4],
                            "overview": show.get('overview', ''),
                            "content_type": "tv",
                            "release_date": show.get('first_air_date', '')
                        })
            except Exception as e: print(f"Error: {e}")
        normalized_query = query.strip().lower()
        for alias, (content_type, content_id) in SEARCH_CONTENT_OVERRIDES.items():
            if content_type != "tv" or alias not in normalized_query:
                continue
            if any(show["id"] == content_id for show in tv_shows):
                continue
            try:
                details = await TMDBService.get_content_details(content_id, content_type)
                if details and details.get("poster"):
                    tv_shows.append({
                        "id": details["id"],
                        "title": details["title"],
                        "poster": details["poster"],
                        "rating": details.get("rating", 0),
                        "year": details.get("year", ""),
                        "overview": details.get("overview", ""),
                        "content_type": content_type,
                        "release_date": details.get("release_date", ""),
                    })
            except Exception as e:
                print(f"Error loading search override for {alias}: {e}")

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
                        "append_to_response": "credits,videos,similar,recommendations"
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
                        
                    recommendation_results = data.get('recommendations', {}).get('results', [])
                    similar_results = data.get('similar', {}).get('results', [])
                    similar_raw = (recommendation_results or similar_results)[:20]
                    recommendation_source = bool(recommendation_results)
                    similar = []
                    for rank, item in enumerate(similar_raw):
                        similar.append({
                            "id": item['id'],
                            "title": item.get('title') if content_type == 'movie' else item.get('name'),
                            "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{item['poster_path']}" if item.get('poster_path') else None,
                            "rating": item.get('vote_average', 0),
                            "overview": item.get('overview', ''),
                            "vote_count": item.get('vote_count', 0),
                            "popularity": item.get('popularity', 0),
                            "genre_ids": item.get('genre_ids', []),
                            "original_language": item.get('original_language', ''),
                            "year": item.get('release_date', '')[:4] if item.get('release_date', '') else (item.get('first_air_date', '')[:4] if item.get('first_air_date', '') else ''),
                            "content_type": content_type
                            ,"source": "tmdb_recommendation" if recommendation_source else "tmdb_similar"
                            ,"similar_rank": rank
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
    async def get_trending_content(content_type: str) -> List[Dict]:
        """Fetch this week's trending titles for the requested content type."""
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                response = await client.get(
                    f"{TMDB_API_URL}/trending/{content_type}/week",
                    params={"api_key": TMDB_API_KEY},
                )
                if response.status_code != 200:
                    return []

                items = []
                for item in response.json().get('results', [])[:20]:
                    if IMAGE_CONFIG['REQUIRE_POSTER'] and not item.get('poster_path'):
                        continue
                    items.append({
                        "id": item['id'],
                        "title": item.get('title') or item.get('name', ''),
                        "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{item['poster_path']}",
                        "rating": item.get('vote_average', 0),
                        "overview": item.get('overview', ''),
                        "genre_ids": item.get('genre_ids', []),
                        "original_language": item.get('original_language', ''),
                        "popularity": item.get('popularity', 0),
                        "year": (item.get('release_date') or item.get('first_air_date') or '')[:4],
                        "content_type": content_type,
                        "is_trending": True,
                    })
                return items
            except Exception as e:
                print(f"Error fetching trending {content_type}: {e}")
                return []

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

    @staticmethod
    async def get_similar_by_title(title: str, content_type: str = 'both') -> List[Dict]:
        """Search for a title, then fetch TMDB similar recommendations for it."""
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            try:
                types_to_try = ['movie', 'tv'] if content_type == 'both' else [content_type]
                found_id, found_type = None, None

                for ct in types_to_try:
                    endpoint = 'movie' if ct == 'movie' else 'tv'
                    resp = await client.get(f"{TMDB_API_URL}/search/{endpoint}", params={
                        "api_key": TMDB_API_KEY,
                        "query": title,
                        "page": 1,
                        "include_adult": False
                    })
                    if resp.status_code == 200:
                        results = resp.json().get('results', [])
                        if results:
                            found_id = results[0]['id']
                            found_type = ct
                            break

                if not found_id:
                    return []

                sim_resp = await client.get(
                    f"{TMDB_API_URL}/{'movie' if found_type == 'movie' else 'tv'}/{found_id}/similar",
                    params={"api_key": TMDB_API_KEY, "page": 1}
                )
                if sim_resp.status_code != 200:
                    return []

                items = []
                for item in sim_resp.json().get('results', [])[:20]:
                    if IMAGE_CONFIG['REQUIRE_POSTER'] and not item.get('poster_path'):
                        continue
                    items.append({
                        "id": item['id'],
                        "title": item.get('title') or item.get('name', ''),
                        "poster": f"{IMAGE_CONFIG['TMDB_BASE_URL']}{item['poster_path']}" if item.get('poster_path') else None,
                        "rating": item.get('vote_average', 0),
                        "year": (item.get('release_date') or item.get('first_air_date') or '')[:4],
                        "overview": item.get('overview', ''),
                        "content_type": found_type,
                        "original_language": item.get('original_language', ''),
                        "source": "tmdb_similar"
                    })
                print(f"✅ TMDB similar for '{title}': {len(items)} results")
                return items
            except Exception as e:
                print(f"❌ Error in get_similar_by_title: {e}")
                return []
