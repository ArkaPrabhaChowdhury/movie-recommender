import httpx
import asyncio
from config.constants import TMDB_API_KEY, TMDB_API_URL, INDIAN_OTT_PLATFORMS, API_CONFIG
from utils.analytics_tracker import tracker

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
                # Use item's specific content type if 'both' is requested
                # Fallback to the provided api_content_type if not specified in the item
                itype = item.get("content_type", api_content_type)
                if itype == "both":
                    # If both the param and the item don't specify, we can't fetch. 
                    # Default to 'movie' or skip? Let's skip invalid ones.
                    continue
                    
                task = client.get(
                    f"{TMDB_API_URL}/{itype}/{item['id']}/watch/providers",
                    params={"api_key": TMDB_API_KEY}
                )
                tasks.append(task)
            
            # Execute all requests in parallel
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Keep track of which items we actually sent tasks for
            valid_items = [item for item in content_items if item.get("content_type", api_content_type) != "both"]
            
            ott_content = []
            
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    tracker.record_event("provider_failures")
                    print(f"Error for item {valid_items[i]['id']}: {response}")
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
                                        "id": provider_id,
                                        "name": ott_info["name"],
                                        "logo": provider.get('logo_path', ''),
                                        "color": ott_info["color"],
                                        "is_rent": False
                                    })
                                else:
                                    streaming_platforms.append({
                                        "id": provider_id,
                                        "name": provider_name,
                                        "logo": provider.get('logo_path', ''),
                                        "color": "#6B7280",
                                        "is_rent": False
                                    })
                        
                        # Include rent options as well for more content
                        if 'rent' in india_providers:
                            for provider in india_providers['rent']:
                                streaming_platforms.append({
                                    "id": provider['provider_id'],
                                    "name": f"{provider['provider_name']} (Rent)",
                                    "logo": provider.get('logo_path', ''),
                                    "color": "#F59E0B",
                                    "is_rent": True
                                })
                        
                        # Add the content item regardless of whether streaming platforms were found
                        content_item = valid_items[i].copy()
                        content_item["streaming"] = {
                            "available_on": streaming_platforms[:API_CONFIG['MAX_STREAMING_PLATFORMS']],
                            "tmdb_link": india_providers.get('link'),
                            "platform_found": bool(streaming_platforms)
                        }
                        ott_content.append(content_item)
                            
                except Exception as e:
                    tracker.record_event("provider_failures")
                    print(f"Error processing streaming data for item {valid_items[i]['id']}: {e}")
                    # Still add the item even on error
                    content_item = valid_items[i].copy()
                    content_item["streaming"] = {"available_on": [], "platform_found": False}
                    ott_content.append(content_item)
        
        return ott_content
