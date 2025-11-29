import httpx
import json
import re
from config.constants import OLLAMA_API_URL

class OllamaService:
    @staticmethod
    async def get_ai_response(prompt: str, temperature: float = 0.7) -> str:
        """Get response from Ollama LLM with optimized settings"""
        try:
            print(f"🔗 Connecting to Ollama at: {OLLAMA_API_URL}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(OLLAMA_API_URL, json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                    "options": {
                        "num_predict": 300,
                        "top_p": 0.9,
                        "top_k": 40
                    }
                })
                
                print(f"📡 Ollama response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    ai_text = result.get("response", "")
                    print(f"✅ Ollama response received: {len(ai_text)} characters")
                    return ai_text
                else:
                    print(f"❌ Ollama error status: {response.status_code}")
                    print(f"❌ Ollama error body: {response.text}")
                    return ""
                    
        except httpx.ConnectError as e:
            print(f"❌ Cannot connect to Ollama: {e}")
            return ""
        except httpx.TimeoutException as e:
            print(f"⏱️ Ollama request timed out: {e}")
            return ""
        except Exception as e:
            print(f"❌ Error calling Ollama: {e}")
            return ""
    
    @staticmethod
    def parse_json_response(ai_text: str, fallback_data: dict) -> dict:
        """Parse JSON from AI response with fallback and data normalization"""
        try:
            ai_text = ai_text.strip()
            print(f"🔍 Parsing AI response: {ai_text[:200]}...")
            
            # Multiple patterns to find JSON
            json_patterns = [
                r'\{[^{}]*"response"[^{}]*"search_criteria"[^{}]*\}',
                r'\{.*?"response".*?\}',
                r'\{.*\}'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, ai_text, re.DOTALL)
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        if isinstance(parsed, dict) and "response" in parsed:
                            # ALWAYS normalize the parsed data
                            normalized = OllamaService._normalize_ai_response(parsed)
                            print(f"✅ Successfully parsed and normalized JSON")
                            return normalized
                    except json.JSONDecodeError:
                        continue
            
            print(f"⚠️ No valid JSON found, using fallback")
            return fallback_data
            
        except Exception as e:
            print(f"⚠️ Error parsing response: {e}")
            return fallback_data
    
    @staticmethod
    def _normalize_ai_response(parsed_data: dict) -> dict:
        """Normalize AI response to ensure correct data types"""
        try:
            # Get search criteria
            search_criteria = parsed_data.get('search_criteria', {})
            
            # Normalize genre - convert list to string if needed
            genre = search_criteria.get('genre', 'comedy')
            if isinstance(genre, list):
                genre = genre[0] if genre else 'comedy'
            
            # Handle compound genres like "comedy/drama" - FIXED
            genre = str(genre).lower()
            if '/' in genre or '-' in genre:
                # For compound genres, map to primary genre based on context
                if 'comedy' in genre:
                    genre = 'comedy'
                elif 'drama' in genre:
                    genre = 'drama'
                elif 'action' in genre:
                    genre = 'action'
                else:
                    genre = genre.split('/')[0].split('-')[0]  # Take first part
            
            # Map to valid genres
            valid_genres = ['action', 'comedy', 'drama', 'thriller', 'family', 'romance', 'horror', 'sci-fi']
            if genre not in valid_genres:
                genre = 'comedy'  # Default for emotion-based requests
            
            # Normalize language
            language = search_criteria.get('language', 'hindi')
            if isinstance(language, list):
                language = language[0] if language else 'hindi'
            language = str(language).lower()
            
            # Normalize content_type
            content_type = search_criteria.get('content_type', 'both')
            if isinstance(content_type, list):
                content_type = content_type[0] if content_type else 'both'
            content_type = str(content_type).lower()
            
            # Ensure valid content_type
            if content_type not in ['movie', 'tv', 'both']:
                content_type = 'both'
            
            # Normalize suggested_titles
            suggested_titles = parsed_data.get('suggested_titles', [])
            if not isinstance(suggested_titles, list):
                suggested_titles = []
            
            print(f"🔧 Normalized - Genre: '{genre}' (was: '{search_criteria.get('genre', 'unknown')}'), Language: {language}, Content: {content_type}")
            
            # Return normalized structure
            return {
                "response": parsed_data.get('response', ''),
                "search_criteria": {
                    "genre": genre,
                    "language": language, 
                    "content_type": content_type
                },
                "suggested_titles": suggested_titles
            }
            
        except Exception as e:
            print(f"⚠️ Error normalizing AI response: {e}")
            # Return fallback structure
            return {
                "response": parsed_data.get('response', 'Let me find some recommendations for you!'),
                "search_criteria": {
                    "genre": "comedy",
                    "language": "hindi",
                    "content_type": "both"
                },
                "suggested_titles": []
            }
