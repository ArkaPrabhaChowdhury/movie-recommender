import os
import httpx
from typing import List, Dict

class EmailService:
    def __init__(self):
        self.api_key = os.getenv('RESEND_API_KEY')
        self.api_url = "https://api.resend.com/emails"
        self.from_email = "OTT Scout <onboarding@resend.dev>" # Default test email, should be updated with a domain

    async def send_recommendation_email(self, to_email: str, user_name: str, recommendations: List[Dict]):
        if not self.api_key:
            print("⚠️ RESEND_API_KEY not set. Skipping email.")
            return False

        if not recommendations:
            return False

        # Build HTML content
        items_html = ""
        for item in recommendations[:5]:
            title = item.get('title', 'Unknown Title')
            year = item.get('year', '')
            year_display = f"({year})" if year else ""
            reason = item.get('recommendation_reason', 'Matches your taste profile')
            poster = item.get('poster', '')
            
            items_html += f"""
            <div style="margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                <table width="100%">
                    <tr>
                        <td width="120" valign="top">
                            <img src="{poster}" alt="{title}" width="100" style="border-radius: 8px; background: #f7fafc;">
                        </td>
                        <td valign="top" style="padding-left: 15px;">
                            <h3 style="margin: 0; color: #1a202c;">{title} {year_display}</h3>
                            <p style="color: #4a5568; margin: 5px 0;">{reason}</p>
                            <a href="https://ottscout.vercel.app/details/{item.get('content_type')}/{item.get('id')}" 
                               style="display: inline-block; background: #319795; color: white; padding: 6px 12px; text-decoration: none; border-radius: 5px; font-size: 14px; margin-top: 5px;">
                               Watch Now
                            </a>
                        </td>
                    </tr>
                </table>
            </div>
            """

        html_content = f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #319795; text-align: center;">Weekly Scout: Your Movie Picks! 🎬</h1>
                    <p>Hi {user_name},</p>
                    <p>We've found some fresh content we think you'll love based on what you've been watching lately.</p>
                    
                    <div style="margin-top: 30px;">
                        {items_html}
                    </div>
                    
                    <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #718096;">
                        You're receiving this because you're a scout at OTT Scout.<br>
                        <a href="https://ottscout.vercel.app/profile" style="color: #319795;">Update Preferences</a>
                    </div>
                </div>
            </body>
        </html>
        """

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": to_email,
                        "subject": f"Weekly Scout: Top {len(recommendations[:5])} Picks for You! 🍿",
                        "html": html_content
                    }
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ Weekly email sent to {to_email}")
                    return True
                else:
                    print(f"❌ Resend API Error {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
