from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import datetime

from app.core.database import engine
from app.models.settings import AppSettings, SettingsUpdate, SettingsResponse

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

def get_or_create_settings(session: Session) -> AppSettings:
    """Get existing settings or create default"""
    settings = session.exec(select(AppSettings)).first()
    if not settings:
        settings = AppSettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings

@router.get("/", response_model=SettingsResponse)
def get_settings(session: Session = Depends(get_session)):
    """Get application settings (sensitive data masked)"""
    settings = get_or_create_settings(session)
    
    # Mask token for security
    token_preview = None
    if settings.github_token:
        token = settings.github_token
        if len(token) > 10:
            token_preview = f"{token[:4]}...{token[-4:]}"
        else:
            token_preview = "***"
    
    return SettingsResponse(
        has_github_token=bool(settings.github_token),
        github_token_preview=token_preview,
        language=getattr(settings, 'language', 'zh'),
        last_updated=settings.last_updated
    )

@router.put("/", response_model=SettingsResponse)
def update_settings(settings_update: SettingsUpdate, session: Session = Depends(get_session)):
    """Update application settings"""
    settings = get_or_create_settings(session)
    
    # Update fields
    if settings_update.github_token is not None:
        settings.github_token = settings_update.github_token if settings_update.github_token.strip() else None
    
    if settings_update.language is not None:
        settings.language = settings_update.language
    
    settings.last_updated = datetime.now()
    
    session.add(settings)
    session.commit()
    session.refresh(settings)
    
    # Return masked response
    token_preview = None
    if settings.github_token:
        token = settings.github_token
        if len(token) > 10:
            token_preview = f"{token[:4]}...{token[-4:]}"
        else:
            token_preview = "***"
    
    return SettingsResponse(
        has_github_token=bool(settings.github_token),
        github_token_preview=token_preview,
        language=settings.language,
        last_updated=settings.last_updated
    )

@router.get("/github-token")
def get_github_token(session: Session = Depends(get_session)):
    """Get the actual GitHub token (for internal API use only)"""
    settings = get_or_create_settings(session)
    return {"github_token": settings.github_token}

@router.delete("/github-token")
def clear_github_token(session: Session = Depends(get_session)):
    """Clear the saved GitHub token"""
    settings = get_or_create_settings(session)
    settings.github_token = None
    settings.last_updated = datetime.now()
    
    session.add(settings)
    session.commit()
    
    return {"ok": True, "message": "GitHub token cleared"}

