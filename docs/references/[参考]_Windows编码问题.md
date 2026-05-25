# 编码问题总结
    # 问题现象
运行 Python 时报错：


SyntaxError: invalid syntax
中文字符显示为乱码："��δ�ҵ���"（实际是 "未找到"）

根本原因
Windows 默认编码是 GBK (CP936)，不是 UTF-8

Python 文件保存时的编码与读取时不匹配：

文件可能以 GBK 保存
但 Python 3 默认假设 UTF-8
或者文件以 UTF-8 保存，但终端/编辑器用 GBK 读取
编辑器/工具链的问题：

某些编辑器可能自动转换编码
复制粘贴代码时可能引入编码问题
如何避免
1. 始终在 Python 文件开头声明编码：


# -*- coding: utf-8 -*-
这是第一行（或第二行，如果有 shebang）

2. 确保编辑器使用 UTF-8 保存：

VS Code 设置：


{
  "files.encoding": "utf8",
  "files.autoGuessEncoding": false
}
3. 检查文件实际编码：


# PowerShell 查看文件编码
Get-Content -Path "file.py" -Encoding Byte | Format-Hex
4. 在代码中避免中文字符串（推荐）：


# 不推荐（可能有编码问题）
return f"(未找到相关文献: {section_title})"

# 推荐（使用英文）
return f"(No relevant documents found for section: {section_title})"
5. 如果必须用中文，使用 logging 配置：


import sys
sys.stdout.reconfigure(encoding='utf-8')
快速修复方法
如果遇到编码问题，最可靠的方式是：

用 Claude Code 的 Write 工具重写整个文件（强制 UTF-8）
或者在 VS Code 中：Ctrl+Shift+P → Change File Encoding → Save with Encoding → UTF-8