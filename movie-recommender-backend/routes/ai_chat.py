from fastapi import APIRouter, HTTPException
import asyncio
from datetime import datetime
from models.request_models import AIChatRequest
from services.ollama_service import OllamaService
from services.simple_recommender import SimpleRecommender
from routes.discovery import get_content_with_date_filtering
from routes.search import global_search_with_ott_filtering
from config.constants import LANGUAGE_MAP

router = APIRouter()

@router.post("/ai-chat")
async def ai_chat_recommendation(request: AIChatRequest):
    """AI recommendations with proper content prioritization"""
    try:
        user_message = request.message.strip()
        conversation_history = request.conversation_history or []
        
        print(f"🤖 AI Chat request: '{user_message}'")
        
        # Try AI first
        ai_data = None
        try:
            print("🔄 Trying AI response...")
            
            ai_prompt = f"""User request: "{user_message}"

Respond with EXACTLY this JSON format:
{{
    "response": "Your friendly response",
    "search_criteria": {{
        "genre": "action",
        "language": "english", 
        "content_type": "tv"
    }},
    "suggested_titles": ["Title1", "Title2", "Title3"]
}}

Use appropriate genre, language, and content_type based on the request."""

            ai_text = await OllamaService.get_ai_response(ai_prompt, temperature=0.1)
            
            if ai_text:
                fallback_data = SimpleRecommender.analyze_request(user_message)
                ai_data = OllamaService.parse_json_response(ai_text, fallback_data)
                print("✅ Using AI response")
            else:
                raise Exception("No AI response")
                
        except Exception as e:
            print(f"⚠️ AI failed, using smart fallback: {e}")
            ai_data = SimpleRecommender.analyze_request(user_message)
        
        # Extract search criteria
        search_criteria = ai_data.get('search_criteria', {})
        genre = search_criteria.get('genre', 'action')
        language = search_criteria.get('language', 'english')
        content_type = search_criteria.get('content_type', 'tv')
        
        print(f"🎯 Final params - Genre: '{genre}', Language: {language}, Content: {content_type}")
        
        # PRIORITIZE SPECIFIC SEARCH RESULTS OVER GENERIC RESULTS
        suggested_titles = ai_data.get('suggested_titles', [])
        specific_content = []
        
        if suggested_titles:
            print(f"🔎 Searching SPECIFIC titles first: {suggested_titles}")
            for title in suggested_titles:
                try:
                    title_results = await global_search_with_ott_filtering(title)
                    specific_content.extend(title_results)
                    print(f"  - '{title}': found {len(title_results)} results")
                    
                    if title_results:
                        found_titles = [item.get('title', 'Unknown') for item in title_results]
                        print(f"    Specific titles: {found_titles}")
                        
                except Exception as e:
                    print(f"  - '{title}': error {e}")
                    continue
        
        print(f"📊 SPECIFIC content found: {len(specific_content)} items")
        
        # Only add generic content if we don't have enough specific results
        generic_content = []
        if len(specific_content) < 10:  # Only if we need more
            print(f"🔍 Need more content, searching generic {genre} {content_type}...")
            language_code = LANGUAGE_MAP.get(language, 'en')
            generic_results = await get_content_with_date_filtering(language_code, content_type, genre, '2years')
            
            # Filter out generic results that aren't related to the search
            if 'marvel' in user_message.lower() or 'superhero' in user_message.lower():
                # For Marvel/superhero requests, filter generic content
                filtered_generic = []
                marvel_keywords = ['marvel', 'superhero', 'hero', 'comic', 'dc', 'batman', 'superman', 'avengers']
                
                for item in generic_results:
                    title_lower = item.get('title', '').lower()
                    overview_lower = item.get('overview', '').lower()
                    
                    if any(keyword in title_lower or keyword in overview_lower for keyword in marvel_keywords):
                        filtered_generic.append(item)
                
                generic_content = filtered_generic[:5]  # Limit generic results
                print(f"📊 FILTERED generic content: {len(generic_content)} items (Marvel-related only)")
            else:
                generic_content = generic_results[:8]  # Normal case
                print(f"📊 GENERIC content: {len(generic_content)} items")
        
        # Combine with SPECIFIC content first
        all_content = specific_content + generic_content
        print(f"📊 Combined: {len(specific_content)} specific + {len(generic_content)} generic = {len(all_content)} total")
        
        # Deduplication
        unique_content = []
        seen_ids = set()
        
        for item in all_content:
            if item['id'] not in seen_ids:
                seen_ids.add(item['id'])
                unique_content.append(item)
        
        print(f"📊 After deduplication: {len(unique_content)} items")
        
        # Sort with HEAVY preference for specific search results
        def sort_key(item):
            base_rating = item.get('rating', 0)
            title = item.get('title', '').lower()
            
            # Check if this was from specific search
            is_specific = any(
                suggested_title.lower() in title or 
                any(word in title for word in suggested_title.lower().split())
                for suggested_title in suggested_titles
            )
            
            if is_specific:
                boosted_rating = base_rating + 5  # HEAVY boost for specific results
                print(f"⭐⭐⭐ SPECIFIC MATCH '{item.get('title', 'Unknown')}': {base_rating} → {boosted_rating}")
                return boosted_rating
            
            return base_rating
        
        unique_content.sort(key=sort_key, reverse=True)
        
        # Limit final results
        final_recommendations = unique_content[:15]
        
        print(f"📈 Final breakdown:")
        print(f"  - Specific results prioritized: {len([item for item in final_recommendations if any(suggested_title.lower() in item.get('title', '').lower() for suggested_title in suggested_titles)])}")
        print(f"  - Generic results: {len(final_recommendations) - len([item for item in final_recommendations if any(suggested_title.lower() in item.get('title', '').lower() for suggested_title in suggested_titles)])}")
        
        # Log final titles
        if final_recommendations:
            final_titles = [f"{item.get('title', 'Unknown')} ({item.get('content_type', 'unknown')})" for item in final_recommendations]
            print(f"📤 FINAL TITLES: {final_titles}")
        
        return {
            "ai_response": ai_data.get('response', ''),
            "recommendations": final_recommendations,
            "query_analysis": {
                "detected_genre": genre,
                "detected_language": language,
                "detected_content_type": content_type,
                "mood": "prioritized_search",
                "traits": [f"specific_titles: {suggested_titles}"]
            },
            "total_found": len(final_recommendations),
            "conversation_context": conversation_history + [{
                "user": user_message,
                "ai": ai_data.get('response', ''),
                "timestamp": datetime.now().isoformat()
            }]
        }
        
    except Exception as e:
        print(f"❌ Complete error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "ai_response": "I'm having some technical difficulties, but I can still help you find great content!",
            "recommendations": [],
            "query_analysis": {"detected_genre": "action", "detected_language": "english", "detected_content_type": "tv"},
            "total_found": 0,
            "conversation_context": conversation_history
        }
