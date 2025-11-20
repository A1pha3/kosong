#!/usr/bin/env python3
"""
文档格式修复脚本

自动修复文档格式问题：
- 为代码块添加语言标记
- 修复标题层级跳跃（可选，需要手动审查）
"""

import re
from pathlib import Path
from typing import List, Tuple


class DocFixer:
    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)
        self.fixed_files = []
    
    def fix_all(self, dry_run: bool = False) -> List[str]:
        """修复所有文档文件"""
        md_files = list(self.docs_dir.rglob("*.md"))
        
        for md_file in md_files:
            if self.fix_file(md_file, dry_run):
                self.fixed_files.append(str(md_file))
        
        return self.fixed_files
    
    def fix_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """修复单个文档文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            
            # 修复代码块语言标记
            content = self.fix_code_blocks(content, file_path)
            
            # 如果内容有变化，写回文件
            if content != original_content:
                if not dry_run:
                    file_path.write_text(content, encoding="utf-8")
                    print(f"✅ 已修复: {file_path}")
                else:
                    print(f"🔍 需要修复: {file_path}")
                return True
            
            return False
        
        except Exception as e:
            print(f"❌ 错误处理 {file_path}: {e}")
            return False
    
    def fix_code_blocks(self, content: str, file_path: Path) -> str:
        """为代码块添加语言标记"""
        lines = content.split("\n")
        fixed_lines = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            # 检查是否是代码块标记
            if line.strip().startswith("```"):
                if not in_code_block:
                    # 代码块开始
                    lang_marker = line.strip()[3:].strip()
                    
                    if not lang_marker:
                        # 没有语言标记，尝试推断
                        lang = self.infer_language(lines, i, file_path)
                        fixed_lines.append(f"```{lang}")
                        in_code_block = True
                    else:
                        # 已有语言标记
                        fixed_lines.append(line)
                        in_code_block = True
                else:
                    # 代码块结束
                    fixed_lines.append(line)
                    in_code_block = False
            else:
                fixed_lines.append(line)
        
        return "\n".join(fixed_lines)
    
    def infer_language(self, lines: List[str], start_idx: int, file_path: Path) -> str:
        """推断代码块的语言"""
        # 查看代码块内容来推断语言
        code_lines = []
        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip().startswith("```"):
                break
            code_lines.append(lines[i])
        
        code_content = "\n".join(code_lines).strip()
        
        # 如果是空代码块（通常是输出示例）
        if not code_content:
            # 检查前面的上下文
            context_before = ""
            for i in range(max(0, start_idx - 3), start_idx):
                context_before += lines[i].lower()
            
            if "输出" in context_before or "结果" in context_before or "output" in context_before.lower():
                return "text"
            return "text"
        
        # Python 代码特征
        python_patterns = [
            r'^\s*import\s+',
            r'^\s*from\s+\w+\s+import',
            r'^\s*def\s+\w+\s*\(',
            r'^\s*class\s+\w+',
            r'^\s*async\s+def',
            r'^\s*await\s+',
            r'asyncio\.run\(',
            r'print\(',
        ]
        
        for pattern in python_patterns:
            if re.search(pattern, code_content, re.MULTILINE):
                return "python"
        
        # Bash/Shell 命令特征
        bash_patterns = [
            r'^\s*\$\s+',
            r'^\s*#\s+',
            r'^\s*(git|cd|ls|mkdir|pip|uv|make|pytest)\s+',
        ]
        
        for pattern in bash_patterns:
            if re.search(pattern, code_content, re.MULTILINE):
                return "bash"
        
        # JSON 特征
        if code_content.strip().startswith('{') or code_content.strip().startswith('['):
            try:
                # 简单检查是否像 JSON
                if '"' in code_content and ':' in code_content:
                    return "json"
            except:
                pass
        
        # Mermaid 图表特征
        if any(keyword in code_content for keyword in ['graph', 'sequenceDiagram', 'classDiagram', 'flowchart']):
            return "mermaid"
        
        # 默认为 text（用于输出示例等）
        return "text"
    
    def print_summary(self) -> None:
        """打印修复摘要"""
        if not self.fixed_files:
            print("\n✅ 没有需要修复的文件")
        else:
            print(f"\n✅ 共修复 {len(self.fixed_files)} 个文件")


def main():
    import sys
    
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 预览模式（不会实际修改文件）\n")
    
    fixer = DocFixer()
    fixer.fix_all(dry_run=dry_run)
    fixer.print_summary()
    
    if dry_run:
        print("\n提示：运行 'python scripts/fix_docs_format.py' 来实际修复文件")


if __name__ == "__main__":
    main()
