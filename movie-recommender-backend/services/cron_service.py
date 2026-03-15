import asyncio
from typing import List, Dict
from services.user_preference_service import UserPreferenceService
from services.recommendation_engine import RecommendationEngine
from services.email_service import EmailService

class CronService:
    def __init__(self):
        self.user_service = UserPreferenceService()
        self.recommendation_engine = RecommendationEngine()
        self.email_service = EmailService()

    async def run_weekly_recommendations(self):
        """
        Main task to iterate through all users and send them personalized 
        recommendations via email.
        """
        print("🕒 Starting weekly recommendation email task...")
        
        # 1. Fetch all users from database who have an email
        users = await self.user_service.get_all_users_for_email()
        print(f"👥 Found {len(users)} users with email sub.")
        
        results = {
            "total_users": len(users),
            "emails_sent": 0,
            "failed": 0
        }

        for user in users:
            user_id = user.get("user_id")
            email = user.get("email")
            
            # Extract name
            full_name = user.get("full_name")
            user_name = full_name.split(" ")[0] if full_name else "User"

            try:
                print(f"🔄 Generating picks for {email} ({user_id})...")
                
                # 2. Get recommendations using existing engine
                # We want 5 strong recommendations
                resp = await self.recommendation_engine.get_personalized_recommendations(user_id, limit=5)
                recommendations = resp.get("recommendations", [])
                
                if not recommendations:
                    print(f"⏭️ No recommendations found for {email}. Skipping.")
                    continue

                # 3. Send email
                success = await self.email_service.send_recommendation_email(
                    to_email=email,
                    user_name=user_name,
                    recommendations=recommendations
                )
                
                if success:
                    results["emails_sent"] += 1
                else:
                    results["failed"] += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing weekly email for {user_id}: {e}")
                results["failed"] += 1

        print(f"🏁 Weekly task completed: {results}")
        return results
