# ManuScript v0.1 - 最小可运行原型

## 目标

用最少的代码验证核心技术可行性：
1. RAGFlow API 连通性
2. OpenAI API 调用
3. 生成带引用标记的文本

## 运行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 运行核心脚本（无 UI）
python prototype.py

# 运行 Gradio UI
python main.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| config.py | 配置管理（读取 .env） |
| logger.py | 日志配置 |
| prototype.py | 核心脚本（先开发） |
| main.py | Gradio UI（后开发） |

## 验收标准

- [ ] prototype.py 能成功调用 RAGFlow 检索
- [ ] prototype.py 能成功调用 OpenAI 生成
- [ ] 生成文本包含 [1], [2] 引用标记
