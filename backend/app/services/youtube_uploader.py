import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import urllib.parse

logger = logging.getLogger(__name__)

class YouTubePublisher:
    """
    Service for publishing and preparing video clips for YouTube Shorts.
    Supports:
    1. Direct 1-Click Browser Upload Intent (Opens YouTube Studio upload with pre-copied SEO metadata)
    2. YouTube Data API v3 direct upload (if client_secret.json / OAuth credentials exist)
    """

    DEFAULT_SHORTS_HASHTAGS = ["#Shorts", "#Viral", "#Trending", "#Reels", "#FYP"]

    def __init__(self, client_secrets_file: Optional[str] = None):
        from ..config import DATA_DIR
        self.secrets_file = client_secrets_file or os.getenv(
            "YOUTUBE_CLIENT_SECRETS_FILE",
            str(DATA_DIR / "client_secret.json")
        )

    def prepare_shorts_metadata(
        self,
        clip_id: str,
        title: str,
        description: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        game_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate SEO-optimized title, description, tags, and one-click YouTube links.
        """
        # Ensure #Shorts is in the title (critical for YouTube Shorts algorithm)
        clean_title = title.strip()
        if "#shorts" not in clean_title.lower():
            if len(clean_title) <= 90:
                clean_title = f"{clean_title} #Shorts"
            else:
                clean_title = f"{clean_title[:88]}... #Shorts"

        tags = list(hashtags) if hashtags else list(self.DEFAULT_SHORTS_HASHTAGS)
        if game_name and game_name not in ["auto", "generic", "none"]:
            tags.insert(0, f"#{game_name.replace(' ', '')}")
            tags.insert(1, "#Gaming")

        # Deduplicate tags
        unique_tags = []
        for t in tags:
            tag = t if t.startswith("#") else f"#{t}"
            if tag.lower() not in [u.lower() for u in unique_tags]:
                unique_tags.append(tag)

        tags_string = " ".join(unique_tags)
        
        # Build engaging description
        desc_body = description or "Watch till the end! Like and subscribe for more daily viral highlights."
        full_description = f"{desc_body}\n\n👉 Subscribe for more clips!\n\n{tags_string}"

        # YouTube Studio direct upload URL
        studio_upload_url = "https://studio.youtube.com/channel/UC/videos/upload?d=hd"
        web_upload_url = "https://www.youtube.com/upload"

        return {
            "clip_id": clip_id,
            "title": clean_title,
            "description": full_description,
            "hashtags": unique_tags,
            "tags_list": [t.replace("#", "") for t in unique_tags],
            "tags_csv": ", ".join([t.replace("#", "") for t in unique_tags]),
            "studio_upload_url": studio_upload_url,
            "web_upload_url": web_upload_url,
            "copy_text": f"Title:\n{clean_title}\n\nDescription:\n{full_description}"
        }

    def is_api_configured(self) -> bool:
        """Check if OAuth client secrets exist for direct API uploads."""
        return bool(self.secrets_file and Path(self.secrets_file).exists())

    def upload_via_api(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: List[str],
        privacy_status: str = "unlisted"
    ) -> Dict[str, Any]:
        """
        Upload clip to YouTube via YouTube Data API v3 if credentials are available.
        """
        if not video_path.exists():
            return {"success": False, "message": f"Video file not found at {video_path}"}

        if not self.is_api_configured():
            return {
                "success": False,
                "message": (
                    "YouTube API credentials (client_secret.json) not found. "
                    "Use 1-Click Studio Upload or place client_secret.json in data/ directory."
                ),
                "studio_url": "https://studio.youtube.com/channel/UC/videos/upload?d=hd"
            }

        try:
            # Dynamically import google client libs if installed
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google.oauth2.credentials import Credentials

            token_path = Path(self.secrets_file).parent / "youtube_token.json"
            if not token_path.exists():
                return {
                    "success": False,
                    "message": "YouTube OAuth token not found. Please authenticate your channel first.",
                    "studio_url": "https://studio.youtube.com/channel/UC/videos/upload?d=hd"
                }

            creds = Credentials.from_authorized_user_file(str(token_path))
            youtube = build("youtube", "v3", credentials=creds)

            body = {
                "snippet": {
                    "title": title[:100],
                    "description": description,
                    "tags": tags,
                    "categoryId": "20"  # 20 is Gaming
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                }
            }

            media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            response = request.execute()

            video_id = response.get("id")
            return {
                "success": True,
                "video_id": video_id,
                "video_url": f"https://youtube.com/shorts/{video_id}",
                "studio_url": f"https://studio.youtube.com/video/{video_id}/edit",
                "message": f"Successfully published to YouTube Shorts ({privacy_status})!"
            }
        except ImportError:
            return {
                "success": False,
                "message": "google-api-python-client not installed. Use 1-Click Studio Upload.",
                "studio_url": "https://studio.youtube.com/channel/UC/videos/upload?d=hd"
            }
        except Exception as e:
            logger.error(f"YouTube upload error: {e}")
            return {
                "success": False,
                "message": f"Upload error: {str(e)}",
                "studio_url": "https://studio.youtube.com/channel/UC/videos/upload?d=hd"
            }
