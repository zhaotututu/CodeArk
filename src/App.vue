<script setup lang="ts">
import { ref, provide } from 'vue';
import Dashboard from './views/Dashboard.vue';
import ProjectSettings from './views/ProjectSettings.vue';

type ViewType = 'dashboard' | 'settings';

const currentView = ref<ViewType>('dashboard');
const currentProjectId = ref<number | null>(null);

const showSettings = (projectId: number) => {
  currentProjectId.value = projectId;
  currentView.value = 'settings';
};

const showDashboard = () => {
  currentView.value = 'dashboard';
  currentProjectId.value = null;
};

// Provide to child components
provide('showSettings', showSettings);
provide('showDashboard', showDashboard);
</script>

<template>
  <Dashboard v-if="currentView === 'dashboard'" />
  <ProjectSettings v-else-if="currentView === 'settings'" :project-id="currentProjectId" />
</template>
