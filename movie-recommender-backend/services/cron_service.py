import asyncio
from typing import List, Dict
from services.user_preference_service import UserPreferenceService
from services.recommendation_engine import RecommendationEngine
from services.email_service import EmailService
from services.tmdb_service import TMDBService
from datetime import datetime, timezone
from utils.analytics_tracker import tracker

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

    async def run_watching_notifications(self):
        """Check TMDB for newly aired episodes and email watching subscribers."""
        users = await self.user_service.get_all_watching_users()
        results = {"total_users": len(users), "episodes_checked": 0, "emails_sent": 0, "failed": 0}
        now = datetime.now(timezone.utc).date()

        for user in users:
            user_name = (user.get('full_name') or 'User').split(' ')[0]
            for subscription in user.get('watching', []):
                try:
                    status = await TMDBService.get_tv_episode_status(subscription['content_id'])
                    episode = status.get('last_episode') or {}
                    air_date = episode.get('air_date')
                    results['episodes_checked'] += 1
                    if not episode.get('id') or not air_date or datetime.fromisoformat(air_date).date() > now:
                        continue
                    if episode.get('id') == subscription.get('last_notified_episode_id'):
                        tracker.record_event("duplicate_notifications_prevented")
                        continue

                    show = {**subscription, 'id': subscription['content_id']}
                    sent = await self.email_service.send_episode_notification_email(
                        user.get('email'), user_name, show, episode
                    )
                    if sent:
                        tracker.record_event("notification_successes")
                        await self.user_service.update_watching_episode(
                            user['user_id'], subscription['content_id'], episode['id']
                        )
                        results['emails_sent'] += 1
                    else:
                        tracker.record_event("notification_failures")
                        results['failed'] += 1
                except Exception as e:
                    print(f"Error processing watching subscription: {e}")
                    results['failed'] += 1
        return results
