"""
OAuth2 service for handling authentication with external calendar providers
(Google Calendar, Microsoft Graph, etc.)
"""

import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, parse_qs, urlparse
import requests
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from src.backend.models.calendar import CalendarIntegration, CalendarProvider
from src.backend.database.database import SessionLocal

logger = logging.getLogger(__name__)

class OAuthProvider:
    """Base class for OAuth providers"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.encryption_key = self._get_encryption_key()
        
    def _get_encryption_key(self) -> bytes:
        """Get or create encryption key for storing tokens"""
        key = os.getenv("OAUTH_ENCRYPTION_KEY")
        if not key:
            # In production, this should be set as an environment variable
            key = Fernet.generate_key()
            logger.warning("Using generated encryption key. Set OAUTH_ENCRYPTION_KEY in production.")
        return key.encode() if isinstance(key, str) else key
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt token for secure storage"""
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token for use"""
        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(encrypted_token.encode()).decode()
    
    def generate_auth_url(self, state: str, scopes: List[str]) -> str:
        """Generate OAuth authorization URL"""
        raise NotImplementedError("Subclasses must implement generate_auth_url")
    
    def exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access/refresh tokens"""
        raise NotImplementedError("Subclasses must implement exchange_code_for_tokens")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        raise NotImplementedError("Subclasses must implement refresh_access_token")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from provider"""
        raise NotImplementedError("Subclasses must implement get_user_info")

class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider for Calendar API access"""
    
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    REVOKE_URL = "https://oauth2.googleapis.com/revoke"
    
    SCOPES = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    
    def generate_auth_url(self, state: str, scopes: Optional[List[str]] = None) -> str:
        """Generate Google OAuth authorization URL"""
        if not scopes:
            scopes = self.SCOPES
            
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"  # Force consent to get refresh token
        }
        
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for Google tokens"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        if response.status_code != 200:
            logger.error(f"Google token exchange failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for tokens"
            )
        
        return response.json()
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Google access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        if response.status_code != 200:
            logger.error(f"Google token refresh failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh access token"
            )
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Google user information"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USER_INFO_URL, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Google user info failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information"
            )
        
        return response.json()
    
    def revoke_token(self, token: str) -> bool:
        """Revoke Google access token"""
        params = {"token": token}
        response = requests.post(self.REVOKE_URL, params=params)
        return response.status_code == 200

class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft OAuth provider for Graph API access"""
    
    AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"
    
    SCOPES = [
        "https://graph.microsoft.com/Calendars.ReadWrite",
        "https://graph.microsoft.com/User.Read",
        "offline_access"
    ]
    
    def generate_auth_url(self, state: str, scopes: Optional[List[str]] = None) -> str:
        """Generate Microsoft OAuth authorization URL"""
        if not scopes:
            scopes = self.SCOPES
            
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "response_mode": "query"
        }
        
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for Microsoft tokens"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        if response.status_code != 200:
            logger.error(f"Microsoft token exchange failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for tokens"
            )
        
        return response.json()
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Microsoft access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        if response.status_code != 200:
            logger.error(f"Microsoft token refresh failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh access token"
            )
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Microsoft user information"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USER_INFO_URL, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Microsoft user info failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information"
            )
        
        return response.json()

class OAuthService:
    """Main OAuth service for managing calendar integrations"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.state_cache = {}  # In production, use Redis or database
    
    def _initialize_providers(self) -> Dict[CalendarProvider, OAuthProvider]:
        """Initialize OAuth providers from environment variables"""
        providers = {}
        
        # Google Calendar
        google_client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
        google_redirect_uri = os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", "http://localhost:8000/api/calendar/auth/google/callback")
        
        if google_client_id and google_client_secret:
            providers[CalendarProvider.GOOGLE] = GoogleOAuthProvider(
                client_id=google_client_id,
                client_secret=google_client_secret,
                redirect_uri=google_redirect_uri
            )
        
        # Microsoft Graph
        microsoft_client_id = os.getenv("MICROSOFT_GRAPH_CLIENT_ID")
        microsoft_client_secret = os.getenv("MICROSOFT_GRAPH_CLIENT_SECRET")
        microsoft_redirect_uri = os.getenv("MICROSOFT_GRAPH_REDIRECT_URI", "http://localhost:8000/api/calendar/auth/microsoft/callback")
        
        if microsoft_client_id and microsoft_client_secret:
            providers[CalendarProvider.MICROSOFT] = MicrosoftOAuthProvider(
                client_id=microsoft_client_id,
                client_secret=microsoft_client_secret,
                redirect_uri=microsoft_redirect_uri
            )
        
        return providers
    
    def generate_state_token(self, user_id: int, provider: CalendarProvider) -> str:
        """Generate a secure state token for OAuth flow"""
        state_data = {
            "user_id": user_id,
            "provider": provider.value,
            "timestamp": datetime.utcnow().isoformat(),
            "nonce": secrets.token_urlsafe(32)
        }
        
        state_token = secrets.token_urlsafe(32)
        self.state_cache[state_token] = state_data
        
        return state_token
    
    def validate_state_token(self, state_token: str) -> Optional[Dict[str, Any]]:
        """Validate state token and return associated data"""
        state_data = self.state_cache.pop(state_token, None)
        if not state_data:
            return None
        
        # Check if token is expired (30 minutes)
        timestamp = datetime.fromisoformat(state_data["timestamp"])
        if datetime.utcnow() - timestamp > timedelta(minutes=30):
            return None
        
        return state_data
    
    def get_auth_url(self, user_id: int, provider: CalendarProvider, scopes: Optional[List[str]] = None) -> str:
        """Get OAuth authorization URL for provider"""
        if provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {provider.value} not configured"
            )
        
        state_token = self.generate_state_token(user_id, provider)
        oauth_provider = self.providers[provider]
        
        return oauth_provider.generate_auth_url(state_token, scopes)
    
    def handle_callback(self, provider: CalendarProvider, code: str, state: str, user_id: int) -> CalendarIntegration:
        """Handle OAuth callback and create/update integration"""
        if provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {provider.value} not configured"
            )
        
        # Validate state token
        state_data = self.validate_state_token(state)
        if not state_data or state_data["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state token"
            )
        
        oauth_provider = self.providers[provider]
        
        # Exchange code for tokens
        token_data = oauth_provider.exchange_code_for_tokens(code, state)
        
        # Get user info
        user_info = oauth_provider.get_user_info(token_data["access_token"])
        
        # Calculate token expiration
        expires_in = token_data.get("expires_in", 3600)
        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Store integration in database
        db = SessionLocal()
        try:
            # Check if integration already exists
            integration = db.query(CalendarIntegration).filter(
                CalendarIntegration.user_id == user_id,
                CalendarIntegration.provider == provider
            ).first()
            
            if integration:
                # Update existing integration
                integration.access_token = oauth_provider.encrypt_token(token_data["access_token"])
                if "refresh_token" in token_data:
                    integration.refresh_token = oauth_provider.encrypt_token(token_data["refresh_token"])
                integration.token_expires_at = token_expires_at
                integration.scope = token_data.get("scope", "")
                integration.email = user_info.get("email")
                integration.provider_user_id = user_info.get("id")
                integration.is_active = True
            else:
                # Create new integration
                integration = CalendarIntegration(
                    user_id=user_id,
                    provider=provider,
                    provider_user_id=user_info.get("id"),
                    email=user_info.get("email"),
                    access_token=oauth_provider.encrypt_token(token_data["access_token"]),
                    refresh_token=oauth_provider.encrypt_token(token_data.get("refresh_token", "")),
                    token_expires_at=token_expires_at,
                    scope=token_data.get("scope", ""),
                    is_active=True
                )
                db.add(integration)
            
            db.commit()
            db.refresh(integration)
            return integration
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save integration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save integration"
            )
        finally:
            db.close()
    
    def refresh_token(self, integration: CalendarIntegration) -> CalendarIntegration:
        """Refresh access token for integration"""
        if integration.provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {integration.provider.value} not configured"
            )
        
        oauth_provider = self.providers[integration.provider]
        
        try:
            # Decrypt refresh token
            refresh_token = oauth_provider.decrypt_token(integration.refresh_token)
            
            # Refresh tokens
            token_data = oauth_provider.refresh_access_token(refresh_token)
            
            # Calculate new expiration
            expires_in = token_data.get("expires_in", 3600)
            token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Update integration
            db = SessionLocal()
            try:
                integration.access_token = oauth_provider.encrypt_token(token_data["access_token"])
                if "refresh_token" in token_data:
                    integration.refresh_token = oauth_provider.encrypt_token(token_data["refresh_token"])
                integration.token_expires_at = token_expires_at
                
                db.commit()
                db.refresh(integration)
                return integration
                
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to update integration: {str(e)}")
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            # Mark integration as inactive if refresh fails
            integration.is_active = False
            db = SessionLocal()
            try:
                db.commit()
            except:
                db.rollback()
            finally:
                db.close()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh access token"
            )
    
    def get_valid_token(self, integration: CalendarIntegration) -> str:
        """Get valid access token, refreshing if necessary"""
        if integration.provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {integration.provider.value} not configured"
            )
        
        oauth_provider = self.providers[integration.provider]
        
        # Check if token is expired (with 5-minute buffer)
        if datetime.utcnow() + timedelta(minutes=5) >= integration.token_expires_at:
            integration = self.refresh_token(integration)
        
        return oauth_provider.decrypt_token(integration.access_token)
    
    def revoke_integration(self, integration: CalendarIntegration):
        """Revoke OAuth tokens and deactivate integration"""
        if integration.provider not in self.providers:
            logger.warning(f"Provider {integration.provider.value} not configured for revocation")
            return
        
        oauth_provider = self.providers[integration.provider]
        
        try:
            # Decrypt and revoke access token
            access_token = oauth_provider.decrypt_token(integration.access_token)
            
            if hasattr(oauth_provider, 'revoke_token'):
                oauth_provider.revoke_token(access_token)
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}")
        
        # Deactivate integration
        db = SessionLocal()
        try:
            integration.is_active = False
            integration.access_token = ""
            integration.refresh_token = ""
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to deactivate integration: {str(e)}")
        finally:
            db.close()

# Global instance
oauth_service = OAuthService()