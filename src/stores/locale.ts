import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';

type Locale = 'zh' | 'en';

export const useLocaleStore = defineStore('locale', () => {
  const currentLocale = ref<Locale>('zh'); // 默认中文

  const toggleLocale = () => {
    currentLocale.value = currentLocale.value === 'zh' ? 'en' : 'zh';
  };
  
  // 监听语言变化，同步到后端
  watch(currentLocale, async (newLang) => {
    try {
      await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: newLang })
      });
    } catch (e) {
      console.error('[LOCALE] Failed to sync language to backend:', e);
    }
  });

  const messages = {
    zh: {
      nav: {
        title: '图图的代码方舟',
        refresh: '刷新数据',
        addRepo: '新建项目',
        connect: '连接本地文件夹',
      },
      dashboard: {
        title: '指挥中心',
        subtitle: '全自动 Git 托管与版本控制系统',
        noRepos: '暂无服役舰队',
        noReposSub: '初始化您的第一个全托管项目，图图的代码方舟将自动完成 Git 初始化、远程库创建及首次推送。',
        connectBtn: '🚀 启动新项目',
        branch: '当前分支',
        status: {
          idle: '系统待机',
          watching: '实时监控中',
          syncing: '正在同步数据...',
          error: '连接异常',
        },
        scan: '安全扫描',
        push: '立即推送',
        settings: '配置',
        terminalTitle: '系统终端',
        visibility: {
          private: '私有仓库',
          public: '公开仓库',
        },
        syncMode: {
          auto: '自动同步',
          interval: '间隔同步',
          fixed: '定时同步',
        },
      },
      addModal: {
        title: '项目初始化向导',
        subtitle: {
          auto: '快速设置全自动 Git + GitHub 托管',
          manual: '连接现有的 Git 项目进行监控'
        },
        tabs: {
            auto: '✨ 自动托管 (推荐)',
            manual: '🔗 手动连接'
        },
        autoDesc: '适用于新项目。图图的代码方舟将为您处理 Git Init、GitHub 建库和远程关联。',
        manualDesc: '适用于已有 Git 项目。仅做本地监控，需您手动处理远程关联。',
        pathLabel: '本地工作区路径',
        pathPlaceholder: '例如 D:\\Projects\\NewApp',
        browseFolder: '浏览文件夹',
        nameLabel: '项目代号 (Repo Name)',
        descriptionLabel: '仓库描述 (可选)',
        descriptionPlaceholder: '简要描述这个项目的用途...',
        tokenLabel: 'GitHub 访问令牌 (PAT)',
        tokenPlaceholder: 'ghp_xxxxxxxxxxxx',
        tokenHelp: '❓ 如何获取 Token？',
        privateLabel: '创建为私有仓库 (Private)',
        
        gitignore: {
          title: '.gitignore 配置',
          edit: '编辑',
          description: '📝 自定义忽略规则（默认已包含常见文件）',
          editorTitle: '.gitignore 编辑器',
          commonPatterns: '快速添加常见规则',
          fileContent: '文件内容',
          placeholder: '# 添加需要忽略的文件和目录\nnode_modules/\n__pycache__/\n*.log',
          hint: '💡 每行一个规则，支持通配符 * 和 ?',
          close: '关闭',
          done: '完成'
        },
        
        sync: {
          label: '同步策略',
          mode: {
              auto: '⚡ 自动同步 (变动即推)',
              interval: '⏱️ 间隔同步',
              fixed: '📅 定时同步'
          },
          intervalLabel: '间隔时间 (分钟)',
          fixedLabel: '每天定时 (HH:MM)',
          autoDesc: '检测到文件变化后自动推送 (防抖 10s)',
        },

        guideTitle: '如何获取 GitHub Token?',
        guideStep1: '1. 点击下方按钮前往 GitHub 设置页',
        guideStep2: '2. 点击 "Generate new token (classic)"',
        guideStep3: '3. 勾选 "repo" 和 "workflow" 权限',
        guideStep4: '4. 复制生成的 Token 填入左侧',
        openGithub: '前往 GitHub Token 页面 ↗',
        
        helpDialog: {
          title: '📘 GitHub Token 获取指南',
          step1Title: '第一步：访问 GitHub 设置',
          step1Desc: '点击下方按钮，或手动访问：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)',
          step2Title: '第二步：生成新 Token',
          step2Desc: '点击 "Generate new token (classic)" 按钮。给 Token 起一个名字，如 "图图的代码方舟自动备份"。',
          step3Title: '第三步：选择权限',
          step3Desc: '必须勾选以下权限：',
          step3Items: ['✓ repo — 完整仓库控制权限', '✓ workflow — GitHub Actions权限'],
          step4Title: '第四步：生成并复制',
          step4Desc: '点击页面底部的 "Generate token"。复制生成的 Token（以 ghp_ 开头），粘贴到左侧输入框。',
          warning: '⚠️ 安全提示：Token 生成后只显示一次，请妥善保管。图图的代码方舟仅在本地存储 Token，不会上传到任何服务器。',
          openBtn: '立即前往 GitHub',
          closeBtn: '我知道了'
        },
        
        cancel: '取消',
        confirm: '🚀 开始初始化',
        manualConfirm: '📂 添加项目',
        error: '操作失败: ',
        processing: '系统正在初始化环境...',
        browseFailure: '文件夹选择功能仅在 Tauri 环境中可用。请手动输入路径。',
        confirmBtn: '确定'
      },
      tokenDialog: {
        title: 'GitHub Token 配置',
        subtitle: '配置一次，全局可用',
        tokenConfigured: '✓ Token 已配置',
        clearToken: '清除',
        notConfigured: '⚠️ 未配置 GitHub Token',
        notConfiguredDesc: '配置后可自动创建GitHub仓库',
        tokenLabel: 'GitHub Personal Access Token',
        tokenPlaceholder: 'ghp_xxxxxxxxxxxx',
        tokenHelp: '❓ 如何获取 Token？',
        securityNote: '安全提示：',
        securityDesc: 'Token 将加密保存在本地数据库，仅用于自动创建GitHub仓库。图图的代码方舟不会将您的Token上传到任何服务器。',
        cancel: '取消',
        save: '💾 保存配置',
        saving: '保存中...',
        
        helpDialog: {
          title: '📘 GitHub Token 获取指南',
          step1Title: '第一步：访问 GitHub 设置',
          step1Desc: '前往 GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)',
          step2Title: '第二步：生成新 Token',
          step2Desc: '点击 "Generate new token (classic)"，设置名称如 "图图的代码方舟"',
          step3Title: '第三步：选择权限',
          repoPermission: '— 完整仓库控制权限',
          workflowPermission: '— GitHub Actions权限',
          step4Title: '第四步：复制 Token',
          step4Desc: '生成后立即复制（以ghp_开头），粘贴到配置框',
          warning: '⚠️ Token只显示一次，请妥善保管！',
          openBtn: '🔗 立即前往 GitHub',
          closeBtn: '关闭'
        },
        
        errorMsg: {
          emptyToken: '请输入GitHub Token',
          saveFailed: '保存失败，请重试',
          clearFailed: '清除失败: ',
          browserBlocked: '无法自动打开浏览器。\n\n是否复制 URL 到剪贴板？',
          urlCopied: 'URL 已复制到剪贴板！\n\n请粘贴到浏览器地址栏打开。',
          copyPrompt: '请复制以下 URL：',
          copyManual: '请复制以下 URL 并在浏览器中打开：'
        },
        
        successMsg: {
          tokenSaved: 'GitHub Token 保存成功！',
          tokenCleared: 'Token 已清除'
        },
        
        confirmDialog: {
          title: '确认操作',
          message: '确定要清除已保存的GitHub Token吗？',
          cancel: '取消',
          confirm: '确定'
        },
        
        dialogButtons: {
          success: '成功',
          error: '错误',
          confirm: '确定'
        }
      },
      wizard: {
        steps: {
          initGit: '初始化 Git 仓库...',
          createRepo: '在 GitHub 创建仓库...',
          linkRemote: '关联远程仓库...',
          firstCommit: '提交初始文件...',
          scanning: '扫描本地仓库...',
          analyzing: '分析 Git 历史...',
          configuring: '配置监控策略...',
          complete: '完成！'
        }
      },
      riskDialog: {
        title: '⚠️ 安全策略拦截',
        desc: '以下文件违反了备份策略（如体积过大或敏感格式）。',
        ignore: '添加至忽略列表',
        cancel: '取消操作',
        safeMsg: '✅ 扫描通过，文件安全。',
      },
      log: {
        // Git 初始化日志
        initLocalRepo: '📦 初始化本地 Git 仓库...',
        localRepoExists: '✅ 本地仓库已存在',
        newRepoCreated: '✅ 已创建新的 Git 仓库',
        checkGitignore: '📝 检查 .gitignore 文件...',
        gitignoreCreated: '✅ 已创建 .gitignore 文件',
        gitignoreExists: '✅ .gitignore 文件已存在',
        
        // GitHub 连接日志
        connectingGithub: '🌐 连接 GitHub API...',
        connectedToUser: (username: string) => `✅ 已连接到 GitHub 用户: ${username}`,
        checkingRepoExists: (name: string) => `🔍 检查 GitHub 仓库是否存在: ${name}...`,
        repoExists: (url: string) => `✅ 仓库已存在: ${url}`,
        remoteHasCommits: (count: number) => `⚠️ 远程仓库已有 ${count} 个提交`,
        remoteIsEmpty: 'ℹ️ 远程仓库为空',
        creatingRepo: (name: string, isPrivate: boolean) => `➕ 创建新仓库: ${name} (私有: ${isPrivate})...`,
        repoCreated: (url: string) => `✅ 仓库创建成功: ${url}`,
        
        // 远程配置日志
        configuringRemote: '🔗 配置远程仓库...',
        oldRemoteDeleted: '🔄 已删除旧的 origin 远程',
        remoteAdded: '✅ 已添加 origin 远程仓库',
        
        // 提交推送日志
        preparingCommit: '📤 准备提交和推送...',
        filesStaged: (count: number) => `📋 已暂存 ${count} 个文件`,
        initialCommitCreated: '✅ 已创建初始提交',
        initialCommitCreatedWithMsg: "✅ 已创建初始提交: 'Initial commit by TuTu's Code Ark'",
        noFilesToCommit: '⚠️ 没有文件需要提交',
        branchRenamed: '🔄 已重命名分支为 main',
        pushingToGithub: '🚀 正在推送到 GitHub...',
        pullingRemote: '🔄 远程仓库已存在，尝试拉取最新内容...',
        remoteMerged: '✅ 已合并远程内容',
        cannotMerge: '⚠️ 无法自动合并，将使用强制推送',
        remoteWillOverwrite: '⚠️ 远程内容将被本地覆盖',
        forcePushSuccess: '✅ 强制推送成功',
        fetchFailed: (error: string) => `ℹ️ 远程拉取失败，尝试直接推送: ${error}`,
        pushSuccess: '✅ 推送成功！代码已上传到 GitHub',
        normalPushFailed: '⚠️ 常规推送失败，尝试强制推送...',
        forcePushOverwrite: '✅ 强制推送成功（远程内容已被覆盖）',
        
        // 项目初始化日志
        startingInit: (name: string) => `[INIT] Starting project initialization: ${name}`,
        checkingToken: '[INIT] No token provided, checking global settings...',
        usingSavedToken: '[SUCCESS] Using saved GitHub token',
        step1: (path: string) => `[INIT] Step 1/5: Checking local path ${path}`,
        pathExists: (path: string) => `[SUCCESS] Path already exists: ${path}`,
        step2: '[INIT] Step 2/5: Checking if project already exists',
        noDuplicate: '[SUCCESS] No duplicate found, proceeding',
        step3: '[INIT] Step 3/5: Initializing Git repository and pushing to GitHub',
        gitInitComplete: (url: string) => `[SUCCESS] Git initialization complete, remote repo: ${url}`,
        step4: '[INIT] Step 4/5: Saving project info to database',
        savedToDb: (id: number) => `[SUCCESS] Project saved to database (ID: ${id})`,
        step5: '[INIT] Step 5/5: Starting file monitoring service',
        monitoringStarted: '[SUCCESS] File monitoring started, will auto-sync changes',
        initComplete: '[COMPLETE] Project initialization complete! Project is ready',
        startedWatching: (name: string) => `Started watching: ${name}`,
        
        // 同步日志
        syncDetected: (count: number) => `[SYNC] Detected ${count} file change(s), starting sync...`,
        syncComplete: '[SUCCESS] Sync complete: Push successful',
        statusUpdated: '[SUCCESS] Status updated to: idle',
        
        // 扫描日志
        scanStarting: (id: number) => `[SCAN] Starting security scan for project ${id}`,
        scanGettingStatus: (path: string) => `[SCAN] Getting Git status for ${path}`,
        scanFoundFiles: (count: number) => `[SCAN] Found ${count} changed file(s)`,
        scanPassed: '[SCAN] Security scan passed: no risks detected',
        scanFoundRisks: (count: number) => `[SCAN] Security scan found ${count} risky file(s)`,
        
        // 系统日志
        connectedToLogStream: 'Connected to log stream',
      },
      settings: {
        title: '项目配置',
        back: '返回',
        cancel: '取消',
        save: '保存配置',
        saving: '保存中...',
        saveSuccess: '配置已保存',
        saveFailed: '保存失败',
        
        projectInfo: {
          title: '项目信息',
        },
        
        visibility: {
          title: '仓库可见性',
          private: '私有',
          public: '公开',
          privateBtn: '🔒 私有',
          publicBtn: '🌍 公开',
          privateDesc: '仓库仅对您可见，需要授权才能访问',
          publicDesc: '仓库对所有人公开可见，任何人都可以克隆',
          currentStatus: '当前状态:',
          privateWithLabel: '🔒 Private (私有)',
          publicWithLabel: '🌍 Public (公开)',
          syncHint: '💡 更改后点击"保存"将同步到GitHub',
        },
        
        sync: {
          title: '同步策略',
          modeLabel: '同步模式',
          intervalLabel: '间隔时间 (分钟)',
          fixedLabel: '每天定时 (HH:MM)',
          autoPush: '启用自动推送',
          stripSecrets: '自动移除敏感信息',
        },
        
        advanced: {
          title: '高级设置',
          maxFileSize: '最大文件大小 (MB)',
          commitPrefix: 'Commit 前缀',
          ignoreHidden: '忽略隐藏文件',
          aiCommit: '使用 AI 生成提交信息',
        },
        
        gitignore: {
          title: '.gitignore 管理',
          edit: '编辑',
          description: '配置哪些文件和目录不被 Git 追踪',
          editorTitle: '.gitignore 编辑器',
          commonPatterns: '常用模式',
          fileContent: '文件内容',
          placeholder: '# 每行一个规则\nnode_modules/\n*.log\n.env',
          hint: '提示：每行一个规则，支持通配符（* 和 ?）',
          saveSuccess: '.gitignore 已保存',
        },
        
        danger: {
          title: '危险操作',
          deleteProject: '删除项目',
          confirmTitle: '确认删除',
          confirmMessage: '您确定要删除项目',
          deleteRemote: '同时删除 GitHub 远程仓库',
          deleteRemoteHint: '如果取消勾选，项目只会从图图的代码方舟列表中移除，GitHub 仓库将保留。',
          confirmDelete: '确认删除',
          tokenPrompt: '请输入 GitHub Token 以删除远程仓库（留空则只删除本地项目）:',
          tokenRequired: '需要 GitHub Token 才能删除远程仓库',
          deleteFailed: '删除失败',
          repoDeletedOnGithub: 'GitHub 仓库已被删除',
          repoDeletedMessage: 'GitHub 上的仓库 "{repo}" 已被删除。是否同时删除本地项目配置？',
          deleteLocalProject: '删除本地项目',
          keepProject: '保留项目',
        },
      },
    },
    en: {
      nav: {
        title: "TuTu's Code Ark",
        refresh: 'Refresh',
        addRepo: 'New Project',
        connect: 'Connect Folder',
      },
      dashboard: {
        title: 'Command Center',
        subtitle: 'Automated Git Hosting & Version Control System',
        noRepos: 'No Active Fleet',
        noReposSub: "Initialize your first fully managed project. TuTu's Code Ark handles Git init, remote creation, and push.",
        connectBtn: '🚀 Launch Project',
        branch: 'Branch',
        status: {
          idle: 'System Idle',
          watching: 'Monitoring',
          syncing: 'Syncing Data...',
          error: 'Connection Error',
        },
        scan: 'Security Scan',
        push: 'Push Now',
        settings: 'Config',
        terminalTitle: 'SYSTEM TERMINAL',
        visibility: {
          private: 'Private',
          public: 'Public',
        },
        syncMode: {
          auto: 'Auto Sync',
          interval: 'Interval',
          fixed: 'Scheduled',
        },
      },
      addModal: {
        title: 'Initialization Wizard',
        subtitle: {
          auto: 'Quick setup with full auto Git + GitHub hosting',
          manual: 'Connect existing Git project for monitoring'
        },
        tabs: {
            auto: '✨ Auto Managed (Rec)',
            manual: '🔗 Manual Link'
        },
        autoDesc: "For new projects. TuTu's Code Ark handles Git Init, GitHub Repo creation, and linking.",
        manualDesc: 'For existing Git projects. Local monitoring only.',
        
        pathLabel: 'Local Workspace Path',
        pathPlaceholder: 'e.g. D:\\Projects\\NewApp',
        browseFolder: 'Browse Folder',
        nameLabel: 'Project Codename',
        descriptionLabel: 'Repository Description (Optional)',
        descriptionPlaceholder: 'Brief description of this project...',
        tokenLabel: 'GitHub Access Token (PAT)',
        tokenPlaceholder: 'ghp_xxxxxxxxxxxx',
        tokenHelp: '❓ How to get Token?',
        privateLabel: 'Private Repository',
        
        gitignore: {
          title: '.gitignore Configuration',
          edit: 'Edit',
          description: '📝 Custom ignore rules (defaults included)',
          editorTitle: '.gitignore Editor',
          commonPatterns: 'Quick Add Common Rules',
          fileContent: 'File Content',
          placeholder: '# Files and directories to ignore\nnode_modules/\n__pycache__/\n*.log',
          hint: '💡 One rule per line, supports wildcards (* and ?)',
          close: 'Close',
          done: 'Done'
        },

        sync: {
          label: 'Sync Policy',
          mode: {
              auto: '⚡ Auto Sync (Realtime)',
              interval: '⏱️ Interval Sync',
              fixed: '📅 Scheduled Sync'
          },
          intervalLabel: 'Interval (Minutes)',
          fixedLabel: 'Daily Schedule (HH:MM)',
          autoDesc: 'Push automatically on change (10s debounce)',
        },
        
        guideTitle: 'How to get GitHub Token?',
        guideStep1: '1. Click button below to open GitHub',
        guideStep2: '2. Click "Generate new token (classic)"',
        guideStep3: '3. Check "repo" and "workflow" scopes',
        guideStep4: '4. Copy the token and paste it here',
        openGithub: 'Open GitHub Settings ↗',
        
        helpDialog: {
          title: '📘 GitHub Token Guide',
          step1Title: 'Step 1: Visit GitHub Settings',
          step1Desc: 'Click the button below, or manually: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)',
          step2Title: 'Step 2: Generate New Token',
          step2Desc: "Click \"Generate new token (classic)\". Give it a name like \"TuTu's Code Ark Auto Backup\".",
          step3Title: 'Step 3: Select Permissions',
          step3Desc: 'Required scopes:',
          step3Items: ['✓ repo — Full repository control', '✓ workflow — GitHub Actions permissions'],
          step4Title: 'Step 4: Generate & Copy',
          step4Desc: 'Click "Generate token" at the bottom. Copy the generated token (starts with ghp_) and paste it into the input field.',
          warning: "⚠️ Security Note: Token is shown only once. TuTu's Code Ark stores it locally and never uploads it.",
          openBtn: 'Go to GitHub Now',
          closeBtn: 'Got it'
        },
        
        cancel: 'Cancel',
        confirm: '🚀 Initialize Now',
        manualConfirm: '📂 Add Project',
        error: 'Operation failed: ',
        processing: 'Initializing Environment...',
        browseFailure: 'Folder selection only available in Tauri environment. Please enter path manually.',
        confirmBtn: 'OK'
      },
      tokenDialog: {
        title: 'GitHub Token Configuration',
        subtitle: 'Configure once, use globally',
        tokenConfigured: '✓ Token Configured',
        clearToken: 'Clear',
        notConfigured: '⚠️ GitHub Token Not Configured',
        notConfiguredDesc: 'Configure to auto-create GitHub repositories',
        tokenLabel: 'GitHub Personal Access Token',
        tokenPlaceholder: 'ghp_xxxxxxxxxxxx',
        tokenHelp: '❓ How to get Token?',
        securityNote: 'Security Note:',
        securityDesc: "Token is encrypted and stored locally for auto-creating GitHub repos. TuTu's Code Ark never uploads your token to any server.",
        cancel: 'Cancel',
        save: '💾 Save Config',
        saving: 'Saving...',
        
        helpDialog: {
          title: '📘 GitHub Token Guide',
          step1Title: 'Step 1: Visit GitHub Settings',
          step1Desc: 'Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)',
          step2Title: 'Step 2: Generate New Token',
          step2Desc: 'Click "Generate new token (classic)", name it like "TuTu\'s Code Ark"',
          step3Title: 'Step 3: Select Permissions',
          repoPermission: '— Full repository control',
          workflowPermission: '— GitHub Actions permissions',
          step4Title: 'Step 4: Copy Token',
          step4Desc: 'Copy immediately (starts with ghp_), paste into config box',
          warning: '⚠️ Token is shown only once, keep it safe!',
          openBtn: '🔗 Go to GitHub Now',
          closeBtn: 'Close'
        },
        
        errorMsg: {
          emptyToken: 'Please enter GitHub Token',
          saveFailed: 'Save failed, please retry',
          clearFailed: 'Clear failed: ',
          browserBlocked: 'Cannot auto-open browser.\n\nCopy URL to clipboard?',
          urlCopied: 'URL copied to clipboard!\n\nPaste into browser address bar.',
          copyPrompt: 'Please copy this URL:',
          copyManual: 'Please copy this URL and open in browser:'
        },
        
        successMsg: {
          tokenSaved: 'GitHub Token saved successfully!',
          tokenCleared: 'Token cleared'
        },
        
        confirmDialog: {
          title: 'Confirm Action',
          message: 'Are you sure you want to clear the saved GitHub Token?',
          cancel: 'Cancel',
          confirm: 'Confirm'
        },
        
        dialogButtons: {
          success: 'Success',
          error: 'Error',
          confirm: 'OK'
        }
      },
      wizard: {
        steps: {
          initGit: 'Initializing Git repository...',
          createRepo: 'Creating GitHub repository...',
          linkRemote: 'Linking remote repository...',
          firstCommit: 'Committing initial files...',
          scanning: 'Scanning local repository...',
          analyzing: 'Analyzing Git history...',
          configuring: 'Configuring monitoring strategy...',
          complete: 'Complete!'
        }
      },
      riskDialog: {
        title: '⚠️ Security Policy Alert',
        desc: 'Files violated backup policy (size limit or blocked type).',
        ignore: 'Add to Ignore List',
        cancel: 'Cancel',
        safeMsg: '✅ Scan passed. Safe to sync.',
      },
      log: {
        // Git initialization logs
        initLocalRepo: '📦 Initializing local Git repository...',
        localRepoExists: '✅ Local repository already exists',
        newRepoCreated: '✅ New Git repository created',
        checkGitignore: '📝 Checking .gitignore file...',
        gitignoreCreated: '✅ .gitignore file created',
        gitignoreExists: '✅ .gitignore file already exists',
        
        // GitHub connection logs
        connectingGithub: '🌐 Connecting to GitHub API...',
        connectedToUser: (username: string) => `✅ Connected to GitHub user: ${username}`,
        checkingRepoExists: (name: string) => `🔍 Checking if GitHub repository exists: ${name}...`,
        repoExists: (url: string) => `✅ Repository exists: ${url}`,
        remoteHasCommits: (count: number) => `⚠️ Remote repository has ${count} commit(s)`,
        remoteIsEmpty: 'ℹ️ Remote repository is empty',
        creatingRepo: (name: string, isPrivate: boolean) => `➕ Creating new repository: ${name} (private: ${isPrivate})...`,
        repoCreated: (url: string) => `✅ Repository created successfully: ${url}`,
        
        // Remote configuration logs
        configuringRemote: '🔗 Configuring remote repository...',
        oldRemoteDeleted: '🔄 Old origin remote deleted',
        remoteAdded: '✅ Origin remote added',
        
        // Commit & push logs
        preparingCommit: '📤 Preparing to commit and push...',
        filesStaged: (count: number) => `📋 Staged ${count} file(s)`,
        initialCommitCreated: '✅ Initial commit created',
        initialCommitCreatedWithMsg: "✅ Initial commit created: 'Initial commit by TuTu's Code Ark'",
        noFilesToCommit: '⚠️ No files to commit',
        branchRenamed: '🔄 Branch renamed to main',
        pushingToGithub: '🚀 Pushing to GitHub...',
        pullingRemote: '🔄 Remote repository exists, pulling latest content...',
        remoteMerged: '✅ Remote content merged',
        cannotMerge: '⚠️ Cannot auto-merge, will force push',
        remoteWillOverwrite: '⚠️ Remote content will be overwritten',
        forcePushSuccess: '✅ Force push successful',
        fetchFailed: (error: string) => `ℹ️ Remote fetch failed, trying direct push: ${error}`,
        pushSuccess: '✅ Push successful! Code uploaded to GitHub',
        normalPushFailed: '⚠️ Normal push failed, trying force push...',
        forcePushOverwrite: '✅ Force push successful (remote content overwritten)',
        
        // Project initialization logs
        startingInit: (name: string) => `[INIT] Starting project initialization: ${name}`,
        checkingToken: '[INIT] No token provided, checking global settings...',
        usingSavedToken: '[SUCCESS] Using saved GitHub token',
        step1: (path: string) => `[INIT] Step 1/5: Checking local path ${path}`,
        pathExists: (path: string) => `[SUCCESS] Path already exists: ${path}`,
        step2: '[INIT] Step 2/5: Checking if project already exists',
        noDuplicate: '[SUCCESS] No duplicate found, proceeding',
        step3: '[INIT] Step 3/5: Initializing Git repository and pushing to GitHub',
        gitInitComplete: (url: string) => `[SUCCESS] Git initialization complete, remote repo: ${url}`,
        step4: '[INIT] Step 4/5: Saving project info to database',
        savedToDb: (id: number) => `[SUCCESS] Project saved to database (ID: ${id})`,
        step5: '[INIT] Step 5/5: Starting file monitoring service',
        monitoringStarted: '[SUCCESS] File monitoring started, will auto-sync changes',
        initComplete: '[COMPLETE] Project initialization complete! Project is ready',
        startedWatching: (name: string) => `Started watching: ${name}`,
        
        // Sync logs
        syncDetected: (count: number) => `[SYNC] Detected ${count} file change(s), starting sync...`,
        syncComplete: '[SUCCESS] Sync complete: Push successful',
        statusUpdated: '[SUCCESS] Status updated to: idle',
        
        // Scan logs
        scanStarting: (id: number) => `[SCAN] Starting security scan for project ${id}`,
        scanGettingStatus: (path: string) => `[SCAN] Getting Git status for ${path}`,
        scanFoundFiles: (count: number) => `[SCAN] Found ${count} changed file(s)`,
        scanPassed: '[SCAN] Security scan passed: no risks detected',
        scanFoundRisks: (count: number) => `[SCAN] Security scan found ${count} risky file(s)`,
        
        // System logs
        connectedToLogStream: 'Connected to log stream',
      },
      settings: {
        title: 'Project Settings',
        back: 'Back',
        cancel: 'Cancel',
        save: 'Save Config',
        saving: 'Saving...',
        saveSuccess: 'Configuration saved',
        saveFailed: 'Save failed',
        
        projectInfo: {
          title: 'Project Information',
        },
        
        visibility: {
          title: 'Repository Visibility',
          private: 'Private',
          public: 'Public',
          privateBtn: '🔒 Private',
          publicBtn: '🌍 Public',
          privateDesc: 'Repository is only visible to you, requires authorization',
          publicDesc: 'Repository is publicly visible, anyone can clone',
          currentStatus: 'Current Status:',
          privateWithLabel: '🔒 Private',
          publicWithLabel: '🌍 Public',
          syncHint: '💡 After changes, click "Save" to sync to GitHub',
        },
        
        sync: {
          title: 'Sync Policy',
          modeLabel: 'Sync Mode',
          intervalLabel: 'Interval (Minutes)',
          fixedLabel: 'Daily Schedule (HH:MM)',
          autoPush: 'Enable Auto Push',
          stripSecrets: 'Auto Strip Secrets',
        },
        
        advanced: {
          title: 'Advanced Settings',
          maxFileSize: 'Max File Size (MB)',
          commitPrefix: 'Commit Prefix',
          ignoreHidden: 'Ignore Hidden Files',
          aiCommit: 'Use AI for Commit Messages',
        },
        
        gitignore: {
          title: '.gitignore Manager',
          edit: 'Edit',
          description: 'Configure which files and directories to ignore',
          editorTitle: '.gitignore Editor',
          commonPatterns: 'Common Patterns',
          fileContent: 'File Content',
          placeholder: '# One rule per line\nnode_modules/\n*.log\n.env',
          hint: 'Tip: One rule per line, supports wildcards (* and ?)',
          saveSuccess: '.gitignore saved',
        },
        
        danger: {
          title: 'Danger Zone',
          deleteProject: 'Delete Project',
          confirmTitle: 'Confirm Deletion',
          confirmMessage: 'Are you sure you want to delete project',
          deleteRemote: 'Also delete GitHub remote repository',
          deleteRemoteHint: "If unchecked, project will only be removed from TuTu's Code Ark, GitHub repo will remain.",
          confirmDelete: 'Confirm Delete',
          tokenPrompt: 'Enter GitHub Token to delete remote repository (leave empty to only delete local):',
          tokenRequired: 'GitHub Token required to delete remote repository',
          deleteFailed: 'Delete failed',
          repoDeletedOnGithub: 'GitHub Repository Deleted',
          repoDeletedMessage: 'The repository "{repo}" has been deleted on GitHub. Would you like to also delete the local project configuration?',
          deleteLocalProject: 'Delete Local Project',
          keepProject: 'Keep Project',
        },
      },
    },
  };

  const t = computed(() => messages[currentLocale.value]);

  return { currentLocale, toggleLocale, t };
});
