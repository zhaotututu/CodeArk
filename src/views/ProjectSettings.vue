<script setup lang="ts">
import { ref, onMounted, computed, inject } from 'vue';
import { useProjectStore } from '../stores/projects';
import { useLocaleStore } from '../stores/locale';
import Card from '../components/ui/Card.vue';
import Button from '../components/ui/Button.vue';
import type { ProjectConfig } from '../stores/projects';
import { storeToRefs } from 'pinia';

interface Props {
    projectId: number | null;
}

const props = defineProps<Props>();
const showDashboard = inject<() => void>('showDashboard');

const projectStore = useProjectStore();
const localeStore = useLocaleStore();
const { t } = storeToRefs(localeStore);
const project = computed(() => props.projectId ? projectStore.projects.find(p => p.id === props.projectId) : null);

const config = ref<ProjectConfig>({
    auto_push: true,
    sync_mode: 'interval',
    sync_interval: 300,
    sync_fixed_time: '00:00',
    max_file_size_mb: 50,
    blocked_extensions: ['.exe', '.dll', '.zip', '.mp4'],
    ignore_hidden: true,
    ai_commit_message: false,
    default_commit_prefix: 'backup: ',
    is_private: true,
    strip_secrets: true
});

const isSaving = ref(false);
const showDeleteConfirm = ref(false);
const showRepoDeletedDialog = ref(false);
const deletedRepoName = ref('');
const mousePosition = ref({ x: 0, y: 0 });
const gitignoreContent = ref('');
const showGitignoreEditor = ref(false);
const isSavingGitignore = ref(false);
const notification = ref({ show: false, message: '', type: 'success' as 'success' | 'error' });

const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
    notification.value = { show: true, message, type };
    setTimeout(() => {
        notification.value.show = false;
    }, 3000);
};

onMounted(async () => {
    if (!props.projectId || !project.value) {
        if (showDashboard) showDashboard();
        return;
    }
    
    // Load current config
    const currentConfig = await projectStore.getConfig(props.projectId);
    if (currentConfig) {
        config.value = currentConfig;
    }
    
    // Auto-sync visibility from GitHub if it's a GitHub repo
    if (project.value.remote_url && project.value.remote_url.includes('github.com')) {
        await syncVisibilityFromGitHub();
    }
    
    // Load .gitignore content
    await loadGitignore();
});

const handleSave = async () => {
    if (!props.projectId) return;
    
    isSaving.value = true;
    try {
        await projectStore.updateConfig(props.projectId, config.value);
        showNotification(t.value.settings.saveSuccess, 'success');
        await projectStore.fetchProjects();
    } catch (e: any) {
        const errorMsg = e?.message || e?.toString() || 'Unknown error';
        console.error('[ERROR] Failed to save config:', e);
        
        // Check if it's a visibility update issue
        if (errorMsg.includes('visibility') || errorMsg.includes('GitHub token')) {
            showNotification('⚠️ ' + errorMsg, 'error');
        } else {
            showNotification(t.value.settings.saveFailed + ': ' + errorMsg, 'error');
        }
    } finally {
        isSaving.value = false;
    }
};

const handleDelete = async () => {
    if (!project.value || !props.projectId) return;
    
    try {
        const res = await fetch(`/api/projects/${props.projectId}`, {
            method: 'DELETE'
        });
        
        if (res.ok) {
            await projectStore.fetchProjects();
            if (showDashboard) showDashboard();
        } else {
            const error = await res.json();
            showNotification(t.value.settings.danger.deleteFailed + ': ' + error.detail, 'error');
        }
    } catch (e) {
        showNotification(t.value.settings.danger.deleteFailed + ': ' + e, 'error');
    }
};

const syncIntervalMinutes = computed({
    get: () => Math.floor(config.value.sync_interval / 60),
    set: (val) => { config.value.sync_interval = val * 60; }
});

const handleMouseMove = (e: MouseEvent, ref: HTMLElement | null) => {
    if (!ref) return;
    const rect = ref.getBoundingClientRect();
    mousePosition.value = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
    };
};

const loadGitignore = async () => {
    if (!props.projectId) return;
    try {
        const res = await fetch(`/api/projects/${props.projectId}/gitignore`);
        if (res.ok) {
            const data = await res.json();
            gitignoreContent.value = data.content || '';
        }
    } catch (e) {
        console.error('[ERROR] Failed to load .gitignore:', e);
    }
};

const saveGitignore = async () => {
    if (!props.projectId) return;
    isSavingGitignore.value = true;
    try {
        const res = await fetch(`/api/projects/${props.projectId}/gitignore`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: gitignoreContent.value })
        });
        
        if (res.ok) {
            showNotification(t.value.settings.gitignore.saveSuccess, 'success');
            showGitignoreEditor.value = false;
        } else {
            const error = await res.json();
            showNotification(t.value.settings.saveFailed + ': ' + error.detail, 'error');
        }
    } catch (e) {
        showNotification(t.value.settings.saveFailed + ': ' + e, 'error');
    } finally {
        isSavingGitignore.value = false;
    }
};

const addCommonIgnores = (pattern: string) => {
    const lines = gitignoreContent.value.split('\n');
    if (!lines.includes(pattern)) {
        gitignoreContent.value += (gitignoreContent.value ? '\n' : '') + pattern;
    }
};

const syncVisibilityFromGitHub = async () => {
    if (!props.projectId) return;
    
    try {
        const res = await fetch(`/api/projects/${props.projectId}/sync-visibility`, {
            method: 'POST'
        });
        
        if (res.ok) {
            const data = await res.json();
            config.value.is_private = data.is_private;
            // Silent sync on page load - no notification
        } else if (res.status === 404) {
            // Repository deleted on GitHub
            const error = await res.json();
            if (error.detail?.startsWith('REPO_DELETED:')) {
                deletedRepoName.value = error.detail.split('REPO_DELETED:')[1];
                showRepoDeletedDialog.value = true;
            } else {
                console.error('[SYNC] Failed to sync visibility:', error.detail);
            }
        } else {
            // Only show error if it's not a token issue (user might not have configured token yet)
            const error = await res.json();
            if (!error.detail?.includes('token')) {
                console.error('[SYNC] Failed to sync visibility:', error.detail);
            }
        }
    } catch (e) {
        console.error('[SYNC] Failed to sync visibility:', e);
    }
};

const handleDeleteLocalProject = async () => {
    showRepoDeletedDialog.value = false;
    await handleDelete();
};

const handleKeepProject = () => {
    showRepoDeletedDialog.value = false;
};
</script>

<template>
    <div class="h-screen flex flex-col bg-black text-white font-sans overflow-hidden relative">
        <!-- Space Background -->
        <div class="space-grid fixed inset-0"></div>
        <div class="fixed inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/80 pointer-events-none z-0"></div>

        <!-- Compact Navbar -->
        <nav class="border-b border-white/10 bg-black/60 backdrop-blur-xl flex-none z-50">
            <div class="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <Button variant="ghost" size="sm" @click="showDashboard && showDashboard()" class="h-8 px-3 text-xs text-zinc-300 hover:text-white hover:bg-white/10 border border-zinc-700 hover:border-zinc-600">
                        ← {{ t.settings.back }}
                    </Button>
                    <div class="flex items-center gap-2">
                        <span class="text-xl font-bold text-white">{{ t.settings.title }}</span>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <Button 
                        class="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white h-8 px-4 text-xs font-bold"
                        @click="handleSave"
                        :disabled="isSaving"
                    >
                        {{ isSaving ? t.settings.saving : t.settings.save }}
                    </Button>
                </div>
            </div>
        </nav>

        <!-- Bento Grid Layout - No Scroll -->
        <main class="flex-1 max-w-7xl w-full mx-auto p-4 z-10 overflow-hidden">
            <div v-if="project" class="grid grid-cols-12 gap-3 h-full">
                
                <!-- Project Info & Visibility - Span 4 columns -->
                <div class="col-span-4 space-y-3">
                    <!-- Project Info Card -->
                    <div class="group relative bg-zinc-900/60 backdrop-blur-md border border-white/10 rounded-xl p-4 hover:border-purple-500/50 transition-all overflow-hidden">
                        <div class="pointer-events-none absolute inset-0 rounded-xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                             :style="`background: radial-gradient(circle at ${mousePosition.x}px ${mousePosition.y}px, rgba(168, 85, 247, 0.15) 0%, rgba(0, 0, 0, 0) 70%)`"
                             @mousemove="(e) => handleMouseMove(e, $event.currentTarget as HTMLElement)">
                        </div>
                        <div class="relative z-10">
                            <h2 class="text-lg font-bold mb-3 text-white/90">{{ project.name }}</h2>
                            <p class="text-xs text-zinc-400 font-mono mb-2 truncate" :title="project.path">{{ project.path }}</p>
                            <p v-if="project.remote_url" class="text-xs text-zinc-500 truncate" :title="project.remote_url">{{ project.remote_url }}</p>
                        </div>
                    </div>

                    <!-- Repository Visibility Toggle with Neon Border -->
                    <div class="relative bg-zinc-900/60 backdrop-blur-md border rounded-xl p-4 overflow-hidden"
                         :class="config.is_private ? 'border-yellow-500/50' : 'border-green-500/50'">
                        <div class="neon-border-wrapper absolute inset-0 rounded-xl pointer-events-none"
                             :class="config.is_private ? 'neon-yellow' : 'neon-green'">
                        </div>
                        <div class="relative z-10">
                            <div class="flex items-center justify-between mb-3">
                                <span class="text-sm font-bold text-white/90">{{ t.settings.visibility.title }}</span>
                                <div class="text-xs px-2 py-1 rounded-full font-bold"
                                     :class="config.is_private ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'">
                                    {{ config.is_private ? t.settings.visibility.private : t.settings.visibility.public }}
                                </div>
                            </div>
                            
                            <!-- Current Status Info -->
                            <div class="mb-3 p-2 rounded bg-black/30 border border-white/5">
                                <p class="text-xs text-zinc-400">
                                    {{ t.settings.visibility.currentStatus }} <span :class="config.is_private ? 'text-yellow-400' : 'text-green-400'">
                                        {{ config.is_private ? t.settings.visibility.privateWithLabel : t.settings.visibility.publicWithLabel }}
                                    </span>
                                </p>
                                <p class="text-[10px] text-zinc-500 mt-1">
                                    {{ t.settings.visibility.syncHint }}
                                </p>
                            </div>
                            
                            <div class="flex gap-2 mb-2">
                                <button
                                    @click="config.is_private = true"
                                    class="flex-1 py-2 px-3 text-xs rounded-lg border transition-all duration-300 font-medium"
                                    :class="config.is_private 
                                        ? 'bg-yellow-600/20 border-yellow-500 text-yellow-300 shadow-lg shadow-yellow-500/20' 
                                        : 'bg-black/50 border-zinc-700 text-zinc-400 hover:border-yellow-500/50'"
                                >
                                    {{ t.settings.visibility.privateBtn }}
                                </button>
                                <button
                                    @click="config.is_private = false"
                                    class="flex-1 py-2 px-3 text-xs rounded-lg border transition-all duration-300 font-medium"
                                    :class="!config.is_private 
                                        ? 'bg-green-600/20 border-green-500 text-green-300 shadow-lg shadow-green-500/20' 
                                        : 'bg-black/50 border-zinc-700 text-zinc-400 hover:border-green-500/50'"
                                >
                                    {{ t.settings.visibility.publicBtn }}
                                </button>
                            </div>
                            <p class="text-xs text-zinc-500 leading-relaxed">
                                {{ config.is_private ? t.settings.visibility.privateDesc : t.settings.visibility.publicDesc }}
                            </p>
                        </div>
                    </div>

                    <!-- Danger Zone -->
                    <div class="bg-red-900/20 backdrop-blur-md border border-red-500/30 rounded-xl p-4">
                        <h3 class="text-sm font-bold mb-3 text-red-400">{{ t.settings.danger.title }}</h3>
                        <Button 
                            variant="ghost"
                            class="w-full text-red-400 hover:text-red-300 hover:bg-red-500/10 border border-red-500/30 text-xs h-8"
                            @click="showDeleteConfirm = true"
                        >
                            {{ t.settings.danger.deleteProject }}
                        </Button>
                    </div>
                </div>

                <!-- Sync Policy - Span 4 columns -->
                <div class="col-span-4 bg-zinc-900/60 backdrop-blur-md border border-white/10 rounded-xl p-4 hover:border-purple-500/50 transition-all">
                    <h3 class="text-base font-bold mb-4 text-white/90">{{ t.settings.sync.title }}</h3>
                    
                    <div class="space-y-3">
                        <div>
                            <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-bold">{{ t.settings.sync.modeLabel }}</label>
                            <div class="grid grid-cols-2 gap-1.5">
                                <button
                                    v-for="mode in ['interval', 'fixed'] as const"
                                    :key="mode"
                                    @click="config.sync_mode = mode"
                                    class="py-2 px-2 text-xs rounded-lg border transition-all duration-300 font-medium"
                                    :class="config.sync_mode === mode 
                                        ? 'bg-purple-600/20 border-purple-500 text-purple-300 shadow-lg shadow-purple-500/20' 
                                        : 'bg-black/50 border-zinc-700 text-zinc-400 hover:border-purple-500/50'"
                                >
                                    {{ t.addModal.sync.mode[mode] }}
                                </button>
                            </div>
                        </div>

                        <div v-if="config.sync_mode === 'interval'">
                            <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-bold">{{ t.settings.sync.intervalLabel }}</label>
                            <input 
                                v-model.number="syncIntervalMinutes"
                                type="number"
                                min="1"
                                class="w-full bg-black/50 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:border-purple-500 outline-none text-white"
                            />
                        </div>

                        <div v-if="config.sync_mode === 'fixed'">
                            <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-bold">{{ t.settings.sync.fixedLabel }}</label>
                            <input 
                                v-model="config.sync_fixed_time"
                                type="time"
                                class="w-full bg-black/50 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:border-purple-500 outline-none text-white"
                            />
                        </div>

                        <div class="pt-2 space-y-2">
                            <div class="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 transition-colors">
                                <input 
                                    type="checkbox" 
                                    v-model="config.auto_push" 
                                    id="auto_push"
                                    class="accent-purple-600 w-4 h-4 rounded cursor-pointer"
                                />
                                <label for="auto_push" class="text-sm text-zinc-300 cursor-pointer">{{ t.settings.sync.autoPush }}</label>
                            </div>
                            <div class="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 transition-colors">
                                <input 
                                    type="checkbox" 
                                    v-model="config.strip_secrets" 
                                    id="strip_secrets"
                                    class="accent-purple-600 w-4 h-4 rounded cursor-pointer"
                                />
                                <label for="strip_secrets" class="text-sm text-zinc-300 cursor-pointer">{{ t.settings.sync.stripSecrets }}</label>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Advanced Settings - Span 4 columns -->
                <div class="col-span-4 space-y-3">
                    <div class="bg-zinc-900/60 backdrop-blur-md border border-white/10 rounded-xl p-4 hover:border-purple-500/50 transition-all">
                        <h3 class="text-base font-bold mb-4 text-white/90">{{ t.settings.advanced.title }}</h3>
                        
                        <div class="space-y-3">
                            <div>
                                <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-bold">{{ t.settings.advanced.maxFileSize }}</label>
                                <input 
                                    v-model.number="config.max_file_size_mb"
                                    type="number"
                                    min="1"
                                    class="w-full bg-black/50 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:border-purple-500 outline-none text-white"
                                />
                            </div>

                            <div>
                                <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-bold">{{ t.settings.advanced.commitPrefix }}</label>
                                <div class="grid grid-cols-2 gap-1.5">
                                    <button
                                        v-for="prefix in ['backup: ', 'feat: ', 'fix: ', 'docs: ', 'style: ', 'chore: ']"
                                        :key="prefix"
                                        @click="config.default_commit_prefix = prefix"
                                        class="py-2 px-2 text-xs rounded-lg border transition-all duration-300 font-medium text-left"
                                        :class="config.default_commit_prefix === prefix 
                                            ? 'bg-purple-600/20 border-purple-500 text-purple-300 shadow-lg shadow-purple-500/20' 
                                            : 'bg-black/50 border-zinc-700 text-zinc-400 hover:border-purple-500/50'"
                                    >
                                        {{ prefix }}
                                    </button>
                                </div>
                            </div>

                            <div class="pt-2 space-y-2">
                                <div class="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 transition-colors">
                                    <input 
                                        type="checkbox" 
                                        v-model="config.ignore_hidden" 
                                        id="ignore_hidden"
                                        class="accent-purple-600 w-4 h-4 rounded cursor-pointer"
                                    />
                                    <label for="ignore_hidden" class="text-sm text-zinc-300 cursor-pointer">{{ t.settings.advanced.ignoreHidden }}</label>
                                </div>
                                <!-- AI提交信息功能已隐藏，未来实现时再开启 -->
                            </div>
                        </div>
                    </div>

                    <!-- .gitignore Editor -->
                    <div class="bg-zinc-900/60 backdrop-blur-md border border-white/10 rounded-xl p-4 hover:border-purple-500/50 transition-all">
                        <div class="flex items-center justify-between mb-3">
                            <h3 class="text-sm font-bold text-white/90">{{ t.settings.gitignore.title }}</h3>
                            <Button 
                                variant="ghost"
                                size="sm"
                                class="h-7 px-3 text-xs text-purple-400 hover:text-purple-300 hover:bg-purple-500/10"
                                @click="showGitignoreEditor = true"
                            >
                                {{ t.settings.gitignore.edit }}
                            </Button>
                        </div>
                        <p class="text-xs text-zinc-500 leading-relaxed">
                            {{ t.settings.gitignore.description }}
                        </p>
                    </div>
                </div>

            </div>
        </main>

        <!-- Delete Confirmation Dialog -->
        <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-6">
            <Card class="w-full max-w-md bg-zinc-950/90 border-red-500/50 p-6 backdrop-blur-xl">
                <h3 class="text-xl font-bold text-red-400 mb-4">{{ t.settings.danger.confirmTitle }}</h3>
                <p class="text-zinc-300 mb-4">{{ t.settings.danger.confirmMessage }} "{{ project?.name }}" 吗？</p>
                
                <div class="space-y-3 mb-6">
                    <div class="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                        <p class="text-sm text-blue-300">
                            ℹ️ 此操作仅从图图的代码方舟列表中移除项目，不会删除本地文件或远程仓库。
                        </p>
                    </div>
                </div>

                <div class="flex justify-end gap-3">
                    <Button variant="ghost" @click="showDeleteConfirm = false" class="text-xs h-9 text-zinc-300 hover:text-white hover:bg-white/10 border border-zinc-700 hover:border-zinc-600">{{ t.settings.cancel }}</Button>
                    <Button 
                        class="bg-red-600 hover:bg-red-500 text-white text-xs h-9 px-4"
                        @click="handleDelete"
                    >
                        {{ t.settings.danger.confirmDelete }}
                    </Button>
                </div>
            </Card>
        </div>

        <!-- Repo Deleted on GitHub Dialog -->
        <div v-if="showRepoDeletedDialog" class="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-6">
            <Card class="w-full max-w-md bg-zinc-950/90 border-yellow-500/50 p-6 backdrop-blur-xl">
                <h3 class="text-xl font-bold text-yellow-400 mb-4">⚠️ {{ t.settings.danger.repoDeletedOnGithub }}</h3>
                <p class="text-zinc-300 mb-4">
                    {{ t.settings.danger.repoDeletedMessage.replace('{repo}', deletedRepoName) }}
                </p>
                
                <div class="space-y-3 mb-6">
                    <div class="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                        <p class="text-sm text-yellow-300">
                            ⚠️ GitHub 上的仓库 "{{ deletedRepoName }}" 已不存在。您可以选择删除本地项目配置，或保留项目继续使用本地文件。
                        </p>
                    </div>
                </div>

                <div class="flex justify-end gap-3">
                    <Button variant="ghost" @click="handleKeepProject" class="text-xs h-9 text-zinc-300 hover:text-white hover:bg-white/10 border border-zinc-700 hover:border-zinc-600">
                        {{ t.settings.danger.keepProject }}
                    </Button>
                    <Button 
                        class="bg-red-600 hover:bg-red-500 text-white text-xs h-9 px-4"
                        @click="handleDeleteLocalProject"
                    >
                        {{ t.settings.danger.deleteLocalProject }}
                    </Button>
                </div>
            </Card>
        </div>

        <!-- .gitignore Editor Dialog -->
        <div v-if="showGitignoreEditor" class="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-6">
            <Card class="w-full max-w-3xl bg-zinc-950/90 border-purple-500/50 p-6 backdrop-blur-xl max-h-[85vh] flex flex-col">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold text-purple-400">{{ t.settings.gitignore.editorTitle }}</h3>
                    <button @click="showGitignoreEditor = false" class="text-zinc-400 hover:text-white">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <!-- Common Patterns -->
                <div class="mb-4">
                    <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-bold">{{ t.settings.gitignore.commonPatterns }}</label>
                    <div class="flex flex-wrap gap-2">
                        <button
                            v-for="pattern in ['node_modules/', '__pycache__/', '*.log', '.DS_Store', '.env', 'dist/', 'build/', '*.pyc', '.vscode/', '.idea/']"
                            :key="pattern"
                            @click="addCommonIgnores(pattern)"
                            class="px-3 py-1.5 text-xs rounded-lg border border-zinc-700 bg-black/50 text-zinc-400 hover:border-purple-500/50 hover:text-purple-300 transition-all font-mono"
                        >
                            + {{ pattern }}
                        </button>
                    </div>
                </div>
                
                <div class="flex-1 min-h-0 mb-4">
                    <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-bold">{{ t.settings.gitignore.fileContent }}</label>
                    <textarea
                        v-model="gitignoreContent"
                        class="w-full h-full min-h-[300px] bg-black/50 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:border-purple-500 outline-none text-white font-mono resize-none"
                        :placeholder="t.settings.gitignore.placeholder"
                    ></textarea>
                </div>

                <div class="flex justify-between items-center">
                    <p class="text-xs text-zinc-500">
                        {{ t.settings.gitignore.hint }}
                    </p>
                    <div class="flex gap-3">
                        <Button variant="ghost" @click="showGitignoreEditor = false" class="text-xs h-9 text-zinc-300 hover:text-white hover:bg-white/10 border border-zinc-700 hover:border-zinc-600">{{ t.settings.cancel }}</Button>
                        <Button 
                            class="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white text-xs h-9 px-4"
                            @click="saveGitignore"
                            :disabled="isSavingGitignore"
                        >
                            {{ isSavingGitignore ? t.settings.saving : t.settings.save }}
                        </Button>
                    </div>
                </div>
            </Card>
        </div>

        <!-- Toast Notification -->
        <Transition
            enter-active-class="transition-all duration-300 ease-out"
            enter-from-class="opacity-0 translate-y-4"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="opacity-100 translate-y-0"
            leave-to-class="opacity-0 translate-y-4"
        >
            <div v-if="notification.show" class="fixed top-20 left-1/2 -translate-x-1/2 z-[100] px-6 py-3 rounded-lg shadow-2xl backdrop-blur-xl border"
                 :class="notification.type === 'success' 
                    ? 'bg-green-500/20 border-green-500/50 text-green-300' 
                    : 'bg-red-500/20 border-red-500/50 text-red-300'">
                <div class="flex items-center gap-2">
                    <span class="text-xl">{{ notification.type === 'success' ? '✅' : '❌' }}</span>
                    <span class="text-sm font-medium">{{ notification.message }}</span>
                </div>
            </div>
        </Transition>

    </div>
</template>

<style scoped>
.space-grid {
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
}

/* Neon Border Animation */
.neon-border-wrapper {
    filter: blur(1px);
    z-index: 0;
    opacity: 0.6;
}

.neon-border-wrapper::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    padding: 1px;
    background: linear-gradient(135deg, currentColor, transparent, currentColor);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    animation: rotate-border 4s linear infinite;
}

.neon-yellow {
    color: rgb(234, 179, 8);
    filter: blur(1px) drop-shadow(0 0 8px rgb(234, 179, 8));
}

.neon-green {
    color: rgb(34, 197, 94);
    filter: blur(1px) drop-shadow(0 0 8px rgb(34, 197, 94));
}

@keyframes rotate-border {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}

/* Custom Scrollbar for any overflow */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
}

::-webkit-scrollbar-thumb {
    background: rgba(168, 85, 247, 0.5);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(168, 85, 247, 0.7);
}
</style>

