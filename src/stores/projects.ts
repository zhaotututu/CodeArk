import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface ProjectConfig {
    auto_push: boolean;
    sync_mode: 'interval' | 'fixed';
    sync_interval: number;
    sync_fixed_time: string;
    max_file_size_mb: number;
    blocked_extensions: string[];
    ignore_hidden: boolean;
    ai_commit_message: boolean;
    default_commit_prefix: string;
    is_private: boolean;
}

export interface Project {
    id: number;
    name: string;
    path: string;
    remote_url: string | null;
    branch: string;
    status: string;
    last_sync_time: string | null;
    config?: ProjectConfig;
}

export interface AutoInitData {
    path: string;
    name: string;
    description?: string;  // Repository description (optional)
    github_token?: string;  // Optional, will use global settings if not provided
    is_private: boolean;
    lang?: string;  // 语言参数: 'zh' 或 'en'
    gitignore_content?: string;  // 自定义 .gitignore 内容
}

export const useProjectStore = defineStore('projects', () => {
    const projects = ref<Project[]>([]);

    const fetchProjects = async () => {
        const res = await fetch('/api/projects/');
        if (res.ok) {
            projects.value = await res.json();
        }
    };

    const addProject = async (path: string) => {
        const res = await fetch('/api/projects/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        if (res.ok) {
            await fetchProjects();
            return await res.json();
        }
        throw new Error((await res.json()).detail);
    };
    
    const autoInitProject = async (data: AutoInitData) => {
        const res = await fetch('/api/projects/auto-init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            await fetchProjects();
            return await res.json();
        }
        throw new Error((await res.json()).detail);
    }

    const getConfig = async (id: number) => {
        const res = await fetch(`/api/projects/${id}/config`);
        return await res.json();
    };

    const updateConfig = async (id: number, config: ProjectConfig) => {
        const res = await fetch(`/api/projects/${id}/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to update config');
        }
        
        return res.ok;
    };
    
    const scanProject = async (id: number, lang: string = 'zh') => {
         const res = await fetch(`/api/projects/${id}/scan?lang=${lang}`, { method: 'POST' });
         return await res.json();
    }
    
    const ignoreFiles = async (id: number, files: string[]) => {
        const res = await fetch(`/api/projects/${id}/ignore`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(files)
        });
        return res.ok;
    }
    
    const manualPush = async (id: number, lang: string = 'zh') => {
        const res = await fetch(`/api/projects/${id}/manual-push?lang=${lang}`, { method: 'POST' });
        if (!res.ok) {
            throw new Error((await res.json()).detail || 'Failed to push');
        }
        return await res.json();
    }

    return { projects, fetchProjects, addProject, autoInitProject, getConfig, updateConfig, scanProject, ignoreFiles, manualPush };
});
