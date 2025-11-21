import asyncio
from git import Repo, GitCommandError
from typing import List, Dict, Any
import os
from github import Github, GithubException
from app.i18n.log_messages import LogMessages

class GitService:
    @staticmethod
    def is_valid_repo(path: str) -> bool:
        try:
            _ = Repo(path)
            return True
        except (GitCommandError, Exception):
            return False

    @staticmethod
    def get_repo_info(path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")
            
        try:
            repo = Repo(path)
            branch = repo.active_branch.name
            remotes = [r.url for r in repo.remotes]
            remote_url = remotes[0] if remotes else None
            
            return {
                "is_repo": True,
                "branch": branch,
                "remote_url": remote_url,
                "is_dirty": repo.is_dirty() or len(repo.untracked_files) > 0
            }
        except (GitCommandError, TypeError, ValueError):
            # Not a git repo or detached head
            return {
                "is_repo": False,
                "branch": None,
                "remote_url": None,
                "is_dirty": False
            }
    
    @staticmethod
    def get_status(path: str) -> Dict[str, Any]:
        try:
            repo = Repo(path)
            # Get changed files
            changed = [item.a_path for item in repo.index.diff(None)]
            changed.extend(repo.untracked_files)
            return {
                "changed_files": changed,
                "count": len(changed)
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def sync(path: str, message: str = "Backup by TuTu's Code Ark") -> str:
        # Run blocking git operations in a thread
        return await asyncio.to_thread(GitService._sync_sync, path, message)

    @staticmethod
    def _sync_sync(path: str, message: str) -> str:
        repo = Repo(path)
        if not repo.remotes:
            raise Exception("No remote configured")
        
        # Check if there are changes
        if not (repo.is_dirty() or repo.untracked_files):
            return "No changes to push"

        repo.git.add(all=True)
        # Ensure message ends with signature
        if not message.endswith("by TuTu's Code Ark"):
            message = f"{message} by TuTu's Code Ark"
        repo.index.commit(message)
        
        # Push to current active branch
        origin = repo.remote(name='origin')
        current_branch = repo.active_branch.name
        origin.push(refspec=f'{current_branch}:{current_branch}', set_upstream=True)
        return "Push successful"

    @staticmethod
    async def init_and_push_to_github(path: str, name: str, token: str, private: bool, log_callback=None, lang: str = "zh", gitignore_content: str = None, description: str = None) -> str:
        log_messages = []
        
        def sync_log(msg: str, level: str = "info"):
            log_messages.append((msg, level))
        
        result = await asyncio.to_thread(GitService._init_and_push_sync, path, name, token, private, sync_log, lang, gitignore_content, description)
        
        # 批量发送日志消息
        if log_callback:
            for msg, level in log_messages:
                await log_callback(msg, level)
        
        return result

    @staticmethod
    def _init_and_push_sync(path: str, name: str, token: str, private: bool, log_callback=None, lang: str = "zh", gitignore_content: str = None, description: str = None) -> str:
        t = lambda key, **kwargs: LogMessages.t(key, lang, **kwargs)
        
        def log(msg: str, level: str = "info"):
            if log_callback:
                log_callback(msg, level)
        
        # 1. Initialize local repo
        log(t("init_local_repo"))
        if not os.path.exists(path):
            os.makedirs(path)
        
        try:
            repo = Repo(path)
            log(t("local_repo_exists"), "success")
        except:
            repo = Repo.init(path)
            log(t("new_repo_created"), "success")
            
        # 2. Create .gitignore if not exists
        log(t("check_gitignore"))
        gitignore_path = os.path.join(path, ".gitignore")
        if not os.path.exists(gitignore_path):
            # 使用自定义内容或默认内容
            content = gitignore_content if gitignore_content else "__pycache__/\n*.log\nnode_modules/\n.DS_Store\n.venv/\ndist/\n"
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write(content)
            log(t("gitignore_created"), "success")
        else:
            log(t("gitignore_exists"), "success")

        # 3. Create Repo on GitHub
        log(t("connecting_github"))
        g = Github(token)
        user = g.get_user()
        log(t("connected_to_user", username=user.login), "success")
        
        log(t("checking_repo_exists", name=name))
        repo_exists = False
        try:
            # Check if repo exists
            gh_repo = user.get_repo(name)
            remote_url = gh_repo.clone_url
            repo_exists = True
            log(t("repo_exists", url=remote_url), "success")
            
            # Check if remote repo has commits
            try:
                commits = list(gh_repo.get_commits())
                if len(commits) > 0:
                    log(t("remote_has_commits", count=len(commits)), "info")
            except:
                log(t("remote_is_empty"), "info")
                
        except GithubException:
            # Create new
            log(t("creating_repo", name=name, is_private=private))
            gh_repo = user.create_repo(
                name=name, 
                private=private, 
                auto_init=False,
                description=description if description else None
            )
            remote_url = gh_repo.clone_url
            log(t("repo_created", url=remote_url), "success")
            
        # Insert token into URL for auth (or configure credential helper)
        # Safe format: https://oauth2:TOKEN@github.com/USER/REPO.git
        auth_remote_url = remote_url.replace("https://", f"https://oauth2:{token}@")

        # 4. Add Remote
        log(t("configuring_remote"))
        if 'origin' in repo.remotes:
            repo.delete_remote('origin')
            log(t("old_remote_deleted"), "info")
        
        repo.create_remote('origin', auth_remote_url)
        log(t("remote_added"), "success")
        
        # 5. Initial Commit & Push
        log(t("preparing_commit"))
        repo.git.add(all=True)
        files_count = len(repo.untracked_files) + len([item for item in repo.index.diff(None)])
        log(t("files_staged", count=files_count), "info")
        
        if not repo.is_dirty() and not repo.untracked_files:
             # try commit anyway in case it's a fresh init
             try:
                 repo.index.commit("Initial commit by TuTu's Code Ark")
                 log(t("initial_commit_created"), "success")
             except:
                 log(t("no_files_to_commit"), "info")
                 pass 
        else:
             repo.index.commit("Initial commit by TuTu's Code Ark")
             log(t("initial_commit_created_with_msg"), "success")

        origin = repo.remote(name='origin')
        # Rename branch to main if needed
        if repo.active_branch.name != 'main':
            repo.git.branch('-M', 'main')
            log(t("branch_renamed"), "info")
            
        log(t("pushing_to_github"))
        
        # If repo exists on GitHub, try to pull first to avoid conflicts
        if repo_exists:
            try:
                log(t("pulling_remote"))
                origin.fetch()
                
                # Try to merge if there are remote commits
                try:
                    repo.git.merge('origin/main', '--allow-unrelated-histories', '--no-edit')
                    log(t("remote_merged"), "success")
                except GitCommandError as merge_error:
                    # If merge fails, we'll force push with a warning
                    log(t("cannot_merge"), "info")
                    log(t("remote_will_overwrite"), "info")
                    origin.push(refspec='main:main', set_upstream=True, force=True)
                    log(t("force_push_success"), "success")
                    return remote_url
            except Exception as fetch_error:
                log(t("fetch_failed", error=str(fetch_error)), "info")
        
        # Normal push for new repos or after successful merge
        try:
            origin.push(refspec='main:main', set_upstream=True)
            log(t("push_success"), "success")
        except GitCommandError as push_error:
            # If normal push fails, force push
            log(t("normal_push_failed"), "info")
            origin.push(refspec='main:main', set_upstream=True, force=True)
            log(t("force_push_overwrite"), "success")
        
        return remote_url
    
    @staticmethod
    async def update_repo_visibility(remote_url: str, token: str, is_private: bool) -> bool:
        """Update GitHub repository visibility (public/private)"""
        return await asyncio.to_thread(GitService._update_repo_visibility_sync, remote_url, token, is_private)
    
    @staticmethod
    def _update_repo_visibility_sync(remote_url: str, token: str, is_private: bool) -> bool:
        """Sync version of update_repo_visibility"""
        try:
            print(f"[DEBUG] _update_repo_visibility_sync called")
            print(f"[DEBUG] Remote URL: {remote_url}")
            print(f"[DEBUG] Setting private to: {is_private}")
            
            if not remote_url or "github.com" not in remote_url:
                raise ValueError("Not a GitHub repository")
            
            print(f"[DEBUG] Connecting to GitHub...")
            g = Github(token)
            user = g.get_user()
            print(f"[DEBUG] Connected as user: {user.login}")
            
            # Extract repo name from URL
            # URL format: https://github.com/username/repo.git or https://github.com/username/repo
            repo_name = remote_url.split("/")[-1].replace(".git", "")
            print(f"[DEBUG] Extracted repo name: {repo_name}")
            
            # Get the repository
            print(f"[DEBUG] Getting repository...")
            repo = user.get_repo(repo_name)
            print(f"[DEBUG] Current repo private status: {repo.private}")
            
            # Update visibility
            print(f"[DEBUG] Calling repo.edit(private={is_private})...")
            repo.edit(private=is_private)
            print(f"[DEBUG] Successfully updated repository visibility!")
            
            return True
        except GithubException as e:
            print(f"[DEBUG] GithubException: {str(e)}")
            raise Exception(f"Failed to update repository visibility: {str(e)}")
        except Exception as e:
            print(f"[DEBUG] General Exception: {str(e)}")
            raise Exception(f"Error updating repository: {str(e)}")
    
    @staticmethod
    async def get_repo_visibility(remote_url: str, token: str) -> bool:
        """Get current GitHub repository visibility status"""
        return await asyncio.to_thread(GitService._get_repo_visibility_sync, remote_url, token)
    
    @staticmethod
    def _get_repo_visibility_sync(remote_url: str, token: str) -> bool:
        """Sync version of get_repo_visibility - returns True if private, False if public"""
        try:
            if not remote_url or "github.com" not in remote_url:
                raise ValueError("Not a GitHub repository")
            
            g = Github(token)
            user = g.get_user()
            
            # Extract repo name from URL
            # Handle URLs with authentication (e.g., https://oauth2:TOKEN@github.com/user/repo.git)
            clean_url = remote_url.split('@')[-1] if '@' in remote_url else remote_url
            repo_name = clean_url.split("/")[-1].replace(".git", "")
            
            # Get the repository
            repo = user.get_repo(repo_name)
            
            return repo.private
        except GithubException as e:
            if e.status == 404:
                # Repository not found - return special error
                raise Exception(f"REPO_NOT_FOUND:{repo_name}")
            else:
                raise Exception(f"Failed to get repository visibility: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to get repository visibility: {str(e)}")