import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useLocaleStore } from './locale';

export const useLogStore = defineStore('logs', () => {
  const logs = ref<Array<{ time: string; msg: string; level: string; project_id?: number }>>([]);
  const isConnected = ref(false);
  let ws: WebSocket | null = null;

  const connect = () => {
    if (ws) return;
    ws = new WebSocket('ws://localhost:8000/ws/logs');
    ws.onopen = () => {
      isConnected.value = true;
      const localeStore = useLocaleStore();
      addLog('System', localeStore.t.log.connectedToLogStream, 'success');
    };
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        logs.value.push(data);
        if (logs.value.length > 100) logs.value.shift();
      } catch (e) {
        console.error(e);
      }
    };
    ws.onclose = () => {
      isConnected.value = false;
      ws = null;
      setTimeout(connect, 3000);
    };
  };

  const addLog = (time: string, msg: string, level: string) => {
    logs.value.push({ time, msg, level });
    if (logs.value.length > 100) logs.value.shift();
  };

  return { logs, isConnected, connect };
});

