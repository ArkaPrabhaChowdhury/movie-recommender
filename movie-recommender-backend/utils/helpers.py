from config.constants import MOVIE_GENRE_MAP, CONTENT_TYPE_KEYWORDS, DEFAULTS

def extract_filters_from_prompt(prompt: str):
    """Extract genre, language, and content type directly from prompt"""
    prompt_lower = prompt.lower()
    
    # Extract genre
    detected_genre = DEFAULTS['GENRE']
    for genre in MOVIE_GENRE_MAP.keys():
        if genre in prompt_lower:
            detected_genre = genre
            break
    
    # Extract language
    detected_language = DEFAULTS['LANGUAGE']
    from config.constants import LANGUAGE_MAP
    for lang in LANGUAGE_MAP.keys():
        if lang in prompt_lower:
            detected_language = lang
            break
    
    # Extract content type
    detected_content_type = DEFAULTS['CONTENT_TYPE']
    
    has_movies = any(word in prompt_lower for word in CONTENT_TYPE_KEYWORDS['MOVIE'])
    has_shows = any(word in prompt_lower for word in CONTENT_TYPE_KEYWORDS['TV'])
    
    print(f"Prompt analysis: '{prompt_lower}'")
    print(f"Has movies keywords: {has_movies}")
    print(f"Has shows keywords: {has_shows}")
    
    if has_movies and has_shows:
        detected_content_type = 'both'
        print("Detected: BOTH (movies and shows present)")
    elif has_movies and not has_shows:
        detected_content_type = 'movie'
        print("Detected: MOVIE only")
    elif has_shows and not has_movies:
        detected_content_type = 'tv'
        print("Detected: TV only")
    else:
        detected_content_type = 'both'
        print("Detected: BOTH (default - no specific keywords)")
    
    return detected_genre, detected_language, detected_content_type
