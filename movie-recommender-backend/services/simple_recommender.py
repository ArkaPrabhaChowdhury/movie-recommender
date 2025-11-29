import re
from typing import Dict

class SimpleRecommender:
    @staticmethod
    def analyze_request(user_message: str) -> Dict:
        """Smart rule-based analysis"""
        message_lower = user_message.lower()
        
        # Specific pattern matching
        if ('laugh' in message_lower or 'funny' in message_lower) and ('cry' in message_lower or 'emotional' in message_lower):
            return {
                "response": "I understand you want something that makes you laugh but also touches your heart! Let me find romantic comedies and feel-good movies with emotional depth.",
                "search_criteria": {
                    "genre": "comedy",
                    "language": "hindi",
                    "content_type": "both"
                },
                "suggested_titles": ["3 Idiots", "Zindagi Na Milegi Dobara", "Queen"]
            }
        
        elif 'dark' in message_lower or 'psychological' in message_lower:
            return {
                "response": "Looking for something dark and psychological! I'll find mind-bending thrillers for you.",
                "search_criteria": {
                    "genre": "thriller",
                    "language": "hindi", 
                    "content_type": "both"
                },
                "suggested_titles": ["Andhadhun", "Kahaani", "Pink"]
            }
        
        elif 'family' in message_lower or 'kids' in message_lower:
            return {
                "response": "Perfect for family time! Let me find wholesome content everyone can enjoy.",
                "search_criteria": {
                    "genre": "family",
                    "language": "hindi",
                    "content_type": "both"
                },
                "suggested_titles": ["Dangal", "Secret Superstar", "Hindi Medium"]
            }
        
        elif 'motivation' in message_lower or 'inspire' in message_lower:
            return {
                "response": "You need some motivation! Let me find inspiring stories for you.",
                "search_criteria": {
                    "genre": "drama",
                    "language": "hindi",
                    "content_type": "both"
                },
                "suggested_titles": ["Dangal", "Bhaag Milkha Bhaag", "Chak De India"]
            }
        
        else:
            return {
                "response": "Let me find some great recommendations for you!",
                "search_criteria": {
                    "genre": "action",
                    "language": "hindi",
                    "content_type": "both"
                },
                "suggested_titles": ["RRR", "KGF Chapter 2", "Pushpa"]
            }
