import os

class IgnoreService:
    @staticmethod
    def add_to_gitignore(project_path: str, rel_path: str):
        gitignore_path = os.path.join(project_path, ".gitignore")
        
        # 确保文件以换行符结束
        needs_newline = False
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    # 读取最后几个字符判断是否需要换行
                    f.seek(0, os.SEEK_END)
                    if f.tell() > 0:
                        f.seek(f.tell() - 1, os.SEEK_SET)
                        if f.read(1) != '\n':
                            needs_newline = True
            except:
                # 如果读取失败或空文件，安全起见加换行
                needs_newline = True
        
        with open(gitignore_path, "a", encoding="utf-8") as f:
            if needs_newline:
                f.write("\n")
            f.write(f"{rel_path}\n")
            
    @staticmethod
    def get_gitignore_content(project_path: str) -> str:
        gitignore_path = os.path.join(project_path, ".gitignore")
        if not os.path.exists(gitignore_path):
            return ""
        with open(gitignore_path, "r", encoding="utf-8") as f:
            return f.read()
            
    @staticmethod
    def save_gitignore_content(project_path: str, content: str):
        gitignore_path = os.path.join(project_path, ".gitignore")
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(content)

