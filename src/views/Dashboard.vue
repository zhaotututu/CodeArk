<script setup lang="ts">
import { ref, onMounted, watch, inject } from 'vue';
import { useProjectStore } from '../stores/projects';
import { useLogStore } from '../stores/logs';
import { useLocaleStore } from '../stores/locale';
import Card from '../components/ui/Card.vue';
import Button from '../components/ui/Button.vue';
import ProjectInitWizard from '../components/ProjectInitWizard.vue';
import SettingsDialog from '../components/SettingsDialog.vue';
import { storeToRefs } from 'pinia';

const projectStore = useProjectStore();
const logStore = useLogStore();
const localeStore = useLocaleStore();
const { projects } = storeToRefs(projectStore);
const { logs } = storeToRefs(logStore);
const { t, currentLocale } = storeToRefs(localeStore);

const showAddModal = ref(false);
const showSettingsDialog = ref(false);
const showRiskAlert = ref(false);
const showSafeAlert = ref(false);
const showErrorDialog = ref(false);
const errorMessage = ref('');
const riskyFiles = ref<any[]>([]);
const currentScanId = ref<number | null>(null);
const showTokenHelp = ref(false);

onMounted(async () => {
  logStore.connect();
  await projectStore.fetchProjects();
});

const handleWizardSuccess = async () => {
  await projectStore.fetchProjects();
};

const handleManualScan = async (id: number) => {
    try {
        const res = await projectStore.scanProject(id, currentLocale.value);
        
        // 检查响应格式
        if (!res || typeof res !== 'object') {
            errorMessage.value = currentLocale.value === 'zh' 
                ? '扫描失败：服务器响应无效' 
                : 'Scan failed: Invalid server response';
            showErrorDialog.value = true;
            console.error('[SCAN] Invalid response:', res);
            return;
        }
        
        // 如果有错误信息
        if (res.error || res.detail) {
            errorMessage.value = currentLocale.value === 'zh'
                ? `扫描失败：${res.error || res.detail}`
                : `Scan failed: ${res.error || res.detail}`;
            showErrorDialog.value = true;
            console.error('[SCAN] Error:', res.error || res.detail);
            return;
        }
        
        // 检查是否有风险
        if (!res.safe) {
            riskyFiles.value = res.risks;
            currentScanId.value = id;
            showRiskAlert.value = true;
        } else {
            showSafeAlert.value = true;
        }
    } catch (error) {
        console.error('[SCAN] Failed to scan project:', error);
        errorMessage.value = currentLocale.value === 'zh'
            ? '扫描失败：无法连接到后端服务。请确保后端服务已启动。'
            : 'Scan failed: Cannot connect to backend service. Please ensure the backend is running.';
        showErrorDialog.value = true;
    }
};

const handleManualPush = async (id: number) => {
    try {
        const res = await projectStore.manualPush(id, currentLocale.value);
        
        if (res.pushed) {
            showSafeAlert.value = true;
            await projectStore.fetchProjects(); // 刷新项目列表以更新状态
        } else {
            errorMessage.value = currentLocale.value === 'zh'
                ? '暂无变更需要推送'
                : 'No changes to push';
            showErrorDialog.value = true;
        }
    } catch (error: any) {
        console.error('[PUSH] Failed to push project:', error);
        errorMessage.value = currentLocale.value === 'zh'
            ? `推送失败：${error.message || '未知错误'}`
            : `Push failed: ${error.message || 'Unknown error'}`;
        showErrorDialog.value = true;
    }
};

const ignoreFile = async (file: any) => {
    if (currentScanId.value) {
        await projectStore.ignoreFiles(currentScanId.value, [file.path]);
        riskyFiles.value = riskyFiles.value.filter(f => f.path !== file.path);
        if (riskyFiles.value.length === 0) showRiskAlert.value = false;
    }
};

const openGithubSettings = async () => {
  const url = 'https://github.com/settings/tokens/new?scopes=repo,workflow,delete_repo&description=TuTu-Code-Ark+Auto+Token';

  try {
    const tauriApi = await import('@tauri-apps/api/core').catch(() => null);
    if (tauriApi && typeof tauriApi.invoke === 'function') {
      await tauriApi.invoke('open_external', { url });
      return;
    }
  } catch (importError) {
    // Silently fallback to window.open
  }

  try {
    const newWindow = window.open(url, '_blank', 'noopener,noreferrer');

    if (!newWindow) {
      const userConfirmed = confirm(`无法自动打开浏览器。\n\n是否复制 URL 到剪贴板？`);

      if (userConfirmed) {
        try {
          await navigator.clipboard.writeText(url);
          alert('✅ URL 已复制到剪贴板！\n\n请粘贴到浏览器地址栏打开。');
        } catch (clipError) {
          prompt('请复制以下 URL：', url);
        }
      }
    }
  } catch (e) {
    console.error('Failed to open URL:', e);
    prompt('请复制以下 URL 并在浏览器中打开：', url);
  }
};

const browseFolder = async (tab: 'auto' | 'manual') => {
    try {
        // @ts-ignore - Tauri API may not be available in all environments
        const { invoke } = await import('@tauri-apps/api/core');
        const selectedPath = await invoke('select_folder');
        
        if (selectedPath) {
            if (tab === 'auto') {
                formAuto.value.path = selectedPath as string;
            } else {
                formManual.value.path = selectedPath as string;
            }
        }
    } catch (error) {
        console.error('Failed to open folder dialog:', error);
        // Fallback: Show alert if Tauri is not available
        alert('文件夹选择功能仅在 Tauri 环境中可用。请手动输入路径。');
    }
}

// Get inject functions at setup time
const showSettings = inject<((id: number) => void)>('showSettings');

const handleOpenSettings = (projectId: number) => {
    if (showSettings) {
        showSettings(projectId);
    }
}
</script>

<template>
  <div class="h-screen flex flex-col bg-black text-white font-sans overflow-hidden relative">
    
    <!-- Space Background -->
    <div class="space-grid fixed inset-0"></div>
    <div class="fixed inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/80 pointer-events-none z-0"></div>

    <!-- Navbar -->
    <nav class="border-b border-white/5 bg-black/40 backdrop-blur-md flex-none z-50">
      <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <img src="/logo.png" alt="图图的代码方舟" class="h-8 w-auto object-contain" />
          <span class="font-bold text-lg tracking-wide uppercase text-white/90">{{ t.nav.title }}</span>
        </div>
        <div class="flex items-center gap-3">
          <Button variant="ghost" size="sm" class="font-mono text-xs text-zinc-400 hover:text-white border border-white/5 hover:bg-white/5" @click="localeStore.toggleLocale()">
            {{ currentLocale === 'zh' ? 'EN' : '中' }}
          </Button>
          
          <!-- Refresh Button with Icon -->
          <Button variant="ghost" size="sm" class="text-zinc-400 hover:text-white hover:bg-white/5" @click="projectStore.fetchProjects()" :title="t.nav.refresh">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </Button>
          
          <!-- GitHub Token Settings Button -->
          <Button variant="ghost" size="sm" class="text-zinc-400 hover:text-white hover:bg-white/5" @click="showSettingsDialog = true" :title="currentLocale === 'zh' ? '配置GitHub Token' : 'Configure GitHub Token'">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </Button>
          
          <!-- Add New Project Button with Icon -->
          <Button v-if="projects.length > 0" variant="ghost" size="sm" class="text-zinc-400 hover:text-white hover:bg-white/5" @click="showAddModal = true" :title="t.nav.addRepo">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </Button>
        </div>
      </div>
    </nav>

    <main class="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-hidden z-10">
      
      <!-- Project Grid (Left 2 cols) -->
      <div class="lg:col-span-2 flex flex-col min-h-0">
        <div class="flex items-center justify-between mb-6 flex-none">
             <div>
                <h2 class="text-2xl font-bold text-white tracking-tight">{{ t.dashboard.title }}</h2>
                <p class="text-xs text-zinc-500 uppercase tracking-widest mt-1">{{ t.dashboard.subtitle }}</p>
             </div>
             <div class="h-px flex-1 bg-gradient-to-r from-purple-500/50 to-transparent ml-6"></div>
        </div>
        
        <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar relative">
          <!-- Empty State / Launchpad -->
          <div v-if="projects.length === 0" class="absolute inset-0 flex items-center justify-center pb-20">
             <div class="text-center max-w-md p-8 rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm flex flex-col items-center">
                 <div class="w-16 h-16 rounded-full bg-zinc-900 flex items-center justify-center mb-4 border border-white/10 shadow-[0_0_30px_rgba(100,100,100,0.1)]">
                    <span class="text-3xl">🛸</span>
                 </div>
                 <h3 class="text-xl font-bold text-white mb-2">{{ t.dashboard.noRepos }}</h3>
                 <p class="text-zinc-400 text-sm mb-6 leading-relaxed">{{ t.dashboard.noReposSub }}</p>
                 <Button class="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white px-8 py-6 text-lg shadow-[0_0_30px_rgba(124,58,237,0.4)] border-none transition-all hover:scale-105" @click="showAddModal = true">
                    {{ t.dashboard.connectBtn }}
                 </Button>
             </div>
          </div>

          <!-- Project List -->
          <div v-else class="grid grid-cols-1 gap-4 pb-4">
            <Card v-for="project in projects" :key="project.id" class="bg-zinc-900/40 backdrop-blur-md border-white/5 hover:border-purple-500/30 transition-all group relative overflow-hidden">
               <!-- Status Indicator Line -->
               <div class="absolute left-0 top-0 bottom-0 w-1"
                    :class="{
                        'bg-green-500': project.status === 'idle',
                        'bg-blue-500': project.status === 'watching',
                        'bg-yellow-500': project.status === 'syncing',
                        'bg-red-500': project.status === 'error',
                    }"></div>

               <div class="p-5 pl-6 relative z-10">
                  <div class="flex justify-between items-start mb-2">
                      <div class="flex-1">
                          <div class="flex items-center gap-2 mb-1">
                              <h3 class="font-bold text-lg text-zinc-100 tracking-tight group-hover:text-purple-300 transition-colors">{{ project.name }}</h3>
                              
                              <!-- Visibility Icon -->
                              <div 
                                  class="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono transition-all"
                                  :class="project.config?.is_private ? 'bg-purple-500/10 text-purple-400' : 'bg-green-500/10 text-green-400'"
                                  :title="project.config?.is_private ? t.dashboard.visibility.private : t.dashboard.visibility.public"
                              >
                                  <svg v-if="project.config?.is_private" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                      <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
                                  </svg>
                                  <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                                      <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd" />
                                  </svg>
                              </div>
                              
                              <!-- Sync Mode Icon -->
                              <div 
                                  class="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-400 transition-all"
                                  :title="
                                      project.config?.sync_mode === 'auto' ? t.dashboard.syncMode.auto :
                                      project.config?.sync_mode === 'interval' ? t.dashboard.syncMode.interval :
                                      t.dashboard.syncMode.fixed
                                  "
                              >
                                  <!-- Auto Sync Icon -->
                                  <svg v-if="project.config?.sync_mode === 'auto'" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                      <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd" />
                                  </svg>
                                  <!-- Interval Sync Icon -->
                                  <svg v-else-if="project.config?.sync_mode === 'interval'" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
                                  </svg>
                                  <!-- Fixed Time Sync Icon -->
                                  <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                      <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
                                  </svg>
                              </div>
                          </div>
                          <p class="text-xs text-zinc-500 font-mono">{{ project.path }}</p>
                      </div>
                      <div class="flex flex-col items-end">
                          <span class="text-[10px] uppercase font-bold tracking-wider text-zinc-500">
                             STATUS: 
                             <span :class="{
                                'text-green-400': project.status === 'idle',
                                'text-blue-400': project.status === 'watching',
                                'text-yellow-400': project.status === 'syncing',
                                'text-red-400': project.status === 'error',
                             }">{{ 
                                  project.status === 'idle' ? t.dashboard.status.idle : 
                                  project.status === 'watching' ? t.dashboard.status.watching : 
                                  project.status === 'syncing' ? t.dashboard.status.syncing : 
                                  t.dashboard.status.error
                              }}</span>
                          </span>
                      </div>
                  </div>
                  
                  <div class="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
                       <div class="text-xs text-zinc-500 flex items-center gap-2">
                           <span class="w-2 h-2 rounded-full bg-zinc-700"></span>
                           {{ project.branch }}
                       </div>
                       <div class="flex gap-2">
                           <!-- 安全扫描按钮 -->
                           <Button 
                               variant="ghost" 
                               size="sm" 
                               class="h-8 w-8 p-0 text-zinc-400 hover:text-white hover:bg-white/10" 
                               @click="handleManualScan(project.id)"
                               :title="t.dashboard.scan"
                           >
                               <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                               </svg>
                           </Button>
                           
                           <!-- 立即推送按钮 -->
                           <Button 
                               variant="ghost" 
                               size="sm" 
                               class="h-8 w-8 p-0 text-zinc-400 hover:text-white hover:bg-white/10" 
                               @click="handleManualPush(project.id)"
                               :title="t.dashboard.push"
                           >
                               <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                               </svg>
                           </Button>
                           
                           <!-- 设置按钮 -->
                           <Button 
                               variant="ghost" 
                               size="sm" 
                               class="h-8 w-8 p-0 text-zinc-400 hover:text-white hover:bg-white/10" 
                               @click="handleOpenSettings(project.id)"
                               :title="t.dashboard.settings"
                           >
                               <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                               </svg>
                           </Button>
                       </div>
                  </div>
               </div>
            </Card>
          </div>
        </div>
      </div>

      <!-- Live Terminal (Right col) -->
      <div class="lg:col-span-1 flex flex-col min-h-0">
        <div class="flex items-center justify-between mb-6 flex-none">
             <h2 class="text-sm font-mono text-zinc-500 uppercase tracking-widest">{{ t.dashboard.terminalTitle }}</h2>
             <div class="flex gap-1.5">
                <div class="w-1.5 h-1.5 rounded-full bg-zinc-600"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-zinc-600"></div>
             </div>
        </div>

        <Card class="flex-1 bg-black/80 backdrop-blur border-zinc-800 flex flex-col overflow-hidden shadow-2xl">
          <div class="flex-1 p-4 overflow-y-auto font-mono text-xs space-y-2 custom-scrollbar">
            <div v-for="(log, i) in logs" :key="i" class="break-all opacity-80 hover:opacity-100 transition-opacity">
                <span class="text-zinc-600 mr-2">{{ log.time }}</span>
                <span :class="{
                    'text-green-400': log.level === 'success',
                    'text-red-400': log.level === 'error',
                    'text-blue-400': log.level === 'info',
                    'text-zinc-300': !log.level
                }">{{ log.msg }}</span>
            </div>
             <!-- Blinking Cursor -->
             <div class="animate-pulse text-purple-500 mt-2">_</div>
          </div>
        </Card>
      </div>
    </main>

    <!-- Project Init Wizard Component -->
    <ProjectInitWizard 
      v-if="showAddModal" 
      @close="showAddModal = false" 
      @success="handleWizardSuccess"
    />

    <!-- Settings Dialog -->
    <SettingsDialog
      v-if="showSettingsDialog"
      @close="showSettingsDialog = false"
      @success="showSettingsDialog = false"
    />

    <!-- Risk Alert Dialog -->
    <div v-if="showRiskAlert" class="fixed inset-0 bg-red-900/20 backdrop-blur-md z-[60] flex items-center justify-center p-4">
        <Card class="w-full max-w-lg bg-zinc-950 border-red-500/50 p-0 overflow-hidden shadow-[0_0_50px_rgba(220,38,38,0.2)]">
            <div class="p-6 border-b border-red-500/20 bg-red-500/5">
                <h3 class="text-xl font-bold text-red-500 flex items-center gap-2">
                    {{ t.riskDialog.title }}
                </h3>
                <p class="text-zinc-400 text-sm mt-1">{{ t.riskDialog.desc }}</p>
            </div>
            <div class="p-6 max-h-[300px] overflow-y-auto custom-scrollbar">
                <div v-for="file in riskyFiles" :key="file.path" class="flex items-center justify-between p-3 mb-2 rounded border border-zinc-800 bg-zinc-900/50">
                    <div>
                        <p class="text-sm font-mono text-zinc-200">{{ file.path }}</p>
                        <p class="text-xs text-red-400">{{ file.reason }} ({{ file.size_display }})</p>
                    </div>
                    <Button size="sm" variant="secondary" class="h-6 text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300" @click="ignoreFile(file)">{{ t.riskDialog.ignore }}</Button>
                </div>
            </div>
            <div class="p-4 bg-zinc-900/50 border-t border-zinc-800 flex justify-end gap-3">
                <Button variant="ghost" class="text-zinc-300 hover:text-white hover:bg-white/10" @click="showRiskAlert = false">{{ t.riskDialog.cancel }}</Button>
            </div>
        </Card>
    </div>

    <!-- Safe Alert Dialog -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 scale-90"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-90"
    >
      <div v-if="showSafeAlert" class="fixed inset-0 bg-green-900/20 backdrop-blur-md z-[60] flex items-center justify-center p-4">
          <Card class="w-full max-w-md bg-zinc-950 border-green-500/50 p-0 overflow-hidden shadow-[0_0_50px_rgba(34,197,94,0.3)]">
              <div class="p-8 flex flex-col items-center text-center">
                  <!-- Success Icon with Animation -->
                  <div class="w-20 h-20 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mb-5 shadow-[0_0_40px_rgba(34,197,94,0.4)] animate-pulse">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                      </svg>
                  </div>
                  
                  <!-- Title -->
                  <h3 class="text-2xl font-bold text-green-400 mb-3">
                      {{ currentLocale === 'zh' ? '扫描通过' : 'Scan Passed' }}
                  </h3>
                  
                  <!-- Message -->
                  <p class="text-zinc-300 text-base mb-6 leading-relaxed">
                      {{ currentLocale === 'zh' ? '所有文件均已通过安全检查，未发现风险内容。' : 'All files passed security check. No risks detected.' }}
                  </p>
                  
                  <!-- Decorative Line -->
                  <div class="w-full h-px bg-gradient-to-r from-transparent via-green-500/50 to-transparent mb-6"></div>
                  
                  <!-- Confirm Button -->
                  <Button
                      @click="showSafeAlert = false"
                      class="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-semibold py-3 px-8 shadow-[0_0_30px_rgba(34,197,94,0.3)] border-none transition-all hover:scale-105"
                  >
                      {{ currentLocale === 'zh' ? '确定' : 'OK' }}
                  </Button>
              </div>
          </Card>
      </div>
    </Transition>

    <!-- Error Dialog -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 scale-90"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-90"
    >
      <div v-if="showErrorDialog" class="fixed inset-0 bg-red-900/20 backdrop-blur-md z-[60] flex items-center justify-center p-4">
          <Card class="w-full max-w-md bg-zinc-950 border-red-500/50 p-0 overflow-hidden shadow-[0_0_50px_rgba(239,68,68,0.3)]">
              <div class="p-8 flex flex-col items-center text-center">
                  <!-- Error Icon with Animation -->
                  <div class="w-20 h-20 rounded-full bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center mb-5 shadow-[0_0_40px_rgba(239,68,68,0.4)] animate-pulse">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                      </svg>
                  </div>
                  
                  <!-- Title -->
                  <h3 class="text-2xl font-bold text-red-400 mb-3">
                      {{ currentLocale === 'zh' ? '操作失败' : 'Operation Failed' }}
                  </h3>
                  
                  <!-- Error Message -->
                  <div class="w-full p-4 bg-red-500/10 border border-red-500/30 rounded-lg mb-6">
                      <p class="text-zinc-200 text-sm break-words text-left">
                          {{ errorMessage }}
                      </p>
                  </div>
                  
                  <!-- Decorative Line -->
                  <div class="w-full h-px bg-gradient-to-r from-transparent via-red-500/50 to-transparent mb-6"></div>
                  
                  <!-- Confirm Button -->
                  <Button
                      @click="showErrorDialog = false"
                      class="w-full bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-semibold py-3 px-8 shadow-[0_0_30px_rgba(239,68,68,0.3)] border-none transition-all hover:scale-105"
                  >
                      {{ currentLocale === 'zh' ? '确定' : 'OK' }}
                  </Button>
              </div>
          </Card>
      </div>
    </Transition>

    <!-- Token Help Dialog -->
    <div v-if="showTokenHelp" class="fixed inset-0 bg-black/90 backdrop-blur-md z-[70] flex items-center justify-center p-6">
        <div class="w-full max-w-2xl bg-zinc-950 border border-blue-500/30 rounded-xl p-0 overflow-hidden shadow-[0_0_50px_rgba(59,130,246,0.2)] flex flex-col max-h-[85vh]">
            <div class="p-5 border-b border-blue-500/20 bg-blue-500/5 flex-none">
                <h3 class="text-xl font-bold text-blue-400 flex items-center gap-2">
                    {{ t.addModal.helpDialog.title }}
                </h3>
            </div>
            
            <div class="p-6 space-y-3 flex-1">
                <!-- Step 1 -->
                <div class="space-y-1">
                    <h4 class="font-bold text-white text-sm flex items-center gap-2">
                        <span class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-[10px] flex-shrink-0">1</span>
                        {{ t.addModal.helpDialog.step1Title }}
                    </h4>
                    <p class="text-xs text-zinc-400 leading-snug pl-7">{{ t.addModal.helpDialog.step1Desc }}</p>
                </div>

                <!-- Step 2 -->
                <div class="space-y-1">
                    <h4 class="font-bold text-white text-sm flex items-center gap-2">
                        <span class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-[10px] flex-shrink-0">2</span>
                        {{ t.addModal.helpDialog.step2Title }}
                    </h4>
                    <p class="text-xs text-zinc-400 leading-snug pl-7">{{ t.addModal.helpDialog.step2Desc }}</p>
                </div>

                <!-- Step 3 -->
                <div class="space-y-1">
                    <h4 class="font-bold text-white text-sm flex items-center gap-2">
                        <span class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-[10px] flex-shrink-0">3</span>
                        {{ t.addModal.helpDialog.step3Title }}
                    </h4>
                    <p class="text-xs text-zinc-400 leading-snug pl-7 mb-1">{{ t.addModal.helpDialog.step3Desc }}</p>
                    <ul class="pl-7 space-y-0.5">
                        <li v-for="(item, i) in t.addModal.helpDialog.step3Items" :key="i" class="text-[11px] text-green-400">{{ item }}</li>
                    </ul>
                </div>

                <!-- Step 4 -->
                <div class="space-y-1">
                    <h4 class="font-bold text-white text-sm flex items-center gap-2">
                        <span class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-[10px] flex-shrink-0">4</span>
                        {{ t.addModal.helpDialog.step4Title }}
                    </h4>
                    <p class="text-xs text-zinc-400 leading-snug pl-7">{{ t.addModal.helpDialog.step4Desc }}</p>
                </div>

                <!-- Warning Box -->
                <div class="bg-yellow-500/10 border border-yellow-500/30 rounded p-3 mt-2">
                    <p class="text-[11px] text-yellow-200 leading-snug">{{ t.addModal.helpDialog.warning }}</p>
                </div>
            </div>
            
            <div class="p-5 bg-zinc-900/50 border-t border-zinc-800 flex justify-between gap-3 flex-none">
                <Button 
                    class="bg-blue-600 hover:bg-blue-500 text-white px-6 transition-all shadow-lg shadow-blue-900/30 border-none"
                    @click="openGithubSettings"
                >
                    {{ t.addModal.helpDialog.openBtn }}
                </Button>
                <Button variant="ghost" class="text-zinc-300 hover:text-white hover:bg-white/10" @click="showTokenHelp = false">
                    {{ t.addModal.helpDialog.closeBtn }}
                </Button>
            </div>
        </div>
    </div>

  </div>
</template>

<style>
/* Scrollbar styling */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
