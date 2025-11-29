import httpx
import asyncio
from config.constants import TMDB_API_KEY, TMDB_API_URL, INDIAN_OTT_PLATFORMS, API_CONFIG

class StreamingService:
    @staticmethod
    async def get_streaming_providers_batch(content_items: list, api_content_type: str):
        """Get streaming providers for multiple items in parallel"""
        if not content_items:
            return []
            
        async with httpx.AsyncClient(timeout=API_CONFIG['TIMEOUT']) as client:
            # Create all requests
            tasks = []
            for item in content_items:
                task = client.get(
                    f"{TMDB_API_URL}/{api_content_type}/{item['id']}/watch/providers",
                    params={"api_key": TMDB_API_KEY}
                )
                tasks.append(task)
            
            # Execute all requests in parallel
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            ott_content = []
            
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    print(f"Error for item {content_items[i]['id']}: {response}")
                    continue
                    
                try:
                    if response.status_code == 200:
                        data = response.json()
                        providers_data = data.get('results', {})
                        india_providers = providers_data.get('IN', {})
                        
                        streaming_platforms = []
                        
                        # Check flatrate (streaming subscription) providers
                        if 'flatrate' in india_providers:
                            for provider in india_providers['flatrate']:
                                provider_id = provider['provider_id']
                                provider_name = provider['provider_name']
                                
                                if provider_id in INDIAN_OTT_PLATFORMS:
                                    ott_info = INDIAN_OTT_PLATFORMS[provider_id]
                                    streaming_platforms.append({
                                        "name": ott_info["name"],
                                        "logo": provider.get('logo_path', ''),
                                        "color": ott_info["color"]
                                    })
                                else:
                                    streaming_platforms.append({
                                        "name": provider_name,
                                        "logo": provider.get('logo_path', ''),
                                        "color": "#6B7280"
                                    })
                        
                        # Include rent options as well for more content
                        if 'rent' in india_providers:
                            for provider in india_providers['rent']:
                                streaming_platforms.append({
                                    "name": f"{provider['provider_name']} (Rent)",
                                    "logo": provider.get('logo_path', ''),
                                    "color": "#F59E0B"
                                })
                        
                        # Only add content that has some streaming availability
                        if streaming_platforms:
                            content_item = content_items[i].copy()
                            content_item["streaming"] = {
                                "available_on": streaming_platforms[:API_CONFIG['MAX_STREAMING_PLATFORMS']],
                                "rent": [],
                                "buy": []
                            }
                            ott_content.append(content_item)
                            
                except Exception as e:
                    print(f"Error processing streaming data for item {content_items[i]['id']}: {e}")
                    continue
        
        return ott_content
