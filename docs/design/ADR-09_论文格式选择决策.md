# 论文格式决策

> 分析不同论文格式的可搜索性，为 ManuScript 选择最优的文献处理方案

---

## 格式可搜索性对比

| 格式 | 可 grep/正则 | 结构化程度 | 获取难度 | 说明 |
|------|-------------|-----------|---------|------|
| **LaTeX (.tex)** | ✅ 完美 | ✅ 高 | ⚠️ 需要源码 | 最接近代码的格式 |
| **Markdown (.md)** | ✅ 完美 | ✅ 高 | ❌ 论文很少用 | 理想但不现实 |
| **HTML** | ✅ 可以 | ⚠️ 有标签噪音 | ⚠️ 部分期刊提供 | 需要清理标签 |
| **纯文本 (.txt)** | ✅ 可以 | ❌ 无结构 | ⚠️ 需转换 | 丢失格式信息 |
| **PDF** | ❌ 不行 | ❌ 二进制 | ✅ 最常见 | 需要解析工具 |
| **DOCX** | ❌ 不行 | ❌ 压缩XML | ⚠️ 部分期刊 | 需要解压+解析 |

---

## 论文格式的生命周期

### 为什么我们下载的都是 PDF？

论文从写作到发布经历格式转换：

```
作者写作          提交审稿           出版发布          读者获取
   │                │                  │                │
   ▼                ▼                  ▼                ▼
LaTeX/Word  →  LaTeX/Word/PDF  →  PDF (最终版)  →  PDF (下载)
   │                │                  │                │
 源文件           源文件            排版后            只有PDF
```

### PDF 成为发布标准的原因

| 原因 | 说明 |
|------|------|
| **版权保护** | PDF 难以编辑，保护出版商和作者权益 |
| **格式统一** | 不同设备/系统显示一致 |
| **排版固定** | 保留精确的页面布局、字体、公式渲染 |
| **防止篡改** | 确保内容完整性 |

### 能否获取 LaTeX/Word 源文件？

| 来源 | LaTeX 源码 | Word 源文件 | 说明 |
|------|-----------|------------|------|
| **arXiv** | ✅ 可以 | ❌ 不行 | 下载 "Other formats" → Source |
| **期刊官网** | ❌ 不行 | ❌ 不行 | 只提供 PDF |
| **作者主页/GitHub** | ⚠️ 偶尔 | ❌ 极少 | 部分作者开源 |
| **直接联系作者** | ⚠️ 可能 | ⚠️ 可能 | 需要邮件请求 |

> **结论**：arXiv 是唯一的大规模 LaTeX 源码来源（约 200 万篇论文）

### 实际提交格式 vs 最终发布格式

| 出版商 | 作者提交格式 | 最终发布格式 |
|--------|------------|------------|
| **arXiv** | LaTeX (推荐) / PDF | PDF + 源码可下载 |
| **IEEE** | LaTeX / Word | PDF |
| **ACM** | LaTeX (主要) | PDF |
| **Elsevier** | LaTeX / Word | PDF |
| **Nature/Science** | Word (主要) | PDF + HTML |
| **医学期刊** | Word | PDF |

---

## 最佳选择：LaTeX 源码

LaTeX 是纯文本格式，可以像代码一样搜索：

```bash
# 搜索关键词
grep -r "attention mechanism" *.tex

# 用正则提取引用
grep -E "\\cite\{.*transformer.*\}" paper.tex

# 查看某章节内容
grep -A 5 "\\section\{Method\}" paper.tex
```

### LaTeX 的优势

- 纯文本，grep/sed/awk 全部可用
- 结构化标记（`\section{}`, `\cite{}`, `\begin{equation}`）
- 可以用正则提取引用、公式、章节
- 版本控制友好（可以 git diff）

### LaTeX 结构示例

```latex
\section{Introduction}           % 章节标记
\label{sec:intro}                % 可引用标签

Recent advances in \textbf{deep learning}...

\cite{vaswani2017attention}      % 引用标记
\ref{fig:architecture}           % 图表引用

\begin{equation}                 % 公式环境
  E = mc^2
\end{equation}
```

---

## 如何获取 LaTeX 源码

| 来源 | 方法 | 覆盖率 |
|------|------|--------|
| **arXiv** | 下载 `.tar.gz` 源码包 | ~90% 论文有源码 |
| **GitHub** | 搜索论文标题 | 部分作者开源 |
| **Overleaf** | 如果有访问权限 | 需要授权 |
| **作者主页** | 直接联系或下载 | 不稳定 |

### arXiv 源码下载示例

```bash
# 下载源码包
wget https://arxiv.org/e-print/2301.12345

# 解压
tar -xzf 2301.12345

# 搜索内容
grep -r "your keyword" *.tex

# 提取所有引用
grep -oE "\\cite\{[^}]+\}" *.tex | sort | uniq
```

---

## 各领域 LaTeX 普及率

| 领域 | LaTeX 普及率 | 主要来源 | 说明 |
|------|-------------|---------|------|
| **物理学** | ✅ ~95% | arXiv | 几乎全部用 LaTeX |
| **数学** | ✅ ~95% | arXiv | 公式多，必须用 LaTeX |
| **计算机科学** | ✅ ~85% | arXiv, ACL, NeurIPS | AI/ML 领域尤其高 |
| **天文学** | ✅ ~90% | arXiv | 传统 LaTeX 领域 |
| **工程学** | ⚠️ ~50% | IEEE, arXiv | 部分用 Word |
| **化学** | ⚠️ ~40% | ACS, RSC | 混合使用 |
| **生物医学** | ❌ ~10% | PubMed, PMC | 主要用 Word |
| **社会科学** | ❌ ~5% | SSRN | 几乎全用 Word |
| **人文学科** | ❌ ~2% | 各期刊 | Word 为主 |
| **商业/管理** | ❌ ~5% | SSRN | Word 为主 |

---

### 详细格式使用情况（补充）

#### 按学科领域细分

| 领域 | LaTeX | Word | 其他格式 | 主要投稿平台/期刊 | 说明 |
|------|-------|------|---------|-----------------|------|
| **理论物理** | ~98% | ~2% | - | arXiv, Physical Review, JHEP | 公式密集，LaTeX 几乎是唯一选择 |
| **实验物理** | ~90% | ~10% | - | arXiv, Nature Physics, PRL | 部分实验组使用 Word |
| **纯数学** | ~99% | ~1% | - | arXiv, Annals of Math, Inventiones | 数学符号要求极高 |
| **应用数学** | ~90% | ~10% | - | SIAM journals, arXiv | 工业界合作论文偶用 Word |
| **统计学** | ~75% | ~25% | - | JASA, Annals of Statistics | R Markdown 也在增长 |
| **机器学习/AI** | ~95% | ~5% | - | NeurIPS, ICML, ICLR, arXiv | 顶会强制要求 LaTeX |
| **计算机理论** | ~95% | ~5% | - | STOC, FOCS, arXiv | 算法/证明需要 LaTeX |
| **系统/网络** | ~70% | ~30% | - | OSDI, NSDI, SIGCOMM | 部分接受 Word |
| **HCI/软件工程** | ~50% | ~50% | - | CHI, ICSE, FSE | 两种格式均常见 |
| **天文学** | ~95% | ~5% | - | ApJ, MNRAS, A&A, arXiv | 传统 LaTeX 领域 |
| **理论化学** | ~60% | ~40% | - | JCP, JCTC | 计算化学偏向 LaTeX |
| **有机/无机化学** | ~30% | ~70% | - | JACS, Angew. Chem. | ACS 期刊 Word 友好 |
| **材料科学** | ~50% | ~50% | - | Nature Materials, Adv. Mater. | 跨学科，两者均用 |
| **电气工程** | ~60% | ~40% | - | IEEE Trans., arXiv | IEEE 两种模板都提供 |
| **机械工程** | ~40% | ~60% | - | ASME journals | 工业界偏好 Word |
| **土木工程** | ~20% | ~80% | - | ASCE journals | Word 为主 |
| **分子生物学** | ~15% | ~85% | - | Cell, Nature, Science | 实验为主，Word 足够 |
| **临床医学** | ~5% | ~95% | - | NEJM, Lancet, JAMA | Word 是标准 |
| **公共卫生** | ~5% | ~95% | - | BMJ, PLOS Medicine | Word 为主 |
| **神经科学** | ~20% | ~80% | - | Neuron, Nature Neuro | 计算神经科学用 LaTeX |
| **生态学** | ~15% | ~85% | - | Ecology, Ecol. Letters | Word 为主 |
| **心理学** | ~10% | ~90% | - | Psych. Review, JPSP | APA 格式用 Word |
| **经济学** | ~70% | ~30% | - | AER, Econometrica, QJE | 计量经济学偏 LaTeX |
| **金融学** | ~40% | ~60% | - | JF, RFS, JFE | 学术界用 LaTeX 较多 |
| **政治学** | ~15% | ~85% | - | APSR, JOP | Word 为主 |
| **社会学** | ~5% | ~95% | - | ASR, AJS | Word 为主 |
| **法学** | ~2% | ~98% | - | Yale LJ, Harvard LR | Word 是标准 |
| **历史学** | ~2% | ~98% | - | AHR, Past & Present | Word 为主 |
| **文学/语言学** | ~5% | ~95% | - | PMLA, Language | Word 为主 |
| **哲学** | ~20% | ~80% | - | Phil. Review, Mind | 逻辑学分支用 LaTeX |

#### 按出版商/平台分类

| 出版商/平台 | LaTeX 支持 | Word 支持 | 推荐格式 | 备注 |
|------------|-----------|----------|---------|------|
| **arXiv** | ✅ 强烈推荐 | ❌ 仅 PDF | LaTeX | ~90% 提交为 LaTeX 源码 |
| **IEEE** | ✅ 模板提供 | ✅ 模板提供 | 均可 | 两种格式使用率约 50/50 |
| **ACM** | ✅ 官方模板 | ⚠️ 有限支持 | LaTeX | 计算机领域标准 |
| **Elsevier** | ✅ elsarticle | ✅ 完全支持 | 均可 | 3000+ 期刊，格式因刊而异 |
| **Springer Nature** | ✅ 模板提供 | ✅ 完全支持 | 均可 | Nature 系列偏好 Word |
| **Wiley** | ✅ 支持 | ✅ 完全支持 | Word | 大多数期刊偏好 Word |
| **ACS** | ✅ achemso | ✅ 完全支持 | Word | 化学领域 Word 更常见 |
| **RSC** | ✅ 支持 | ✅ 完全支持 | Word | 类似 ACS |
| **PLOS** | ✅ 支持 | ✅ 完全支持 | Word | 开放获取，Word 更常见 |
| **MDPI** | ✅ 模板提供 | ✅ 完全支持 | LaTeX | 提供两种模板 |
| **Frontiers** | ⚠️ 有限 | ✅ 完全支持 | Word | 在线编辑系统 |

#### 按会议类型分类（计算机科学）

| 会议类型 | LaTeX 要求 | 代表会议 | 说明 |
|---------|-----------|---------|------|
| **ML/AI 顶会** | 强制 | NeurIPS, ICML, ICLR, AAAI | 必须使用官方 LaTeX 模板 |
| **NLP 顶会** | 强制 | ACL, EMNLP, NAACL | ACL 格式强制 LaTeX |
| **CV 顶会** | 强制 | CVPR, ICCV, ECCV | 必须 LaTeX |
| **理论顶会** | 强制 | STOC, FOCS, SODA | 必须 LaTeX |
| **系统顶会** | 推荐 | OSDI, SOSP, NSDI | LaTeX 推荐但非强制 |
| **数据库顶会** | 推荐 | SIGMOD, VLDB | 两种均可 |
| **网络顶会** | 推荐 | SIGCOMM, IMC | 两种均可 |
| **HCI 顶会** | 均可 | CHI, UIST | Word 也常见 |

#### 新兴格式

| 格式 | 当前采用率 | 主要用户群 | 趋势 |
|-----|-----------|-----------|------|
| **Typst** | <1% | LaTeX 替代探索者 | 📈 快速增长中 |
| **R Markdown** | ~5% (统计学) | 统计学家、数据科学家 | 📈 稳定增长 |
| **Jupyter Notebook** | ~3% | 计算科学、ML | 📈 作为补充材料 |
| **Quarto** | <1% | 数据科学 | 📈 新兴 |
| **Google Docs** | <1% | 协作草稿 | ➡️ 仅用于初稿 |

#### 数据来源

以上数据综合自：
- [arXiv 投稿指南](https://info.arxiv.org/help/submit/index.html) - LaTeX 为主要格式
- [IEEE 会议模板](https://www.ieee.org/conferences/publishing/templates.html) - 提供 Word 和 LaTeX
- [Springer Nature LaTeX 支持](https://www.springernature.com/gp/authors/campaigns/latex-author-support)
- [ICML 投稿指南](https://icml.cc/Conferences/2025/AuthorInstructions) - 强制 LaTeX
- [Overleaf 学术写作指南](https://www.overleaf.com/for/authors)
- 各期刊官方投稿指南

> **注意**：精确百分比为估计值，实际使用率因具体期刊、研究组和地区而异。

---

### 领域
- 物理学、数学、计算机科学、天文学
- 工程学、化学
- 生物医学
- 社会科学、商业/管理
- 人文学科

### 结论

- **LaTeX 主要集中在理工科**（物理、数学、CS、天文）
- **生物医学和社科人文主要用 Word**
- **arXiv 是 LaTeX 源码的主要来源**

---

## 非 LaTeX 领域的解决方案

### 方案 1：PDF 解析（当前方案）

```
Word/PDF 论文
    │
    ▼
RAGFlow DeepDoc 解析
    │
    ▼
向量检索 + 混合检索
```

**适用**：所有领域
**缺点**：表格/公式解析质量一般

---

### 方案 2：期刊 HTML/XML

部分期刊提供结构化格式：

| 来源 | 格式 | 领域 |
|------|------|------|
| **PubMed Central** | XML | 生物医学 |
| **Springer** | HTML/XML | 多领域 |
| **Elsevier** | XML (ScienceDirect) | 多领域 |
| **Nature** | HTML | 自然科学 |

```python
# PubMed XML 示例
import xml.etree.ElementTree as ET

def parse_pubmed_xml(xml_content: str) -> dict:
    root = ET.fromstring(xml_content)
    return {
        "title": root.find(".//ArticleTitle").text,
        "abstract": root.find(".//AbstractText").text,
        "authors": [a.text for a in root.findall(".//Author/LastName")],
    }
```

---

### 方案 3：API 获取结构化数据

| API | 领域 | 提供内容 |
|-----|------|---------|
| **Semantic Scholar** | 多领域 | 摘要、引用关系 |
| **OpenAlex** | 多领域 | 元数据、摘要 |
| **PubMed API** | 生物医学 | 摘要、MeSH 术语 |
| **CrossRef** | 多领域 | 元数据、DOI |

---

### 方案 4：智能混合策略（推荐）

```
文献来源判断
    │
    ├─ arXiv (物理/数学/CS)
    │   └─ LaTeX 源码 → grep 搜索
    │
    ├─ PubMed (生物医学)
    │   └─ XML/API → 结构化提取
    │
    └─ 其他期刊
        └─ PDF → RAGFlow 解析
```

### 智能格式选择代码示例

```python
def get_best_source(paper_id: str) -> str:
    """根据论文来源选择最优解析方式"""
    if is_arxiv(paper_id):
        return download_latex(paper_id)
    elif is_pubmed(paper_id):
        return fetch_pubmed_xml(paper_id)
    else:
        return parse_pdf(paper_id)

def is_arxiv(paper_id: str) -> bool:
    return "arxiv" in paper_id.lower() or paper_id.startswith("2")

def is_pubmed(paper_id: str) -> bool:
    return paper_id.startswith("PMC") or paper_id.isdigit()
```

---

## 对 ManuScript 的影响

### 当前方案 vs 理想方案

```
当前方案（PDF）                    理想方案（LaTeX）
    │                                    │
    ▼                                    ▼
PDF → RAGFlow 解析 → 向量检索      LaTeX → 直接 grep → 精确定位
    │                                    │
    ▼                                    ▼
- 依赖解析质量                      - 100% 准确
- 可能丢失结构                      - 保留完整结构
- 表格/公式问题                     - 公式/引用可解析
- 通用性强                          - 仅限有源码的论文
```

### 混合方案（推荐）

```
文献来源判断
    │
    ├─ arXiv 论文 → 优先下载 LaTeX 源码 → grep 搜索
    │
    └─ 其他来源 → PDF → RAGFlow 解析 → 向量检索
```

---

## LaTeX 解析工具

如果选择 LaTeX 方案，可用以下工具：

| 工具 | 功能 | 语言 |
|------|------|------|
| **pylatexenc** | LaTeX → 纯文本/Unicode | Python |
| **TexSoup** | LaTeX 解析器（类似 BeautifulSoup） | Python |
| **pandoc** | LaTeX → Markdown/HTML | CLI |
| **latexcodec** | LaTeX 编码处理 | Python |

### 示例：用 TexSoup 提取章节

```python
from TexSoup import TexSoup

with open("paper.tex") as f:
    soup = TexSoup(f.read())

# 提取所有章节标题
sections = soup.find_all("section")
for sec in sections:
    print(sec.string)

# 提取所有引用
citations = soup.find_all("cite")
for cite in citations:
    print(cite.string)
```

---

## 决策记录

### 当前决策

**暂不切换到 LaTeX 方案**

理由：
1. 当前 v1.0 目标是验证核心流程，PDF + RAGFlow 足够
2. 切换到 LaTeX 需要额外的源码下载和解析逻辑
3. 不是所有论文都有 LaTeX 源码（非 arXiv 来源）

### 未来触发条件

当出现以下情况时，考虑引入 LaTeX 方案：

- [ ] 文献库主要来自 arXiv（>80%）
- [ ] PDF 解析质量成为核心瓶颈
- [ ] 需要精确提取引用关系
- [ ] 需要解析数学公式

### 渐进式引入路径

```
v1.0 (当前)
  └─ PDF + RAGFlow（验证核心流程）

v1.5 (如果需要)
  └─ 混合方案：arXiv 论文用 LaTeX，其他用 PDF

v2.0 (如果需要)
  └─ 完整 LaTeX 解析 + 引用图谱构建
```

---

## 相关文档

- [ragflow的解析决策.md](ragflow的解析决策.md) - RAGFlow 解析相关决策
- [ragflow的解析技术分析.md](ragflow的解析技术分析.md) - DeepDoc 技术分析
- [ragflow的检索技巧.md](ragflow的检索技巧.md) - 检索优化参数
