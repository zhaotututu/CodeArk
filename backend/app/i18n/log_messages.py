# -*- coding: utf-8 -*-
"""
多语言日志消息翻译
"""

class LogMessages:
    """日志消息翻译类"""
    
    @staticmethod
    def t(key: str, lang: str = "zh", **kwargs) -> str:
        """
        获取翻译后的日志消息
        
        Args:
            key: 消息键名
            lang: 语言 ('zh' 或 'en')
            **kwargs: 格式化参数
        """
        messages = getattr(LogMessages, f"_{lang}_messages", LogMessages._zh_messages)
        template = messages.get(key, key)
        
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    
    # 中文日志消息
    _zh_messages = {
        # Git 初始化
        "init_local_repo": "  📦 初始化本地 Git 仓库...",
        "local_repo_exists": "  ✅ 本地仓库已存在",
        "new_repo_created": "  ✅ 已创建新的 Git 仓库",
        "check_gitignore": "  📝 检查 .gitignore 文件...",
        "gitignore_created": "  ✅ 已创建 .gitignore 文件",
        "gitignore_exists": "  ✅ .gitignore 文件已存在",
        
        # GitHub 连接
        "connecting_github": "  🌐 连接 GitHub API...",
        "connected_to_user": "  ✅ 已连接到 GitHub 用户: {username}",
        "checking_repo_exists": "  🔍 检查 GitHub 仓库是否存在: {name}...",
        "repo_exists": "  ✅ 仓库已存在: {url}",
        "remote_has_commits": "  ⚠️ 远程仓库已有 {count} 个提交",
        "remote_is_empty": "  ℹ️ 远程仓库为空",
        "creating_repo": "  ➕ 创建新仓库: {name} (私有: {is_private})...",
        "repo_created": "  ✅ 仓库创建成功: {url}",
        
        # 远程配置
        "configuring_remote": "  🔗 配置远程仓库...",
        "old_remote_deleted": "  🔄 已删除旧的 origin 远程",
        "remote_added": "  ✅ 已添加 origin 远程仓库",
        
        # 提交推送
        "preparing_commit": "  📤 准备提交和推送...",
        "files_staged": "  📋 已暂存 {count} 个文件",
        "initial_commit_created": "  ✅ 已创建初始提交",
        "initial_commit_created_with_msg": "  ✅ 已创建初始提交: 'Initial commit by TuTu's Code Ark'",
        "no_files_to_commit": "  ⚠️ 没有文件需要提交",
        "branch_renamed": "  🔄 已重命名分支为 main",
        "pushing_to_github": "  🚀 正在推送到 GitHub...",
        "pulling_remote": "  🔄 远程仓库已存在，尝试拉取最新内容...",
        "remote_merged": "  ✅ 已合并远程内容",
        "cannot_merge": "  ⚠️ 无法自动合并，将使用强制推送",
        "remote_will_overwrite": "  ⚠️ 远程内容将被本地覆盖",
        "force_push_success": "  ✅ 强制推送成功",
        "fetch_failed": "  ℹ️ 远程拉取失败，尝试直接推送: {error}",
        "push_success": "  ✅ 推送成功！代码已上传到 GitHub",
        "normal_push_failed": "  ⚠️ 常规推送失败，尝试强制推送...",
        "force_push_overwrite": "  ✅ 强制推送成功（远程内容已被覆盖）",
        
        # 项目初始化
        "starting_init": "[INIT] Starting project initialization: {name}",
        "checking_token": "[INIT] No token provided, checking global settings...",
        "using_saved_token": "[SUCCESS] Using saved GitHub token",
        "step1": "[INIT] Step 1/5: Checking local path {path}",
        "path_exists": "[SUCCESS] Path already exists: {path}",
        "step2": "[INIT] Step 2/5: Checking if project already exists",
        "no_duplicate": "[SUCCESS] No duplicate found, proceeding",
        "step3": "[INIT] Step 3/5: Initializing Git repository and pushing to GitHub",
        "git_init_complete": "[SUCCESS] Git initialization complete, remote repo: {url}",
        "step4": "[INIT] Step 4/5: Saving project info to database",
        "saved_to_db": "[SUCCESS] Project saved to database (ID: {id})",
        "step5": "[INIT] Step 5/5: Starting file monitoring service",
        "monitoring_started": "[SUCCESS] File monitoring started, will auto-sync changes",
        "init_complete": "[COMPLETE] Project initialization complete! Project is ready",
        "started_watching": "Started watching: {name}",
        
        # 同步
        "sync_detected": "[SYNC] Detected {count} file change(s), starting sync...",
        "sync_complete": "[SUCCESS] Sync complete: Push successful",
        "status_updated": "[SUCCESS] Status updated to: idle",
        
        # 扫描
        "scan_starting": "[SCAN] 开始扫描项目 {id}",
        "scan_getting_status": "[SCAN] 正在获取 Git 状态: {path}",
        "scan_found_files": "[SCAN] 发现 {count} 个变更文件",
        "scan_passed": "[SCAN] 安全扫描通过：未检测到风险",
        "scan_found_risks": "[SCAN] 安全扫描发现 {count} 个风险文件",
        
        # 系统
        "connected_to_log_stream": "已连接到日志流",
        
        # 可见性同步
        "visibility_synced": "[SUCCESS] 已从 GitHub 同步可见性：{visibility}",
        "visibility_updated": "[SUCCESS] 已将仓库可见性更新为 {visibility}",
        "visibility_updating": "[INFO] 正在调用 GitHub API 设置可见性为 {visibility}...",
        
        # 错误消息
        "error_no_token": "[ERROR] 没有可用的 GitHub 令牌",
        "error_directory_create": "[ERROR] 创建目录失败：{error}",
        "error_git_init": "[ERROR] Git 初始化失败：{error}",
        "error_project_exists": "[WARNING] 项目已被图图的代码方舟管理",
        "error_project_not_found": "[SCAN] 未找到项目 {id}",
        "error_git_status": "[SCAN] Git 错误：{error}",
        "error_visibility_update": "[ERROR] 更新 GitHub 仓库可见性失败：{error}",
        "error_visibility_sync": "[ERROR] 同步可见性失败：{error}",
        "repo_deleted_on_github": "⚠️ GitHub 仓库已被删除: {repo_name}",
        "error_no_token_in_settings": "[ERROR] 设置中没有找到 GitHub 令牌",
        
        # 成功消息
        "success_directory_created": "[SUCCESS] 目录已创建：{path}",
        
        # 可见性文本
        "visibility_private": "私有",
        "visibility_public": "公开",
        
        # 监控错误
        "error_watch_failed": "监控失败 {name}：{error}",
        "warning_sync_skipped": "[WARNING] 跳过同步：{error}",
        "warning_status_check_failed": "[WARNING] 文件状态检查失败：{error}",
        "error_sync_failed": "[ERROR] 同步失败：{error}",
        "warning_status_error": "[WARNING] 状态已更新为：错误",
        "info_no_changes": "[INFO] 未检测到文件更改，跳过同步",
        
        # 手动推送
        "manual_push_starting": "[PUSH] 开始手动推送项目：{name}",
        "error_push_failed": "[ERROR] 推送失败：{error}",
    }
    
    # 英文日志消息
    _en_messages = {
        # Git initialization
        "init_local_repo": "  📦 Initializing local Git repository...",
        "local_repo_exists": "  ✅ Local repository already exists",
        "new_repo_created": "  ✅ New Git repository created",
        "check_gitignore": "  📝 Checking .gitignore file...",
        "gitignore_created": "  ✅ .gitignore file created",
        "gitignore_exists": "  ✅ .gitignore file already exists",
        
        # GitHub connection
        "connecting_github": "  🌐 Connecting to GitHub API...",
        "connected_to_user": "  ✅ Connected to GitHub user: {username}",
        "checking_repo_exists": "  🔍 Checking if GitHub repository exists: {name}...",
        "repo_exists": "  ✅ Repository exists: {url}",
        "remote_has_commits": "  ⚠️ Remote repository has {count} commit(s)",
        "remote_is_empty": "  ℹ️ Remote repository is empty",
        "creating_repo": "  ➕ Creating new repository: {name} (private: {is_private})...",
        "repo_created": "  ✅ Repository created successfully: {url}",
        
        # Remote configuration
        "configuring_remote": "  🔗 Configuring remote repository...",
        "old_remote_deleted": "  🔄 Old origin remote deleted",
        "remote_added": "  ✅ Origin remote added",
        
        # Commit & push
        "preparing_commit": "  📤 Preparing to commit and push...",
        "files_staged": "  📋 Staged {count} file(s)",
        "initial_commit_created": "  ✅ Initial commit created",
        "initial_commit_created_with_msg": "  ✅ Initial commit created: 'Initial commit by TuTu's Code Ark'",
        "no_files_to_commit": "  ⚠️ No files to commit",
        "branch_renamed": "  🔄 Branch renamed to main",
        "pushing_to_github": "  🚀 Pushing to GitHub...",
        "pulling_remote": "  🔄 Remote repository exists, pulling latest content...",
        "remote_merged": "  ✅ Remote content merged",
        "cannot_merge": "  ⚠️ Cannot auto-merge, will force push",
        "remote_will_overwrite": "  ⚠️ Remote content will be overwritten",
        "force_push_success": "  ✅ Force push successful",
        "fetch_failed": "  ℹ️ Remote fetch failed, trying direct push: {error}",
        "push_success": "  ✅ Push successful! Code uploaded to GitHub",
        "normal_push_failed": "  ⚠️ Normal push failed, trying force push...",
        "force_push_overwrite": "  ✅ Force push successful (remote content overwritten)",
        
        # Project initialization
        "starting_init": "[INIT] Starting project initialization: {name}",
        "checking_token": "[INIT] No token provided, checking global settings...",
        "using_saved_token": "[SUCCESS] Using saved GitHub token",
        "step1": "[INIT] Step 1/5: Checking local path {path}",
        "path_exists": "[SUCCESS] Path already exists: {path}",
        "step2": "[INIT] Step 2/5: Checking if project already exists",
        "no_duplicate": "[SUCCESS] No duplicate found, proceeding",
        "step3": "[INIT] Step 3/5: Initializing Git repository and pushing to GitHub",
        "git_init_complete": "[SUCCESS] Git initialization complete, remote repo: {url}",
        "step4": "[INIT] Step 4/5: Saving project info to database",
        "saved_to_db": "[SUCCESS] Project saved to database (ID: {id})",
        "step5": "[INIT] Step 5/5: Starting file monitoring service",
        "monitoring_started": "[SUCCESS] File monitoring started, will auto-sync changes",
        "init_complete": "[COMPLETE] Project initialization complete! Project is ready",
        "started_watching": "Started watching: {name}",
        
        # Sync
        "sync_detected": "[SYNC] Detected {count} file change(s), starting sync...",
        "sync_complete": "[SUCCESS] Sync complete: Push successful",
        "status_updated": "[SUCCESS] Status updated to: idle",
        
        # Scan
        "scan_starting": "[SCAN] Starting security scan for project {id}",
        "scan_getting_status": "[SCAN] Getting Git status for {path}",
        "scan_found_files": "[SCAN] Found {count} changed file(s)",
        "scan_passed": "[SCAN] Security scan passed: no risks detected",
        "scan_found_risks": "[SCAN] Security scan found {count} risky file(s)",
        
        # System
        "connected_to_log_stream": "Connected to log stream",
        
        # Visibility sync
        "visibility_synced": "[SUCCESS] Synced visibility from GitHub: {visibility}",
        "visibility_updated": "[SUCCESS] Repository visibility updated to {visibility} on GitHub",
        "visibility_updating": "[INFO] Calling GitHub API to set visibility to {visibility}...",
        
        # Error messages
        "error_no_token": "[ERROR] No GitHub token available",
        "error_directory_create": "[ERROR] Failed to create directory: {error}",
        "error_git_init": "[ERROR] Git initialization failed: {error}",
        "error_project_exists": "[WARNING] Project already managed by TuTu's Code Ark",
        "error_project_not_found": "[SCAN] Project {id} not found",
        "error_git_status": "[SCAN] Git error: {error}",
        "error_visibility_update": "[ERROR] Failed to update GitHub repository visibility: {error}",
        "error_visibility_sync": "[ERROR] Failed to sync visibility: {error}",
        "repo_deleted_on_github": "⚠️ GitHub repository has been deleted: {repo_name}",
        "error_no_token_in_settings": "[ERROR] No GitHub token found in settings",
        
        # Success messages
        "success_directory_created": "[SUCCESS] Directory created: {path}",
        
        # Visibility text
        "visibility_private": "Private",
        "visibility_public": "Public",
        
        # Monitoring errors
        "error_watch_failed": "Failed to watch {name}: {error}",
        "warning_sync_skipped": "[WARNING] Skipping sync: {error}",
        "warning_status_check_failed": "[WARNING] Failed to check file status: {error}",
        "error_sync_failed": "[ERROR] Sync failed: {error}",
        "warning_status_error": "[WARNING] Status updated to: error",
        "info_no_changes": "[INFO] No file changes detected, skipping sync",
        
        # Manual push
        "manual_push_starting": "[PUSH] Starting manual push for project: {name}",
        "error_push_failed": "[ERROR] Push failed: {error}",
    }

