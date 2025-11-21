<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useLocaleStore } from '../stores/locale';
import { storeToRefs } from 'pinia';
import Button from './ui/Button.vue';

const localeStore = useLocaleStore();
const { t } = storeToRefs(localeStore);

const emit = defineEmits<{
  close: [];
  success: [];
}>();

const showTokenHelp = ref(false);
const isLoading = ref(false);
const isSaving = ref(false);
const showToken = ref(false); // 控制 token 明文/密文显示
const showSuccessDialog = ref(false);
const showErrorDialog = ref(false);
const showConfirmDialog = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const settings = ref({
  github_token: '',
  has_token: false,
  token_preview: ''
});

const fetchSettings = async () => {
  isLoading.value = true;
  try {
    const response = await fetch('http://127.0.0.1:8000/settings/');
    const data = await response.json();
    settings.value.has_token = data.has_github_token;
    settings.value.token_preview = data.github_token_preview || '';
  } catch (error) {
    console.log('[ERROR] Failed to fetch settings:', error);
  } finally {
    isLoading.value = false;
  }
};

const saveToken = async () => {
  if (!settings.value.github_token.trim()) {
    errorMessage.value = t.value.tokenDialog.errorMsg.emptyToken;
    showErrorDialog.value = true;
    return;
  }
  
  isSaving.value = true;
  try {
    const response = await fetch('http://127.0.0.1:8000/settings/', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        github_token: settings.value.github_token
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      settings.value.has_token = data.has_github_token;
      settings.value.token_preview = data.github_token_preview;
      settings.value.github_token = ''; // Clear input
      emit('success');
      successMessage.value = t.value.tokenDialog.successMsg.tokenSaved;
      showSuccessDialog.value = true;
    } else {
      errorMessage.value = t.value.tokenDialog.errorMsg.saveFailed;
      showErrorDialog.value = true;
    }
  } catch (error) {
    console.log('[ERROR] Failed to save token:', error);
    errorMessage.value = t.value.tokenDialog.errorMsg.saveFailed;
    showErrorDialog.value = true;
  } finally {
    isSaving.value = false;
  }
};

const clearToken = async () => {
  showConfirmDialog.value = true;
};

const handleConfirmClear = async () => {
  showConfirmDialog.value = false;
  
  try {
    const response = await fetch('http://127.0.0.1:8000/settings/github-token', {
      method: 'DELETE'
    });
    
    if (response.ok) {
      settings.value.has_token = false;
      settings.value.token_preview = '';
      successMessage.value = t.value.tokenDialog.successMsg.tokenCleared;
      showSuccessDialog.value = true;
    }
  } catch (error) {
    console.log('[ERROR] Failed to clear token:', error);
    errorMessage.value = t.value.tokenDialog.errorMsg.clearFailed + error;
    showErrorDialog.value = true;
  }
};

const openGithubSettings = async () => {
  const url = 'https://github.com/settings/tokens/new?scopes=repo,workflow,delete_repo&description=TuTu-Code-Ark+Token';

  try {
    // Try using Tauri API for desktop app
    const tauriApi = await import('@tauri-apps/api/core').catch(() => null);
    if (tauriApi && typeof tauriApi.invoke === 'function') {
      await tauriApi.invoke('open_external', { url });
      console.log('[INFO] Opened GitHub settings via Tauri');
      return;
    }
  } catch (importError) {
    console.log('[INFO] Tauri not available, falling back to window.open');
  }

  // Fallback to window.open for web/dev environment
  try {
    const newWindow = window.open(url, '_blank', 'noopener,noreferrer');

    if (!newWindow) {
      // Browser blocked popup
      const userConfirmed = confirm(t.value.tokenDialog.errorMsg.browserBlocked);

      if (userConfirmed) {
        try {
          await navigator.clipboard.writeText(url);
          successMessage.value = t.value.tokenDialog.errorMsg.urlCopied;
          showSuccessDialog.value = true;
        } catch (clipError) {
          prompt(t.value.tokenDialog.errorMsg.copyPrompt, url);
        }
      }
    }
  } catch (e) {
    console.error('[ERROR] Failed to open URL:', e);
    prompt(t.value.tokenDialog.errorMsg.copyManual, url);
  }
};

onMounted(() => {
  fetchSettings();
});
</script>

<template>
  <div class="fixed inset-0 bg-black/90 backdrop-blur-md z-[60] flex items-center justify-center p-6">
    <div class="w-full max-w-lg bg-zinc-900/95 border border-purple-500/30 rounded-xl shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="p-5 border-b border-purple-500/20 bg-gradient-to-r from-purple-900/20 to-blue-900/20">
        <h3 class="text-xl font-bold text-white flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {{ t.tokenDialog.title }}
        </h3>
        <p class="text-sm text-zinc-400 mt-1">{{ t.tokenDialog.subtitle }}</p>
      </div>

      <!-- Content -->
      <div class="p-6 space-y-5">
        <!-- Current Status -->
        <div v-if="settings.has_token" class="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-semibold text-green-400">{{ t.tokenDialog.tokenConfigured }}</p>
              <p class="text-xs text-zinc-400 mt-1 font-mono">{{ settings.token_preview }}</p>
            </div>
            <button
              @click="clearToken"
              class="text-xs text-red-400 hover:text-red-300 underline transition-colors"
            >
              {{ t.tokenDialog.clearToken }}
            </button>
          </div>
        </div>

        <div v-else class="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p class="text-sm text-amber-400">{{ t.tokenDialog.notConfigured }}</p>
          <p class="text-xs text-zinc-400 mt-1">{{ t.tokenDialog.notConfiguredDesc }}</p>
        </div>

        <!-- Token Input -->
        <div>
          <label class="block text-xs text-zinc-400 mb-2 uppercase tracking-wider font-semibold">
            {{ t.tokenDialog.tokenLabel }}
          </label>
          <div class="relative">
            <input
              v-model="settings.github_token"
              :type="showToken ? 'text' : 'password'"
              :placeholder="t.tokenDialog.tokenPlaceholder"
              class="w-full bg-black/60 border border-zinc-700 rounded-lg px-3 py-2.5 pr-10 text-sm focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none text-white transition-all font-mono"
              @keyup.enter="saveToken"
            />
            <button
              type="button"
              @click="showToken = !showToken"
              class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-zinc-400 hover:text-white transition-colors rounded hover:bg-white/5"
              tabindex="-1"
            >
              <!-- 眼睛图标 - 显示状态 -->
              <svg v-if="showToken" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <!-- 眼睛关闭图标 - 隐藏状态 -->
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
            </button>
          </div>
          <button
            @click="showTokenHelp = true"
            class="mt-2 text-xs text-blue-400 hover:text-blue-300 underline transition-colors"
          >
            {{ t.tokenDialog.tokenHelp }}
          </button>
        </div>

        <!-- Info Box -->
        <div class="p-4 bg-zinc-800/50 border border-zinc-700/50 rounded-lg">
          <p class="text-xs text-zinc-300 leading-relaxed">
            <strong class="text-white">{{ t.tokenDialog.securityNote }}</strong> {{ t.tokenDialog.securityDesc }}
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-5 bg-zinc-900/50 border-t border-zinc-800 flex justify-between gap-3">
        <Button
          variant="ghost"
          @click="emit('close')"
          class="px-6 text-zinc-400 hover:text-white hover:bg-white/5"
        >
          {{ t.tokenDialog.cancel }}
        </Button>
        <Button
          @click="saveToken"
          :disabled="isSaving || !settings.github_token.trim()"
          class="px-8 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white shadow-lg border-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isSaving ? t.tokenDialog.saving : t.tokenDialog.save }}
        </Button>
      </div>
    </div>
  </div>

  <!-- Token Help Dialog -->
  <div v-if="showTokenHelp" class="fixed inset-0 bg-black/90 backdrop-blur-md z-[70] flex items-center justify-center p-6">
    <div class="w-full max-w-2xl bg-zinc-950 border border-blue-500/30 rounded-xl overflow-hidden shadow-[0_0_50px_rgba(59,130,246,0.2)]">
      <div class="p-5 border-b border-blue-500/20 bg-blue-500/5">
        <h3 class="text-xl font-bold text-blue-400">{{ t.tokenDialog.helpDialog.title }}</h3>
      </div>
      
      <div class="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
        <div>
          <h4 class="text-base font-bold text-white mb-2">{{ t.tokenDialog.helpDialog.step1Title }}</h4>
          <p class="text-sm text-zinc-300">{{ t.tokenDialog.helpDialog.step1Desc }}</p>
        </div>
        
        <div>
          <h4 class="text-base font-bold text-white mb-2">{{ t.tokenDialog.helpDialog.step2Title }}</h4>
          <p class="text-sm text-zinc-300">{{ t.tokenDialog.helpDialog.step2Desc }}</p>
        </div>
        
        <div>
          <h4 class="text-base font-bold text-white mb-2">{{ t.tokenDialog.helpDialog.step3Title }}</h4>
          <div class="bg-zinc-900 border border-zinc-700 rounded-lg p-3 space-y-1 text-xs">
            <div class="flex items-center gap-2">
              <span class="text-green-400 font-semibold">✓ repo</span>
              <span class="text-zinc-400">{{ t.tokenDialog.helpDialog.repoPermission }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-green-400 font-semibold">✓ workflow</span>
              <span class="text-zinc-400">{{ t.tokenDialog.helpDialog.workflowPermission }}</span>
            </div>
          </div>
        </div>
        
        <div>
          <h4 class="text-base font-bold text-white mb-2">{{ t.tokenDialog.helpDialog.step4Title }}</h4>
          <p class="text-sm text-zinc-300">{{ t.tokenDialog.helpDialog.step4Desc }}</p>
        </div>
        
        <div class="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <p class="text-sm text-amber-200">{{ t.tokenDialog.helpDialog.warning }}</p>
        </div>
      </div>
      
      <div class="p-5 bg-zinc-900/50 border-t border-zinc-800 flex justify-between gap-3">
        <Button
          @click="openGithubSettings"
          class="bg-blue-600 hover:bg-blue-500 text-white px-6"
        >
          {{ t.tokenDialog.helpDialog.openBtn }}
        </Button>
        <Button
          variant="ghost"
          @click="showTokenHelp = false"
          class="text-zinc-300 hover:text-white hover:bg-white/10"
        >
          {{ t.tokenDialog.helpDialog.closeBtn }}
        </Button>
      </div>
    </div>
  </div>

  <!-- Success Dialog -->
  <Transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="opacity-0 scale-90"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition-all duration-200 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-90"
  >
    <div v-if="showSuccessDialog" class="fixed inset-0 bg-green-900/20 backdrop-blur-md z-[80] flex items-center justify-center p-4">
      <div class="w-full max-w-sm bg-zinc-950 border border-green-500/50 rounded-xl p-0 overflow-hidden shadow-[0_0_50px_rgba(34,197,94,0.3)]">
        <div class="p-8 flex flex-col items-center text-center">
          <div class="w-16 h-16 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mb-4 shadow-[0_0_40px_rgba(34,197,94,0.4)] animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-green-400 mb-3">{{ t.tokenDialog.dialogButtons.success }}</h3>
          <p class="text-zinc-300 text-sm mb-6 whitespace-pre-line">{{ successMessage }}</p>
          <div class="w-full h-px bg-gradient-to-r from-transparent via-green-500/50 to-transparent mb-6"></div>
          <Button
            @click="showSuccessDialog = false"
            class="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-semibold py-2.5 px-8 shadow-[0_0_30px_rgba(34,197,94,0.3)] border-none transition-all hover:scale-105"
          >
            {{ t.tokenDialog.dialogButtons.confirm }}
          </Button>
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
    <div v-if="showErrorDialog" class="fixed inset-0 bg-red-900/20 backdrop-blur-md z-[80] flex items-center justify-center p-4">
      <div class="w-full max-w-sm bg-zinc-950 border border-red-500/50 rounded-xl p-0 overflow-hidden shadow-[0_0_50px_rgba(239,68,68,0.3)]">
        <div class="p-8 flex flex-col items-center text-center">
          <div class="w-16 h-16 rounded-full bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center mb-4 shadow-[0_0_40px_rgba(239,68,68,0.4)] animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-red-400 mb-3">{{ t.tokenDialog.dialogButtons.error }}</h3>
          <p class="text-zinc-300 text-sm mb-6">{{ errorMessage }}</p>
          <div class="w-full h-px bg-gradient-to-r from-transparent via-red-500/50 to-transparent mb-6"></div>
          <Button
            @click="showErrorDialog = false"
            class="w-full bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-semibold py-2.5 px-8 shadow-[0_0_30px_rgba(239,68,68,0.3)] border-none transition-all hover:scale-105"
          >
            {{ t.tokenDialog.dialogButtons.confirm }}
          </Button>
        </div>
      </div>
    </div>
  </Transition>

  <!-- Confirm Dialog -->
  <Transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="opacity-0 scale-90"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition-all duration-200 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-90"
  >
    <div v-if="showConfirmDialog" class="fixed inset-0 bg-amber-900/20 backdrop-blur-md z-[80] flex items-center justify-center p-4">
      <div class="w-full max-w-sm bg-zinc-950 border border-amber-500/50 rounded-xl p-0 overflow-hidden shadow-[0_0_50px_rgba(245,158,11,0.3)]">
        <div class="p-8 flex flex-col items-center text-center">
          <div class="w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center mb-4 shadow-[0_0_40px_rgba(245,158,11,0.4)] animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-amber-400 mb-3">{{ t.tokenDialog.confirmDialog.title }}</h3>
          <p class="text-zinc-300 text-sm mb-6">{{ t.tokenDialog.confirmDialog.message }}</p>
          <div class="w-full h-px bg-gradient-to-r from-transparent via-amber-500/50 to-transparent mb-6"></div>
          <div class="flex gap-3 w-full">
            <Button
              @click="showConfirmDialog = false"
              variant="ghost"
              class="flex-1 text-zinc-400 hover:text-white hover:bg-white/10"
            >
              {{ t.tokenDialog.confirmDialog.cancel }}
            </Button>
            <Button
              @click="handleConfirmClear"
              class="flex-1 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white font-semibold shadow-[0_0_30px_rgba(245,158,11,0.3)] border-none transition-all hover:scale-105"
            >
              {{ t.tokenDialog.confirmDialog.confirm }}
            </Button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

