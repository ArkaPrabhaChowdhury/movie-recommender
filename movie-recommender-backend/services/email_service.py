import os
from typing import Dict, List

import httpx


class EmailService:
    def __init__(self):
        self.api_key = os.getenv('RESEND_API_KEY')
        self.api_url = "https://api.resend.com/emails"
        self.from_email = "OTT Scout <onboarding@resend.dev>"

    async def _send(self, to_email: str, subject: str, html: str) -> bool:
        if not self.api_key:
            print("RESEND_API_KEY not set. Skipping email.")
            return False
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"from": self.from_email, "to": to_email, "subject": subject, "html": html}
                )
                if response.status_code not in [200, 201]:
                    print(f"Resend API Error {response.status_code}: {response.text}")
                    return False
                return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    async def send_recommendation_email(self, to_email: str, user_name: str, recommendations: List[Dict]):
        if not recommendations:
            return False
        items_html = ""
        for item in recommendations[:5]:
            title = item.get('title', 'Unknown Title')
            year = item.get('year', '')
            reason = item.get('recommendation_reason', 'Matches your taste profile')
            items_html += f"""
            <div style="margin-bottom:20px;border-bottom:1px solid #eee;padding-bottom:10px;">
              <h3 style="margin:0;color:#1a202c;">{title} {f'({year})' if year else ''}</h3>
              <p style="color:#4a5568;">{reason}</p>
              <a href="https://ottscout.vercel.app/details/{item.get('content_type')}/{item.get('id')}" style="color:#319795;">Watch Now</a>
            </div>"""
        html = f"""<html><body style="font-family:sans-serif;color:#333"><div style="max-width:600px;margin:auto;padding:20px">
          <h1 style="color:#319795">Weekly Scout: Your Movie Picks!</h1><p>Hi {user_name},</p>
          <p>Here are fresh picks based on your taste.</p>{items_html}
          <p style="font-size:12px;color:#718096">Update your preferences at ottscout.vercel.app/profile.</p>
        </div></body></html>"""
        return await self._send(to_email, f"Weekly Scout: Top {len(recommendations[:5])} Picks for You!", html)

    async def send_episode_notification_email(self, to_email: str, user_name: str, show: Dict, episode: Dict):
        """Notify a user that a watched TV show has a newly released episode."""
        title = show.get('title', 'A watched show')
        episode_name = episode.get('name') or f"Episode {episode.get('episode_number', '')}"
        season_number = episode.get('season_number')
        episode_number = episode.get('episode_number')
        label = f"S{season_number} E{episode_number}" if season_number and episode_number else "New episode"
        details_url = f"https://ottscout.vercel.app/details/tv/{show.get('id')}"
        html = f"""<html><body style="font-family:Arial,sans-serif;color:#253238;background:#f6faf9;padding:24px">
          <div style="max-width:600px;margin:auto;background:#fff;padding:28px;border-radius:16px">
            <p style="color:#168f89;font-weight:700;text-transform:uppercase">OTT Scout · Watching</p>
            <h1>{title} has a new episode</h1><p>Hi {user_name}, the latest episode of a show you follow is out.</p>
            <h2>{episode_name}</h2><p style="color:#168f89;font-weight:700">{label} · {episode.get('air_date', '')}</p>
            <p>{episode.get('overview') or 'A new episode is now available.'}</p>
            <a href="{details_url}" style="display:inline-block;background:#168f89;color:#fff;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:700">Open in OTT Scout</a>
            <p style="font-size:12px;color:#718096">You are receiving this because you marked this TV show as Watching.</p>
          </div></body></html>"""
        return await self._send(to_email, f"New episode: {title} — {episode_name}", html)
