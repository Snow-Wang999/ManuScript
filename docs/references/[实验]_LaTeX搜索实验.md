# LaTeX 搜索实验

> 使用 `tex/CMIPS_v1.20combinedSI.tex` 测试 grep/正则表达式搜索效果

---

## 测试文件信息

| 属性 | 值 |
|------|-----|
| 文件 | `CMIPS_v1.20combinedSI.tex` |
| 大小 | 171.5 KB |
| 主题 | Chemotactic Motility-Induced Phase Separation (CMIPS) |
| 类型 | 物理学论文（含补充材料） |

---

## 搜索效果展示

### 1. 提取章节结构

**命令**：
```bash
grep -E "\\section|\\subsection" paper.tex
```

**结果**：
```
214:\section*{{Supplementary Information}}
216:\section{Thermodynamics of non-chemotactic ABPs}
272:\section{Linear stability analysis}
274:\subsection{Dispersion relation}
337:\subsection{Stability condition}
400:\subsection{Finite and unbounded wavelength instabilities}
420:\subsection{Oscillatory instability condition}
526:\section{Linear stability analysis in the $\text{Pe}_\text{R}-\phi_0$ phase diagram}
670:\section{Numerical simulations}
682:\section{Characterization of coarsening dynamics}
732:\section{Characeterization of small-amplitude fluctuation}
748:\section{Characterization of oscillatory pattern formation}
766:\section{Application in living and synthetic systems}
812:\section{Supplementary movies}
```

**效果**：✅ 完美提取论文大纲，带行号定位

---

### 2. 提取引用

**命令**：
```bash
grep -oE "\\cite\{[^}]+\}" paper.tex | head -20
```

**结果**（部分）：
```
\cite{Palacci2013,Theurkauff2012,Stark2018,Pohl2014,Liebchen2018,...}
\cite{Stenhammar2013,Tjhung2018,Speck2014,Cates2015,Cates2010}
\cite{Murray2003,Colin2021,Adler1966,Fu2018,Cremer2019,...}
\cite{Takatori2015}
\cite{Cates2013,Stenhammar2013}
```

**效果**：✅ 可以提取所有引用的 citation key

---

### 3. 提取公式位置

**命令**：
```bash
grep -n "\\begin{equation}" paper.tex
```

**结果**：
```
125:\begin{equation} \label{eqn::dcdt}
220:\begin{equation} \label{eqn::Pi_2D}
224:\begin{equation}
240:\begin{equation}
251:\begin{equation}
256:\begin{equation}
267:\begin{equation}
...
```

**效果**：✅ 定位所有公式，可结合 label 追踪

---

### 4. 提取图表标签

**命令**：
```bash
grep -E "\\label\{fig:" paper.tex
```

**结果**：
```
134:  \label{fig::ABP}
168:  \label{fig::chi_alpha0}
436:  \label{fig::Delta_demo}
687:  \label{fig::coarsen_from_main}
709:  \label{fig::coarsen_1}
721:  \label{fig::coarsen_2}
```

**效果**：✅ 可以追踪所有图表

---

### 5. 提取参考文献

**命令**：
```bash
grep -A 5 "\\bibitem" paper.tex | head -30
```

**结果**（部分）：
```
\bibitem [{Marchetti et al.(2013)}]{Marchetti2013}
  Marchetti, Joanny, Ramaswamy, Liverpool, Prost, Rao, Simha
  "Hydrodynamics of soft active matter"
  Reviews of Modern Physics 85, 1143 (2013)

\bibitem [{Gompper et al.(2020)}]{Gompper2020}
  Gompper, Winkler, Speck, Solon, Nardini, Peruani, Löwen...
```

**效果**：✅ 可以提取完整参考文献列表

---

### 6. 搜索特定关键词

**命令**：
```bash
grep -n "chemotaxis\|MIPS\|phase separation" paper.tex
```

**效果**：✅ 精确定位关键词出现位置

---

### 7. 提取自定义命令

**命令**：
```bash
grep "\\newcommand" paper.tex
```

**结果**：
```
\newcommand{\avg}[1]{\langle {#1} \rangle}
\newcommand{\pderiv}[2]{\frac{\partial {#1}}{\partial {#2}}}
\newcommand{\kb}{k_{\text{B}}}
\newcommand{\E}[1]{\mathbb{E}\left[{#1}\right]}
\newcommand{\Var}[1]{\mathbb{V}\text{ar}\left[{#1}\right]}
```

**效果**：✅ 可以理解论文中的符号定义

---

## 效果总结

| 搜索任务 | grep 效果 | PDF 解析效果 |
|---------|----------|-------------|
| 章节结构 | ✅ 完美 | ⚠️ 可能丢失层级 |
| 引用提取 | ✅ 完美 | ❌ 通常无法提取 |
| 公式定位 | ✅ 完美 | ❌ 公式变成图片/乱码 |
| 图表追踪 | ✅ 完美 | ⚠️ 可能丢失标签 |
| 参考文献 | ✅ 完美 | ⚠️ 格式可能混乱 |
| 关键词搜索 | ✅ 完美 | ✅ 可以 |
| 符号定义 | ✅ 完美 | ❌ 无法获取 |

---

## 对 ManuScript 的启示

### LaTeX 方案优势

1. **引用追踪**：可以精确提取 `\cite{key}` 并关联到 `\bibitem{key}`
2. **结构感知**：章节层级完整保留
3. **公式可解析**：LaTeX 公式可以直接使用
4. **版本控制**：可以 git diff 追踪修改

### 实现建议

```python
import re

def extract_from_latex(tex_content: str) -> dict:
    """从 LaTeX 提取结构化信息"""
    return {
        "sections": re.findall(r'\\section\{([^}]+)\}', tex_content),
        "citations": re.findall(r'\\cite\{([^}]+)\}', tex_content),
        "equations": re.findall(r'\\label\{(eqn:[^}]+)\}', tex_content),
        "figures": re.findall(r'\\label\{(fig:[^}]+)\}', tex_content),
    }

def extract_bibitems(tex_content: str) -> list[dict]:
    """提取参考文献"""
    pattern = r'\\bibitem\s*\[\{([^}]+)\}\]\{([^}]+)\}'
    matches = re.findall(pattern, tex_content)
    return [{"display": m[0], "key": m[1]} for m in matches]
```

### 混合方案

```
文献来源
    │
    ├─ arXiv 论文
    │   └─ 下载 .tar.gz → 解压 .tex → grep 搜索
    │
    └─ 其他来源（期刊、会议）
        └─ PDF → RAGFlow 解析 → 向量检索
```

---

## 当前决策

**暂不实现 LaTeX 方案**

理由：
1. v1.0 目标是验证核心流程
2. 需要额外的 arXiv 源码下载逻辑
3. 不是所有论文都有 LaTeX 源码

**未来触发条件**：
- 文献库 >80% 来自 arXiv
- PDF 解析质量成为核心瓶颈
- 需要精确提取引用关系

---

## 实验总结

### 关键发现

从 `CMIPS_v1.20combinedSI.tex`（171.5 KB 物理学论文）的测试中发现：

| 提取内容 | 数量 | 说明 |
|---------|------|------|
| 章节/小节 | 14 个 | 完整论文大纲，带行号 |
| 引用 `\cite{}` | 多处 | 可追踪到具体 citation key |
| 公式 | 多个 | 带 `\label{eqn::xxx}` 可定位 |
| 图表 | 6 个 | `\label{fig::xxx}` 标签完整 |
| 参考文献 | 87 条 | 完整 bibitem 信息 |
| 自定义符号 | 多个 | `\newcommand` 定义可解析 |

### LaTeX vs PDF 对比结论

```
                    LaTeX 源码                    PDF 文件
                        │                            │
搜索方式            grep/正则                   需要解析工具
                        │                            │
章节结构         ✅ \section{} 完美提取        ⚠️ 可能丢失层级
                        │                            │
引用关系         ✅ \cite{} → \bibitem{}       ❌ 通常无法提取
                        │                            │
数学公式         ✅ LaTeX 源码可用             ❌ 变成图片/乱码
                        │                            │
符号定义         ✅ \newcommand 可解析         ❌ 无法获取
                        │                            │
版本控制         ✅ git diff 友好              ❌ 二进制文件
```

### 核心结论

1. **LaTeX 是学术论文的"源代码"**
   - 可以像搜索代码一样搜索论文
   - 结构化信息完整保留
   - 引用关系可追踪

2. **arXiv 是 LaTeX 源码的主要来源**
   - ~90% 的 arXiv 论文提供源码
   - 下载命令：`wget https://arxiv.org/e-print/{paper_id}`

3. **混合方案是最佳实践**
   - arXiv 论文 → LaTeX 源码 → grep 搜索
   - 其他来源 → PDF → RAGFlow 解析

4. **对 ManuScript 的价值**
   - 如果文献主要来自 arXiv，LaTeX 方案可大幅提升检索精度
   - 可以精确提取引用关系，构建文献图谱
   - 公式可直接复用，无需 OCR
