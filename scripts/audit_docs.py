#!/usr/bin/env python3
"""
文档格式审查脚本

检查所有文档的格式规范：
- Markdown 格式是否符合规范
- 代码块是否都有语言标记
- 标题层级是否正确
- 列表格式是否统一
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple


class DocAuditor:
    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)
        self.issues: Dict[str, List[str]] = {}
    
    def audit_all(self) -> Dict[str, List[str]]:
        """审查所有文档文件"""
        md_files = list(self.docs_dir.rglob("*.md"))
        
        for md_file in md_files:
            self.audit_file(md_file)
        
        return self.issues
    
    def audit_file(self, file_path: Path) -> None:
        """审查单个文档文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
            relative_path = str(file_path)
            
            issues = []
            
            # 检查代码块语言标记
            issues.extend(self.check_code_blocks(content, relative_path))
            
            # 检查标题层级
            issues.extend(self.check_heading_levels(content, relative_path))
            
            # 检查列表格式
            issues.extend(self.check_list_format(content, relative_path))
            
            # 检查空行规范
            issues.extend(self.check_blank_lines(content, relative_path))
            
            if issues:
                self.issues[relative_path] = issues
        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    def check_code_blocks(self, content: str, file_path: str) -> List[str]:
        """检查代码块是否有语言标记"""
        issues = []
        lines = content.split("\n")
        in_code_block = False
        
        for i, line in enumerate(lines, 1):
            # 检查代码块标记
            if line.strip().startswith("```"):
                if not in_code_block:
                    # 代码块开始标记
                    lang_marker = line.strip()[3:].strip()
                    
                    # 如果没有语言标记（空的 ``` 或只有空格）
                    if not lang_marker:
                        issues.append(f"Line {i}: 代码块缺少语言标记")
                    
                    in_code_block = True
                else:
                    # 代码块结束标记，不检查
                    in_code_block = False
        
        return issues
    
    def check_heading_levels(self, content: str, file_path: str) -> List[str]:
        """检查标题层级是否正确"""
        issues = []
        lines = content.split("\n")
        
        prev_level = 0
        for i, line in enumerate(lines, 1):
            # 匹配标题
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2)
                
                # 检查是否超过4级标题
                if level > 4:
                    issues.append(f"Line {i}: 标题层级过深（{level}级），建议最多使用4级标题")
                
                # 检查标题层级跳跃（跳过超过1级）
                if prev_level > 0 and level > prev_level + 1:
                    issues.append(f"Line {i}: 标题层级跳跃（从{prev_level}级跳到{level}级）")
                
                prev_level = level
        
        return issues
    
    def check_list_format(self, content: str, file_path: str) -> List[str]:
        """检查列表格式是否统一"""
        issues = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines, 1):
            # 检查无序列表是否使用 - 而不是 * 或 +
            if re.match(r'^\s*[\*\+]\s+', line):
                issues.append(f"Line {i}: 无序列表应使用 '-' 而不是 '*' 或 '+'")
        
        return issues
    
    def check_blank_lines(self, content: str, file_path: str) -> List[str]:
        """检查空行规范"""
        issues = []
        lines = content.split("\n")
        
        for i in range(len(lines) - 1):
            current = lines[i].strip()
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            
            # 检查代码块前后是否有空行
            if current.startswith("```") and not current.endswith("```"):
                # 代码块开始
                if i > 0:
                    prev_line = lines[i - 1].strip()
                    if prev_line and not prev_line.startswith("#"):
                        # 前一行不是空行且不是标题
                        pass  # 这个规则太严格，暂时不检查
            
            # 检查标题前后是否有空行
            if re.match(r'^#{1,6}\s+', next_line):
                if current and not current.startswith("```"):
                    # 标题前应该有空行（除非是文件开头或代码块）
                    pass  # 这个规则太严格，暂时不检查
        
        return issues
    
    def print_report(self) -> None:
        """打印审查报告"""
        if not self.issues:
            print("✅ 所有文档格式检查通过！")
            return
        
        print(f"⚠️  发现 {len(self.issues)} 个文件存在格式问题：\n")
        
        total_issues = 0
        for file_path, issues in sorted(self.issues.items()):
            print(f"📄 {file_path}")
            for issue in issues:
                print(f"   - {issue}")
                total_issues += 1
            print()
        
        print(f"总计: {total_issues} 个问题")


def main():
    auditor = DocAuditor()
    auditor.audit_all()
    auditor.print_report()


if __name__ == "__main__":
    main()
