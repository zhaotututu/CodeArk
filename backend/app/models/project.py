from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
import json

class ProjectConfig(SQLModel):
    auto_push: bool = True
    sync_mode: str = "auto"  # auto, interval, fixed
    sync_interval: int = 300 # seconds for interval mode
    sync_fixed_time: str = "00:00" # HH:MM for fixed mode
    max_file_size_mb: int = 50
    blocked_extensions: list[str] = ['.exe', '.dll', '.zip', '.mp4']
    ignore_hidden: bool = True
    ai_commit_message: bool = False
    default_commit_prefix: str = "backup: "
    is_private: bool = True
    strip_secrets: bool = True

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    path: str = Field(index=True, unique=True)
    remote_url: Optional[str] = None
    branch: str = "main"
    
    config_json: str = Field(default="{}")
    
    last_sync_time: Optional[datetime] = None
    status: str = "idle" 

    @property
    def config(self) -> ProjectConfig:
        try:
            return ProjectConfig(**json.loads(self.config_json))
        except:
            return ProjectConfig()

    def set_config(self, config: ProjectConfig):
        self.config_json = config.model_dump_json()

class ProjectCreate(SQLModel):
    path: str
    name: Optional[str] = None

class ProjectUpdate(SQLModel):
    name: Optional[str] = None
    config: Optional[ProjectConfig] = None

# 响应模型：包含 config 属性
class ProjectResponse(SQLModel):
    id: Optional[int] = None
    name: str
    path: str
    remote_url: Optional[str] = None
    branch: str
    last_sync_time: Optional[datetime] = None
    status: str
    config: ProjectConfig

# 新增：自动初始化请求模型
class ProjectAutoInit(SQLModel):
    path: str
    name: str
    description: Optional[str] = None  # Repository description
    github_token: Optional[str] = None  # Optional, will use global settings if not provided
    is_private: bool = True
    lang: str = "zh"  # 日志语言: 'zh' 或 'en'
    gitignore_content: Optional[str] = None  # 自定义 .gitignore 内容
