import asyncio
import time
from datetime import datetime
from typing import Dict, Set, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlmodel import Session, select
from app.core.database import engine
from app.models.project import Project
from app.models.settings import AppSettings
from app.services.git_service import GitService
from app.services.logger import manager as log_manager
from app.i18n.log_messages import LogMessages

class DebounceHandler(FileSystemEventHandler):
    def __init__(self, project_id: int, callback):
        self.project_id = project_id
        self.callback = callback

    def on_modified(self, event):
        if event.is_directory:
            return
        if ".git" in event.src_path:
            return
        # 过滤常见的临时文件和日志文件
        # 重要：忽略数据库文件，避免状态更新触发循环监控
        ignored_patterns = ['.log', '.tmp', '.cache', '__pycache__', 'node_modules', '.DS_Store', '.swp', '~', '.db', '.db-journal', '.db-wal', '.db-shm']
        if any(pattern in event.src_path for pattern in ignored_patterns):
            return
        self.callback(self.project_id)

    def on_created(self, event):
        if event.is_directory:
            return
        if ".git" in event.src_path:
            return
        # 过滤常见的临时文件和日志文件
        # 重要：忽略数据库文件，避免状态更新触发循环监控
        ignored_patterns = ['.log', '.tmp', '.cache', '__pycache__', 'node_modules', '.DS_Store', '.swp', '~', '.db', '.db-journal', '.db-wal', '.db-shm']
        if any(pattern in event.src_path for pattern in ignored_patterns):
            return
        self.callback(self.project_id)

class WatcherService:
    def __init__(self):
        self.observer = Observer()
        self.observer.start()
        self.watched_projects: Dict[int, Any] = {}
        self.pending_syncs: Dict[int, float] = {} # project_id -> last_event_time
        self.is_running = False
    
    def _get_language(self, session: Session) -> str:
        """Get the global language setting from database"""
        settings = session.exec(select(AppSettings)).first()
        return settings.language if settings and hasattr(settings, 'language') else "zh"

    def start(self):
        self.is_running = True
        asyncio.create_task(self._sync_loop())
        self.refresh_watchers()

    def stop(self):
        self.is_running = False
        self.observer.stop()
        self.observer.join()

    def refresh_watchers(self):
        """Reloads projects from DB and updates watchdog observers"""
        with Session(engine) as session:
            projects = session.exec(select(Project)).all()
            
            for p in projects:
                # 只要开启了 auto_push，我们就监控文件变化
                # 即使是定时模式，我们也需要知道是否有文件变化，以便决定是否需要推送
                if p.config.auto_push:
                    if p.id not in self.watched_projects:
                         self._watch_project(p)
                
            # Remove deleted or disabled watchers (TODO: Optimize this)
    
    def watch_project(self, project: Project):
        """Public method to watch a single project"""
        self._watch_project(project)
            
    def _watch_project(self, project: Project):
        try:
            if project.id in self.watched_projects:
                return
                
            handler = DebounceHandler(project.id, self._on_file_change)
            watch = self.observer.schedule(handler, project.path, recursive=True)
            self.watched_projects[project.id] = watch
            
            # Get language setting for log
            with Session(engine) as session:
                lang = self._get_language(session)
                msg = LogMessages.t("started_watching", lang, name=project.name)
                asyncio.create_task(log_manager.broadcast(msg, "info", project.id))
        except Exception as e:
            # Get language setting for error log
            with Session(engine) as session:
                lang = self._get_language(session)
                msg = LogMessages.t("error_watch_failed", lang, name=project.name, error=str(e))
                asyncio.create_task(log_manager.broadcast(msg, "error", project.id))

    def _on_file_change(self, project_id: int):
        # Update the last modified time for debounce
        # If key exists, update it. If not, create it.
        self.pending_syncs[project_id] = time.time()

    async def _sync_loop(self):
        while self.is_running:
            now = time.time()
            
            # Iterate over a copy of keys to allow modification
            for pid in list(self.pending_syncs.keys()):
                try:
                    with Session(engine) as session:
                        project = session.get(Project, pid)
                        # If project deleted or auto_push disabled, remove from pending
                        if not project or not project.config.auto_push:
                            del self.pending_syncs[pid]
                            continue
                        
                        should_sync = False
                        
                        mode = project.config.sync_mode
                        
                        # Only support interval and fixed modes (auto mode removed)
                        if mode == 'interval':
                            # Check interval
                            last_sync = project.last_sync_time.timestamp() if project.last_sync_time else 0
                            interval = project.config.sync_interval
                            if interval < 60: interval = 60 # Minimum 1 min
                            
                            if now - last_sync > interval:
                                should_sync = True
                                
                        elif mode == 'fixed':
                            # Check fixed time
                            try:
                                target_h, target_m = map(int, project.config.sync_fixed_time.split(':'))
                                dt = datetime.now()
                                if dt.hour == target_h and dt.minute == target_m:
                                    # Only sync if not synced recently (in last 65 seconds)
                                    last_sync = project.last_sync_time
                                    if not last_sync or (dt - last_sync).total_seconds() > 65:
                                        should_sync = True
                            except:
                                pass
                                
                        if should_sync:
                            del self.pending_syncs[pid]
                            await self._trigger_sync(pid)
                            
                except Exception as e:
                    print(f"Error in sync loop for project {pid}: {e}")
                    
            await asyncio.sleep(1)

    async def _trigger_sync(self, project_id: int):
        with Session(engine) as session:
            project = session.get(Project, project_id)
            if not project or not project.config.auto_push:
                return
            
            # Get language setting
            lang = self._get_language(session)
            t = lambda key, **kwargs: LogMessages.t(key, lang, **kwargs)

            # Check if there are actual changes to avoid unnecessary pushes
            try:
                git_info = GitService.get_status(project.path)
                if "error" in git_info:
                    await log_manager.broadcast(t("warning_sync_skipped", error=git_info['error']), "info", project_id)
                    return
                
                changed_count = git_info.get("count", 0)
                if changed_count == 0:
                    await log_manager.broadcast(t("info_no_changes"), "info", project_id)
                    # Even if no changes, update status to idle
                    project.status = "idle"
                    session.add(project)
                    session.commit()
                    return
                
                await log_manager.broadcast(t("sync_detected", count=changed_count), "info", project_id)
            except Exception as e:
                await log_manager.broadcast(t("warning_status_check_failed", error=str(e)), "info", project_id)
            
            # Update status to syncing
            project.status = "syncing"
            session.add(project)
            session.commit()
            
            try:
                result = await GitService.sync(project.path, message=f"{project.config.default_commit_prefix} Auto backup")
                await log_manager.broadcast(t("sync_complete"), "success", project_id)
                
                project.last_sync_time = datetime.now()
                project.status = "idle"
                session.add(project)
                session.commit()
                await log_manager.broadcast(t("status_updated"), "info", project_id)
            except Exception as e:
                await log_manager.broadcast(t("error_sync_failed", error=str(e)), "error", project_id)
                project.status = "error"
                session.add(project)
                session.commit()
                await log_manager.broadcast(t("warning_status_error"), "error", project_id)

watcher_service = WatcherService()

