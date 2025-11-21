import os
from typing import List, Dict, Any, Set
from pathlib import Path
from app.models.project import ProjectConfig

class ScanResult:
    def __init__(self, safe: bool, risks: List[Dict[str, Any]]):
        self.safe = safe
        self.risks = risks

class ScannerService:
    @staticmethod
    def scan_directory(path: str, config: ProjectConfig, changed_files: List[str]) -> ScanResult:
        risks = []
        root_path = Path(path)
        
        # 将配置转换为集合以提高查找速度
        blocked_exts = set(ext.lower() for ext in config.blocked_extensions)
        max_size_bytes = config.max_file_size_mb * 1024 * 1024
        
        for file_rel_path in changed_files:
            # 忽略 .git 目录下的变化（通常 git status 不会返回这个，但双重保险）
            if file_rel_path.startswith(".git"):
                continue

            # 忽略隐藏文件（如果配置开启）
            if config.ignore_hidden and os.path.basename(file_rel_path).startswith("."):
                # 特殊处理：.gitignore 是允许的
                if os.path.basename(file_rel_path) != ".gitignore":
                    continue

            full_path = root_path / file_rel_path
            
            if not full_path.exists() or full_path.is_dir():
                continue
                
            # 1. 检查大小
            try:
                size = full_path.stat().st_size
                if size > max_size_bytes:
                    risks.append({
                        "path": file_rel_path,
                        "size_display": f"{size / 1024 / 1024:.2f} MB",
                        "size_bytes": size,
                        "reason": f"Exceeds {config.max_file_size_mb}MB limit",
                        "type": "size_limit"
                    })
                    continue
            except OSError:
                continue 

            # 2. 检查扩展名
            if full_path.suffix.lower() in blocked_exts:
                 risks.append({
                        "path": file_rel_path,
                        "size_display": f"{size / 1024 / 1024:.2f} MB",
                        "size_bytes": size,
                        "reason": "File type blocked by policy",
                        "type": "extension_block"
                    })

        return ScanResult(safe=len(risks) == 0, risks=risks)

