<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useProjectStore } from '../stores/projects';
import { useLocaleStore } from '../stores/locale';
import Button from './ui/Button.vue';
import { storeToRefs } from 'pinia';

const projectStore = useProjectStore();
const localeStore = useLocaleStore();
const { t } = storeToRefs(localeStore);

const emit = defineEmits<{
  close: [];
  success: [];
}>();

const activeTab = ref<'auto' | 'manual'>('auto');
const isProcessing = ref(false);
const currentStep = ref(0);
const showErrorDialog = ref(false);
const errorMessage = ref('');

// Auto Init Form
const formAuto = ref({
  path: '',
  name: '',
  description: '',
  is_private: true
});

// Manual Init Form
const formManual = ref({
  path: ''
});

// Sync Config (shared for both auto and manual)
const syncConfig = ref({
  sync_mode: 'interval' as 'interval' | 'fixed',
  sync_interval: 300, // 5 minutes in seconds
  sync_fixed_time: '02:00'
});

// .gitignore Config
const gitignoreContent = ref('__pycache__/\n*.log\nnode_modules/\n.DS_Store\n.venv/\ndist/\n');
const showGitignoreEditor = ref(false);

// Multi-step loader configuration
const loadingSteps = computed(() => {
  if (activeTab.value === 'auto') {
    return [
      { text: t.value.wizard?.steps?.initGit || '初始化 Git 仓库...', duration: 1500 },
      { text: t.value.wizard?.steps?.createRepo || '在 GitHub 创建仓库...', duration: 2000 },
      { text: t.value.wizard?.steps?.linkRemote || '关联远程仓库...', duration: 1500 },
      { text: t.value.wizard?.steps?.firstCommit || '提交初始文件...', duration: 2000 },
      { text: t.value.wizard?.steps?.complete || '完成！', duration: 1000 }
    ];
  } else {
    return [
      { text: t.value.wizard?.steps?.scanning || '扫描本地仓库...', duration: 1500 },
      { text: t.value.wizard?.steps?.analyzing || '分析 Git 历史...', duration: 1500 },
      { text: t.value.wizard?.steps?.configuring || '配置监控策略...', duration: 1000 },
      { text: t.value.wizard?.steps?.complete || '完成！', duration: 1000 }
    ];
  }
});

// Auto-fill name from path
watch(() => formAuto.value.path, (newPath) => {
  if (newPath) {
    const parts = newPath.split(/[\\/]/);
    const folder = parts[parts.length - 1] || parts[parts.length - 2];
    if (folder && !formAuto.value.name) {
      formAuto.value.name = folder;
    }
  }
});

const handleAutoInit = async () => {
  isProcessing.value = true;
  currentStep.value = 0;
  
  // 启动动画步骤计时器
  const stepInterval = setInterval(() => {
    if (currentStep.value < loadingSteps.value.length - 1) {
      currentStep.value++;
    }
  }, 1500);
  
  try {
    const project = await projectStore.autoInitProject({
      path: formAuto.value.path,
      name: formAuto.value.name,
      description: formAuto.value.description,
      is_private: formAuto.value.is_private,
      lang: localeStore.currentLocale,  // 传递当前语言设置
      gitignore_content: gitignoreContent.value  // 传递自定义 .gitignore 内容
    });

    // 应用同步配置
    if (project && project.id) {
      await projectStore.updateConfig(project.id, {
        ...project.config,
        sync_mode: syncConfig.value.sync_mode,
        sync_interval: syncConfig.value.sync_interval * 60,
        sync_fixed_time: syncConfig.value.sync_fixed_time,
        auto_push: true
      });
    }

    // 确保动画播放到最后一步
    currentStep.value = loadingSteps.value.length - 1;
    
    // Wait a bit for the loader animation
    setTimeout(() => {
      clearInterval(stepInterval);
      isProcessing.value = false;
      currentStep.value = 0;
      emit('success');
      emit('close');
    }, 1500);
  } catch (e) {
    clearInterval(stepInterval);
    isProcessing.value = false;
    currentStep.value = 0;
    errorMessage.value = String(e);
    showErrorDialog.value = true;
  }
};

const handleManualAdd = async () => {
  if (!formManual.value.path) return;
  isProcessing.value = true;
  currentStep.value = 0;
  
  // 启动动画步骤计时器
  const stepInterval = setInterval(() => {
    if (currentStep.value < loadingSteps.value.length - 1) {
      currentStep.value++;
    }
  }, 1500);
  
  try {
    const project = await projectStore.addProject(formManual.value.path);

    // 应用同步配置
    if (project && project.id) {
      await projectStore.updateConfig(project.id, {
        ...project.config,
        sync_mode: syncConfig.value.sync_mode,
        sync_interval: syncConfig.value.sync_interval * 60,
        sync_fixed_time: syncConfig.value.sync_fixed_time,
        auto_push: true
      });
    }

    // 确保动画播放到最后一步
    currentStep.value = loadingSteps.value.length - 1;
    
    // Wait a bit for the loader animation
    setTimeout(() => {
      clearInterval(stepInterval);
      isProcessing.value = false;
      currentStep.value = 0;
      emit('success');
      emit('close');
    }, 1500);
  } catch (e) {
    clearInterval(stepInterval);
    isProcessing.value = false;
    currentStep.value = 0;
    errorMessage.value = String(e);
    showErrorDialog.value = true;
  }
};

const browseFolder = async (tab: 'auto' | 'manual') => {
  try {
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
    alert(t.value.addModal.browseFailure);
  }
};

const handleSubmit = () => {
  if (activeTab.value === 'auto') {
    handleAutoInit();
  } else {
    handleManualAdd();
  }
};

const addCommonIgnores = (pattern: string) => {
  const lines = gitignoreContent.value.split('\n');
  if (!lines.includes(pattern)) {
    gitignoreContent.value += (gitignoreContent.value ? '\n' : '') + pattern;
  }
};
</script>

<template>
  <!-- Multi-Step Loader Overlay -->
  <Transition
    enter-active-class="transition-opacity duration-300"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-300"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="isProcessing && loadingSteps.length > 0"
      class="fixed inset-0 z-[200] flex size-full items-center justify-center backdrop-blur-2xl bg-black/90"
    >
      <div class="relative h-96">
        <div class="relative mx-auto mt-40 flex max-w-xl flex-col justify-start">
          <div
            v-for="(step, index) in loadingSteps"
            :key="index"
            class="mb-4 flex items-center gap-2 text-left transition-all duration-300 ease-in-out"
            :style="{
              opacity: index === currentStep ? 1 : 0.3,
            }"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              class="size-6 animate-spin text-purple-500"
            >
              <path
                fill-rule="evenodd"
                d="M4.755 10.059a7.5 7.5 0 0 1 12.548-3.364l1.903 1.903h-3.183a.75.75 0 1 0 0 1.5h4.992a.75.75 0 0 0 .75-.75V4.356a.75.75 0 0 0-1.5 0v3.18l-1.9-1.9A9 9 0 0 0 3.306 9.67a.75.75 0 1 0 1.45.388Zm15.408 3.352a.75.75 0 0 0-.919.53 7.5 7.5 0 0 1-12.548 3.364l-1.902-1.903h3.183a.75.75 0 0 0 0-1.5H2.984a.75.75 0 0 0-.75.75v4.992a.75.75 0 0 0 1.5 0v-3.18l1.9 1.9a9 9 0 0 0 15.059-4.035.75.75 0 0 0-.53-.918Z"
                clip-rule="evenodd"
              />
            </svg>
            <div class="flex flex-col">
              <span class="text-lg text-white">
                {{ step.text }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div class="absolute inset-x-0 bottom-0 z-[-1] h-full bg-gradient-to-t from-purple-900/20 via-transparent to-transparent"></div>
    </div>
  </Transition>

  <!-- Main Modal -->
  <div class="fixed inset-0 bg-black/95 backdrop-blur-xl z-50 flex items-center justify-center p-4">
    <!-- Compact Modal Container -->
    <div class="relative w-full max-w-2xl bg-zinc-950/80 border border-purple-500/20 rounded-xl overflow-hidden shadow-[0_0_50px_rgba(168,85,247,0.15)]">
      <!-- Animated Background Gradient -->
      <div class="absolute inset-0 bg-gradient-to-br from-purple-900/10 via-transparent to-blue-900/10 pointer-events-none"></div>

      <!-- Close Button -->
      <button
        @click="emit('close')"
        class="absolute right-3 top-3 z-10 text-zinc-500 hover:text-white transition-colors p-1.5 hover:bg-white/5 rounded-lg"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-4 h-4"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- Header with Animated Title -->
      <div class="relative px-5 pt-4 pb-3 border-b border-white/5">
        <div class="space-y-0.5">
          <h3 class="text-xl font-bold text-white tracking-tight">
            {{ t.addModal.title }}
          </h3>
          <p class="text-xs text-zinc-500">
            {{ t.addModal.subtitle[activeTab] }}
          </p>
        </div>
      </div>

      <!-- Morphing Tabs -->
      <div class="relative px-5 pt-3 flex gap-2">
        <button
          v-for="tab in (['auto', 'manual'] as const)"
          :key="tab"
          @click="activeTab = tab"
          class="relative flex-1 py-2 text-sm font-medium transition-all duration-300 rounded-lg"
          :class="activeTab === tab 
            ? 'bg-gradient-to-r from-purple-600 to-purple-500 text-white shadow-[0_0_20px_rgba(168,85,247,0.3)]' 
            : 'bg-black/40 text-zinc-400 hover:text-zinc-200 hover:bg-black/60'"
        >
          <span class="relative z-10">{{ t.addModal.tabs[tab] }}</span>
        </button>
      </div>

      <!-- Form Content -->
      <div class="relative px-5 py-4">
        <!-- Auto Tab Form -->
        <div v-if="activeTab === 'auto'" class="space-y-3">
          <!-- Info Box -->
          <div class="p-2.5 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-start gap-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 text-blue-400 flex-shrink-0 mt-0.5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
            <p class="text-xs text-blue-200/90">{{ t.addModal.autoDesc }}</p>
          </div>

          <!-- Path Input -->
          <div>
            <label class="block text-xs text-zinc-400 mb-1.5 uppercase tracking-wider font-semibold">
              {{ t.addModal.pathLabel }}
            </label>
            <div class="flex gap-2">
              <input
                v-model="formAuto.path"
                :placeholder="t.addModal.pathPlaceholder"
                class="flex-1 bg-black/60 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none text-white transition-all"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                class="px-3 py-1.5 text-xs border border-zinc-700 hover:border-purple-500 hover:bg-purple-500/10 text-zinc-300 hover:text-purple-300 whitespace-nowrap"
                @click="browseFolder('auto')"
              >
                {{ t.addModal.browseFolder }}
              </Button>
            </div>
          </div>

          <!-- Name & Private Checkbox -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-zinc-400 mb-1.5 uppercase tracking-wider font-semibold">
                {{ t.addModal.nameLabel }}
              </label>
              <input
                v-model="formAuto.name"
                placeholder="MyProject"
                class="w-full bg-black/60 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none text-white transition-all"
              />
            </div>
            <div>
              <label class="block text-xs text-zinc-400 mb-1.5 uppercase tracking-wider font-semibold">
                {{ t.addModal.privateLabel }}
              </label>
              <div class="flex items-center h-[30px] bg-black/60 border border-zinc-700 rounded-lg px-2.5">
                <input
                  type="checkbox"
                  v-model="formAuto.is_private"
                  id="is_private"
                  class="accent-purple-600 w-3.5 h-3.5 rounded"
                />
                <label for="is_private" class="ml-2 text-xs text-zinc-300 cursor-pointer select-none">
                  Private Repo
                </label>
              </div>
            </div>
          </div>

          <!-- Repository Description -->
          <div>
            <label class="block text-xs text-zinc-400 mb-1.5 uppercase tracking-wider font-semibold">
              {{ t.addModal.descriptionLabel }}
            </label>
            <textarea
              v-model="formAuto.description"
              :placeholder="t.addModal.descriptionPlaceholder"
              rows="2"
              class="w-full bg-black/60 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none text-white transition-all resize-none"
            ></textarea>
          </div>

          <!-- .gitignore Configuration -->
          <div class="border-t border-white/5 pt-3">
            <div class="flex items-center justify-between mb-2">
              <label class="block text-xs text-zinc-400 uppercase tracking-wider font-semibold">
                {{ t.addModal.gitignore.title }}
              </label>
              <Button 
                type="button"
                variant="ghost"
                size="sm"
                class="h-6 px-2 text-xs text-purple-400 hover:text-purple-300 hover:bg-purple-500/10"
                @click="showGitignoreEditor = true"
              >
                {{ t.addModal.gitignore.edit }}
              </Button>
            </div>
            <div class="p-2 bg-zinc-800/50 border border-zinc-700/50 rounded-lg">
              <p class="text-xs text-zinc-400 leading-relaxed">
                {{ t.addModal.gitignore.description }}
              </p>
            </div>
          </div>

          <!-- Sync Policy -->
          <div class="border-t border-white/5 pt-3">
            <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-semibold">
              {{ t.addModal.sync.label }}
            </label>
            <div class="flex gap-2 mb-2">
              <button
                v-for="mode in ['interval', 'fixed'] as const"
                :key="mode"
                type="button"
                @click="syncConfig.sync_mode = mode"
                class="flex-1 py-1.5 px-3 text-xs rounded-lg border transition-all"
                :class="syncConfig.sync_mode === mode
                  ? 'bg-purple-600 border-purple-500 text-white shadow-lg'
                  : 'bg-black/40 border-zinc-700 text-zinc-400 hover:border-purple-500/50 hover:text-zinc-200'"
              >
                {{ t.addModal.sync.mode[mode] }}
              </button>
            </div>

            <!-- Dynamic Sync Options -->
            <div v-if="syncConfig.sync_mode === 'interval'" class="flex items-center gap-2">
              <label class="text-xs text-zinc-400 whitespace-nowrap">{{ t.addModal.sync.intervalLabel }}:</label>
              <input
                v-model.number="syncConfig.sync_interval"
                type="number"
                min="1"
                class="flex-1 bg-black/60 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs focus:border-purple-500 outline-none text-white"
              />
            </div>
            <div v-if="syncConfig.sync_mode === 'fixed'" class="flex items-center gap-2">
              <label class="text-xs text-zinc-400 whitespace-nowrap">{{ t.addModal.sync.fixedLabel }}:</label>
              <input
                v-model="syncConfig.sync_fixed_time"
                type="time"
                class="flex-1 bg-black/60 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs focus:border-purple-500 outline-none text-white"
              />
            </div>
          </div>
        </div>

        <!-- Manual Tab Form -->
        <div v-else class="space-y-3">
          <!-- Info Box -->
          <div class="p-2.5 bg-zinc-800/50 border border-zinc-700/50 rounded-lg flex items-start gap-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 text-zinc-400 flex-shrink-0 mt-0.5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
            <p class="text-xs text-zinc-300">{{ t.addModal.manualDesc }}</p>
          </div>

          <!-- Path Input -->
          <div>
            <label class="block text-xs text-zinc-400 mb-1.5 uppercase tracking-wider font-semibold">
              {{ t.addModal.pathLabel }}
            </label>
            <div class="flex gap-2">
              <input
                v-model="formManual.path"
                :placeholder="t.addModal.pathPlaceholder"
                class="flex-1 bg-black/60 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none text-white transition-all"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                class="px-3 py-1.5 text-xs border border-zinc-700 hover:border-purple-500 hover:bg-purple-500/10 text-zinc-300 hover:text-purple-300 whitespace-nowrap"
                @click="browseFolder('manual')"
              >
                {{ t.addModal.browseFolder }}
              </Button>
            </div>
          </div>

          <!-- Sync Policy -->
          <div class="border-t border-white/5 pt-3">
            <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-semibold">
              {{ t.addModal.sync.label }}
            </label>
            <div class="flex gap-2 mb-2">
              <button
                v-for="mode in ['interval', 'fixed'] as const"
                :key="mode"
                type="button"
                @click="syncConfig.sync_mode = mode"
                class="flex-1 py-1.5 px-3 text-xs rounded-lg border transition-all"
                :class="syncConfig.sync_mode === mode
                  ? 'bg-purple-600 border-purple-500 text-white shadow-lg'
                  : 'bg-black/40 border-zinc-700 text-zinc-400 hover:border-purple-500/50 hover:text-zinc-200'"
              >
                {{ t.addModal.sync.mode[mode] }}
              </button>
            </div>

            <!-- Dynamic Sync Options -->
            <div v-if="syncConfig.sync_mode === 'interval'" class="flex items-center gap-2">
              <label class="text-xs text-zinc-400 whitespace-nowrap">{{ t.addModal.sync.intervalLabel }}:</label>
              <input
                v-model.number="syncConfig.sync_interval"
                type="number"
                min="1"
                class="flex-1 bg-black/60 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs focus:border-purple-500 outline-none text-white"
              />
            </div>
            <div v-if="syncConfig.sync_mode === 'fixed'" class="flex items-center gap-2">
              <label class="text-xs text-zinc-400 whitespace-nowrap">{{ t.addModal.sync.fixedLabel }}:</label>
              <input
                v-model="syncConfig.sync_fixed_time"
                type="time"
                class="flex-1 bg-black/60 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs focus:border-purple-500 outline-none text-white"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="relative px-5 py-3 border-t border-white/5 flex justify-end gap-2">
        <Button
          variant="ghost"
          @click="emit('close')"
          class="px-5 py-1.5 text-xs text-zinc-400 hover:text-white hover:bg-white/5"
        >
          {{ t.addModal.cancel }}
        </Button>
        <Button
          @click="handleSubmit"
          :disabled="isProcessing || (activeTab === 'auto' ? !formAuto.path || !formAuto.name : !formManual.path)"
          class="px-6 py-1.5 text-xs bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white shadow-[0_0_30px_rgba(168,85,247,0.3)] border-none transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {{ activeTab === 'auto' ? t.addModal.confirm : t.addModal.manualConfirm }}
        </Button>
      </div>
    </div>
  </div>

  <!-- .gitignore Editor Dialog -->
  <Transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="opacity-0 scale-90"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition-all duration-200 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-90"
  >
    <div v-if="showGitignoreEditor" class="fixed inset-0 bg-black/90 backdrop-blur-md z-[150] flex items-center justify-center p-6">
      <div class="w-full max-w-3xl bg-zinc-950/90 border border-purple-500/50 rounded-xl p-6 backdrop-blur-xl max-h-[85vh] flex flex-col shadow-[0_0_50px_rgba(168,85,247,0.3)]">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-bold text-purple-400">{{ t.addModal.gitignore.editorTitle }}</h3>
          <button @click="showGitignoreEditor = false" class="text-zinc-400 hover:text-white transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Common Patterns -->
        <div class="mb-4">
          <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-bold">{{ t.addModal.gitignore.commonPatterns }}</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="pattern in ['node_modules/', '__pycache__/', '*.log', '.DS_Store', '.env', 'dist/', 'build/', '*.pyc', '.vscode/', '.idea/']"
              :key="pattern"
              type="button"
              @click="addCommonIgnores(pattern)"
              class="px-3 py-1.5 text-xs rounded-lg border border-zinc-700 bg-black/50 text-zinc-400 hover:border-purple-500/50 hover:text-purple-300 transition-all font-mono"
            >
              + {{ pattern }}
            </button>
          </div>
        </div>
        
        <div class="flex-1 min-h-0 mb-4">
          <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-bold">{{ t.addModal.gitignore.fileContent }}</label>
          <textarea
            v-model="gitignoreContent"
            class="w-full h-full min-h-[300px] bg-black/50 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:border-purple-500 outline-none text-white font-mono resize-none"
            :placeholder="t.addModal.gitignore.placeholder"
          ></textarea>
        </div>

        <div class="flex justify-between items-center">
          <p class="text-xs text-zinc-500">
            {{ t.addModal.gitignore.hint }}
          </p>
          <div class="flex gap-3">
            <Button 
              variant="ghost" 
              @click="showGitignoreEditor = false" 
              class="text-xs h-9 text-zinc-300 hover:text-white hover:bg-white/10 border border-zinc-700 hover:border-zinc-600"
            >
              {{ t.addModal.gitignore.close }}
            </Button>
            <Button 
              class="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white text-xs h-9 px-4"
              @click="showGitignoreEditor = false"
            >
              {{ t.addModal.gitignore.done }}
            </Button>
          </div>
        </div>
      </div>
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
    <div v-if="showErrorDialog" class="fixed inset-0 bg-red-900/20 backdrop-blur-md z-[100] flex items-center justify-center p-4">
      <div class="w-full max-w-md bg-zinc-950 border border-red-500/50 rounded-xl p-0 overflow-hidden shadow-[0_0_50px_rgba(239,68,68,0.3)]">
        <div class="p-8 flex flex-col items-center text-center">
          <!-- Error Icon with Animation -->
          <div class="w-20 h-20 rounded-full bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center mb-5 shadow-[0_0_40px_rgba(239,68,68,0.4)] animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          
          <!-- Title -->
          <h3 class="text-2xl font-bold text-red-400 mb-3">
            {{ t.addModal.error }}
          </h3>
          
          <!-- Error Message -->
          <div class="w-full p-4 bg-red-500/10 border border-red-500/30 rounded-lg mb-6">
            <p class="text-zinc-200 text-sm font-mono break-words text-left">
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
            {{ t.addModal.confirmBtn }}
          </Button>
        </div>
      </div>
    </div>
  </Transition>
</template>


