from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
import json

class AppSettings(SQLModel, table=True):
    """Application-wide settings"""
    id: Optional[int] = Field(default=None, primary_key=True)
    github_token: Optional[str] = None  # GitHub Personal Access Token
    language: str = "zh"  # UI language: 'zh' or 'en'
    last_updated: Optional[datetime] = None
    
    __tablename__ = "app_settings"  # type: ignore

class SettingsUpdate(SQLModel):
    """Settings update request model"""
    github_token: Optional[str] = None
    language: Optional[str] = None

class SettingsResponse(SQLModel):
    """Settings response model (masks sensitive data)"""
    has_github_token: bool
    github_token_preview: Optional[str] = None  # Only show first/last few chars
    language: str = "zh"
    last_updated: Optional[datetime] = None

