from fastapi import APIRouter, HTTPException, Depends, Body, Query
from sqlmodel import Session, select
from typing import List, Dict, Any
import os

from app.core.database import engine
from app.models.project import Project, ProjectCreate, ProjectUpdate, ProjectConfig, ProjectAutoInit, ProjectResponse
from app.services.git_service import GitService
from app.services.scanner_service import ScannerService
from app.services.ignore_service import IgnoreService
from app.services.logger import manager as log_manager
from app.i18n.log_messages import LogMessages

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=ProjectResponse)
def create_project(project_in: ProjectCreate, session: Session = Depends(get_session)):
    """
    Manual mode: Add an existing local project to TuTu's Code Ark management
    
    Use cases:
    - Import existing Git projects for monitoring
    - Add cloned repositories
    - Batch import multiple projects
    
    For creating new projects from scratch, use /auto-init instead.
    """
    if not os.path.exists(project_in.path):
        raise HTTPException(
            status_code=404, 
            detail="Path not found. If you want to create a new project, use /auto-init endpoint instead."
        )
    
    # Check if already exists in database
    existing = session.exec(select(Project).where(Project.path == project_in.path)).first()
    if existing:
        return ProjectResponse(
            id=existing.id,
            name=existing.name,
            path=existing.path,
            remote_url=existing.remote_url,
            branch=existing.branch,
            last_sync_time=existing.last_sync_time,
            status=existing.status,
            config=existing.config
        )
    
    # Auto-detect git info
    git_info = GitService.get_repo_info(project_in.path)
    
    # Provide helpful feedback
    if not git_info.get("is_repo"):
        raise HTTPException(
            status_code=400,
            detail="This directory is not a Git repository. Use /auto-init to create a new project with Git and GitHub setup."
        )
    
    if not git_info.get("remote_url"):
        raise HTTPException(
            status_code=400,
            detail="This Git repository has no remote URL. Please configure a remote first, or use /auto-init to set up GitHub automatically."
        )
    
    project = Project(
        name=project_in.name or os.path.basename(project_in.path),
        path=project_in.path,
        remote_url=git_info.get("remote_url"),
        branch=git_info.get("branch") or "main"
    )
    
    session.add(project)
    session.commit()
    session.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        path=project.path,
        remote_url=project.remote_url,
        branch=project.branch,
        last_sync_time=project.last_sync_time,
        status=project.status,
        config=project.config
    )

@router.post("/auto-init", response_model=ProjectResponse)
async def auto_init_project(init_data: ProjectAutoInit, session: Session = Depends(get_session)):
    t = lambda key, **kwargs: LogMessages.t(key, init_data.lang, **kwargs)
    
    await log_manager.broadcast(t("starting_init", name=init_data.name), "info")
    
    # Get GitHub token from request or global settings
    github_token = init_data.github_token
    if not github_token:
        await log_manager.broadcast(t("checking_token"), "info")
        from app.models.settings import AppSettings
        settings = session.exec(select(AppSettings)).first()
        if settings and settings.github_token:
            github_token = settings.github_token
            await log_manager.broadcast(t("using_saved_token"), "success")
        else:
            await log_manager.broadcast(t("error_no_token"), "error")
            raise HTTPException(status_code=400, detail="GitHub token is required. Please configure it in settings or provide it in the request.")
    
    # 1. Validate local path (create if not exists)
    await log_manager.broadcast(t("step1", path=init_data.path), "info")
    if not os.path.exists(init_data.path):
        try:
            os.makedirs(init_data.path)
            await log_manager.broadcast(t("success_directory_created", path=init_data.path), "success")
        except Exception as e:
            await log_manager.broadcast(t("error_directory_create", error=str(e)), "error")
            raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")
    else:
        await log_manager.broadcast(t("path_exists", path=init_data.path), "success")
             
    # 2. Check database for duplicates
    await log_manager.broadcast(t("step2"), "info")
    existing = session.exec(select(Project).where(Project.path == init_data.path)).first()
    if existing:
        await log_manager.broadcast(t("error_project_exists"), "error")
        raise HTTPException(status_code=400, detail="Project already managed by TuTu's Code Ark")
    await log_manager.broadcast(t("no_duplicate"), "success")
         
    # 3. Call GitService for complex initialization
    await log_manager.broadcast(t("step3"), "info")
    try:
        async def log_callback(msg: str, level: str = "info"):
            await log_manager.broadcast(msg, level)
        
        remote_url = await GitService.init_and_push_to_github(
            init_data.path, 
            init_data.name, 
            github_token,  # Use token from request or settings
            init_data.is_private,
            log_callback=log_callback,
            lang=init_data.lang,  # Pass language parameter
            gitignore_content=init_data.gitignore_content,  # Pass custom .gitignore content
            description=init_data.description  # Pass repository description
        )
        await log_manager.broadcast(t("git_init_complete", url=remote_url), "success")
    except Exception as e:
        await log_manager.broadcast(t("error_git_init", error=str(e)), "error")
        raise HTTPException(status_code=500, detail=f"Auto-init failed: {str(e)}")
        
    # 4. Save to database
    await log_manager.broadcast(t("step4"), "info")
    project = Project(
        name=init_data.name,
        path=init_data.path,
        remote_url=remote_url,
        branch="main",
        status="idle"
    )
    
    # Set default to auto push
    config = ProjectConfig(auto_push=True, is_private=init_data.is_private)
    project.set_config(config)
    
    session.add(project)
    session.commit()
    session.refresh(project)
    await log_manager.broadcast(t("saved_to_db", id=project.id), "success")
    
    # 5. Start file monitoring
    await log_manager.broadcast(t("step5"), "info")
    from app.services.watcher_service import watcher_service
    watcher_service.watch_project(project)
    await log_manager.broadcast(t("monitoring_started"), "success")
    
    await log_manager.broadcast(t("init_complete"), "success")
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        path=project.path,
        remote_url=project.remote_url,
        branch=project.branch,
        last_sync_time=project.last_sync_time,
        status=project.status,
        config=project.config
    )

@router.get("/", response_model=List[ProjectResponse])
def read_projects(session: Session = Depends(get_session)):
    projects = session.exec(select(Project)).all()
    # Convert to response model with config
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            path=p.path,
            remote_url=p.remote_url,
            branch=p.branch,
            last_sync_time=p.last_sync_time,
            status=p.status,
            config=p.config
        )
        for p in projects
    ]

@router.get("/{project_id}", response_model=ProjectResponse)
def read_project(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        path=project.path,
        remote_url=project.remote_url,
        branch=project.branch,
        last_sync_time=project.last_sync_time,
        status=project.status,
        config=project.config
    )

@router.get("/{project_id}/status")
def get_project_status(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return GitService.get_status(project.path)

@router.delete("/{project_id}")
def delete_project(
    project_id: int, 
    delete_remote: bool = Query(False, description="是否同时删除远程仓库"),
    github_token: str = Query(None, description="GitHub Token (删除远程仓库时需要)"),
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If delete_remote is True, try to delete GitHub repository
    if delete_remote and project.remote_url and "github.com" in project.remote_url:
        if not github_token:
            raise HTTPException(status_code=400, detail="GitHub token required to delete remote repository")
        
        try:
            from github import Github, GithubException
            g = Github(github_token)
            user = g.get_user()
            
            # Extract repo name from URL
            # URL format: https://github.com/username/repo.git or https://github.com/username/repo
            repo_name = project.remote_url.split("/")[-1].replace(".git", "")
            
            try:
                repo = user.get_repo(repo_name)
                repo.delete()
            except GithubException as e:
                if e.status == 404:
                    # Repo already deleted or doesn't exist
                    pass
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to delete GitHub repository: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete remote repository: {str(e)}")
    
    session.delete(project)
    session.commit()
    return {"ok": True, "message": "Project deleted successfully"}

# --- Config & Scan Endpoints ---

@router.put("/{project_id}/config", response_model=ProjectResponse)
async def update_project_config(project_id: int, config: ProjectConfig, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get language setting
    from app.models.settings import AppSettings
    settings = session.exec(select(AppSettings)).first()
    lang = settings.language if settings and hasattr(settings, 'language') else "zh"
    t = lambda key, **kwargs: LogMessages.t(key, lang, **kwargs)
    
    # Get old config before updating
    old_config = project.config
    
    # Debug logging
    print(f"[DEBUG] Updating config for project {project_id}")
    print(f"[DEBUG] Old is_private: {old_config.is_private}")
    print(f"[DEBUG] New is_private: {config.is_private}")
    print(f"[DEBUG] Remote URL: {project.remote_url}")
    print(f"[DEBUG] Visibility changed: {old_config.is_private != config.is_private}")
    
    # Check if visibility changed and update GitHub if needed
    if old_config.is_private != config.is_private and project.remote_url and "github.com" in project.remote_url:
        print(f"[DEBUG] Attempting to update GitHub visibility...")
        visibility = t("visibility_private") if config.is_private else t("visibility_public")
        await log_manager.broadcast(
            t("visibility_updating", visibility=visibility),
            "info"
        )
        
        # Get GitHub token from settings
        from app.models.settings import AppSettings
        settings = session.exec(select(AppSettings)).first()
        
        print(f"[DEBUG] Settings found: {settings is not None}")
        if settings:
            print(f"[DEBUG] Has GitHub token: {bool(settings.github_token)}")
        
        if settings and settings.github_token:
            try:
                visibility = t("visibility_private") if config.is_private else t("visibility_public")
                await GitService.update_repo_visibility(
                    project.remote_url,
                    settings.github_token,
                    config.is_private
                )
                await log_manager.broadcast(
                    t("visibility_updated", visibility=visibility),
                    "success"
                )
            except Exception as e:
                print(f"[DEBUG] Exception updating visibility: {str(e)}")
                await log_manager.broadcast(
                    t("error_visibility_update", error=str(e)),
                    "error"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update repository visibility on GitHub: {str(e)}"
                )
        else:
            print(f"[DEBUG] No GitHub token found in settings")
            await log_manager.broadcast(
                t("error_no_token_in_settings"),
                "error"
            )
            raise HTTPException(
                status_code=400,
                detail="GitHub token is required to update repository visibility. Please configure it in settings."
            )
    else:
        print(f"[DEBUG] Skipping GitHub update - no visibility change or not a GitHub repo")
    
    project.set_config(config)
    session.add(project)
    session.commit()
    session.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        path=project.path,
        remote_url=project.remote_url,
        branch=project.branch,
        last_sync_time=project.last_sync_time,
        status=project.status,
        config=project.config
    )

@router.get("/{project_id}/config", response_model=ProjectConfig)
def get_project_config(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.config

@router.post("/{project_id}/scan")
async def scan_project_changes(project_id: int, lang: str = Query("zh"), session: Session = Depends(get_session)):
    """
    Pre-flight check: scans changed files against project policy.
    """
    t = lambda key, **kwargs: LogMessages.t(key, lang, **kwargs)
    
    await log_manager.broadcast(t("scan_starting", id=project_id), "info")
    
    project = session.get(Project, project_id)
    if not project:
        await log_manager.broadcast(t("error_project_not_found", id=project_id), "error")
        raise HTTPException(status_code=404, detail="Project not found")
    
    await log_manager.broadcast(t("scan_getting_status", path=project.path), "info")
    status = GitService.get_status(project.path)
    if "error" in status:
        await log_manager.broadcast(t("error_git_status", error=status['error']), "error")
        raise HTTPException(status_code=400, detail=status["error"])
    
    changed_files = status.get("changed_files", [])
    await log_manager.broadcast(t("scan_found_files", count=len(changed_files)), "info")
    
    result = ScannerService.scan_directory(project.path, project.config, changed_files)
    
    if result.safe:
        await log_manager.broadcast(t("scan_passed"), "success")
    else:
        await log_manager.broadcast(t("scan_found_risks", count=len(result.risks)), "error")
    
    return {"safe": result.safe, "risks": result.risks}

@router.post("/{project_id}/ignore")
def add_ignore_rule(project_id: int, files: List[str] = Body(...), session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for file_path in files:
        IgnoreService.add_to_gitignore(project.path, file_path)
        
    return {"ok": True, "message": f"Added {len(files)} files to .gitignore"}

@router.get("/{project_id}/gitignore")
def get_gitignore(project_id: int, session: Session = Depends(get_session)):
    """Get .gitignore content for a project"""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    content = IgnoreService.get_gitignore_content(project.path)
    return {"content": content}

@router.put("/{project_id}/gitignore")
def update_gitignore(project_id: int, content: str = Body(..., embed=True), session: Session = Depends(get_session)):
    """Update .gitignore content for a project"""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    IgnoreService.save_gitignore_content(project.path, content)
    return {"ok": True, "message": ".gitignore updated successfully"}

@router.post("/{project_id}/manual-push")
async def manual_push_project(project_id: int, lang: str = Query("zh"), session: Session = Depends(get_session)):
    """Manually trigger a git push for the project"""
    t = lambda key, **kwargs: LogMessages.t(key, lang, **kwargs)
    
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await log_manager.broadcast(t("manual_push_starting", name=project.name), "info", project_id)
    
    # Check if there are changes to push
    try:
        git_info = GitService.get_status(project.path)
        if "error" in git_info:
            await log_manager.broadcast(t("error_git_status", error=git_info['error']), "error", project_id)
            raise HTTPException(status_code=400, detail=git_info["error"])
        
        changed_count = git_info.get("count", 0)
        if changed_count == 0:
            await log_manager.broadcast(t("info_no_changes"), "info", project_id)
            return {
                "ok": True,
                "message": "No changes to push",
                "pushed": False
            }
        
        await log_manager.broadcast(t("sync_detected", count=changed_count), "info", project_id)
    except Exception as e:
        await log_manager.broadcast(t("warning_status_check_failed", error=str(e)), "error", project_id)
        raise HTTPException(status_code=500, detail=str(e))
    
    # Update status to syncing
    project.status = "syncing"
    session.add(project)
    session.commit()
    
    try:
        result = await GitService.sync(project.path, "Manual backup by TuTu's Code Ark")
        
        # Update status to idle
        project.status = "idle"
        from datetime import datetime
        project.last_sync_time = datetime.now()
        session.add(project)
        session.commit()
        
        await log_manager.broadcast(t("push_success"), "success", project_id)
        return {
            "ok": True,
            "message": result,
            "pushed": True
        }
    except Exception as e:
        # Update status to error
        project.status = "error"
        session.add(project)
        session.commit()
        
        await log_manager.broadcast(t("error_push_failed", error=str(e)), "error", project_id)
        raise HTTPException(status_code=500, detail=f"Push failed: {str(e)}")

@router.post("/{project_id}/sync-visibility")
async def sync_repo_visibility(project_id: int, session: Session = Depends(get_session)):
    """Sync repository visibility status from GitHub to local database"""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.remote_url or "github.com" not in project.remote_url:
        raise HTTPException(status_code=400, detail="Not a GitHub repository")
    
    # Get GitHub token and language
    from app.models.settings import AppSettings
    settings = session.exec(select(AppSettings)).first()
    
    if not settings or not settings.github_token:
        raise HTTPException(status_code=400, detail="GitHub token required")
    
    # Get language setting
    lang = settings.language if hasattr(settings, 'language') else "zh"
    t = lambda key, **kwargs: LogMessages.t(key, lang, **kwargs)
    
    try:
        # Get actual visibility from GitHub
        is_private = await GitService.get_repo_visibility(
            project.remote_url,
            settings.github_token
        )
        
        # Update local config
        config = project.config
        config.is_private = is_private
        project.set_config(config)
        session.add(project)
        session.commit()
        session.refresh(project)
        
        visibility = t("visibility_private") if is_private else t("visibility_public")
        await log_manager.broadcast(
            t("visibility_synced", visibility=visibility),
            "success"
        )
        
        return {
            "ok": True,
            "is_private": is_private,
            "message": f"Visibility synced from GitHub: {'Private' if is_private else 'Public'}"
        }
    except Exception as e:
        error_msg = str(e)
        
        # Check if repository was deleted on GitHub (404)
        if "REPO_NOT_FOUND:" in error_msg:
            repo_name = error_msg.split("REPO_NOT_FOUND:")[-1]
            await log_manager.broadcast(
                t("repo_deleted_on_github", repo_name=repo_name),
                "error"
            )
            # Return special status code to indicate repo was deleted
            raise HTTPException(
                status_code=404, 
                detail=f"REPO_DELETED:{repo_name}"
            )
        else:
            await log_manager.broadcast(
                t("error_visibility_sync", error=error_msg),
                "error"
            )
            raise HTTPException(status_code=500, detail=error_msg)