# 息壤帮助中心设计文档

**创建日期：** 2026-04-05
**状态：** 设计阶段
**版本：** V1

---

## 1. 概述

### 1.1 定位

帮助中心是息壤产品内嵌的自助式知识库，服务所有用户（新手 + 老手），旨在让用户快速了解产品功能、掌握操作方法、自主解决问题。采用分层设计：新手有入门引导，老手有进阶玩法和问题排查内容。

### 1.2 设计基调

**"友好导师"风格** — 延续"地牢学者"的游戏化视觉主题，但语气亲切简洁，像一个热心的 NPC 在指导你。不过度卖萌，保持专业感。

### 1.3 多语言

跟随应用 i18n 设置，帮助中心与产品界面语言同步切换。内容硬编码在前端 i18n 文件中，随版本发布更新。

---

## 2. 技术架构

### 2.1 路由

| 路径 | 名称 | 说明 |
|------|------|------|
| `/settings/help-center` | `settings-help-center` | 帮助中心首页（搜索 + Tab 分类 + 内容列表） |
| `/settings/help-center/:slug` | `settings-help-center-article` | 具体文章（页内展开，路由同步切换以支持深链接分享） |

### 2.2 现有基础设施

帮助中心路由已在 `frontend/src/router/index.ts` 中注册，当前复用 `DungeonScholarSettingsDocPage.vue` 组件渲染 Markdown 文件。

**V2 改造方向：** 将帮助中心从简单的 Markdown 渲染升级为独立的交互式帮助页面，具备搜索、Tab 分类、文章展开/收起、版本日志等能力。需新建独立页面组件 `DungeonScholarHelpCenterPage.vue`。

### 2.3 内容存储

内容硬编码在前端代码中，通过 i18n 系统（`frontend/src/i18n/index.ts`）管理多语言文案。结构化数据以 TypeScript 对象形式定义在帮助中心模块内。

### 2.4 入口

- 着陆页（`EasternFantasyLandingPage`）已预留入口
- 设置页（`DungeonScholarSettingsPage`）已预留入口
- 不需要新增额外入口

---

## 3. 页面布局

### 3.1 整体结构

```
┌──────────────────────────────────────────────────┐
│  返回按钮    帮助中心标题    语言切换  主题切换     │ ← 顶部工具栏（复用现有 doc-toolbar 样式）
├──────────────────────────────────────────────────┤
│  🔍 搜索栏（全文关键词搜索）                        │ ← 全宽搜索区
├──────────────────────────────────────────────────┤
│  [快速开始] [功能指南] [常见问题] [问题排查] [更新日志] │ ← Tab 分类导航
├──────────────────────────────────────────────────┤
│                                                  │
│  内容区域（文章列表 / 展开的文章详情）               │ ← 主内容区
│                                                  │
│  ── 左侧目录 TOC（桌面端，文章展开时显示）          │
│                                                  │
├──────────────────────────────────────────────────┤
│  🏛 社区入口  |  📄 隐私政策  |  📄 用户协议        │ ← 底部链接区
└──────────────────────────────────────────────────┘
```

### 3.2 交互流程

1. 用户进入帮助中心 → 看到搜索栏 + Tab 分类 + 各 Tab 下的文章列表
2. 用户可输入关键词搜索 → 实时过滤匹配的文章
3. 用户点击某篇文章 → 当前页展开内容，左侧出现 TOC 目录，路由切换为 `/settings/help-center/:slug`
4. 用户点击其他文章或返回列表 → 收起当前文章，路由回到 `/settings/help-center` 或切换 slug
5. 底部提供社区/隐私政策/用户协议的外部链接

### 3.3 移动端适配

- 搜索栏全宽
- Tab 改为横向滚动
- 左侧 TOC 目录隐藏（折叠为顶部下拉）
- 文章卡片全宽显示
- 字体适当缩小

---

## 4. 内容结构（按用户旅程 + 功能模块混合分类）

### 4.1 Tab 1：快速开始

覆盖注册到完成第一局答题的标准流程。

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `quick-start` | 开始你的冒险之旅 | 注册 → 登录 → 上传文档 → 选择模式 → 完成答题 → 查看结算，完整6步流程 |

### 4.2 Tab 2：功能指南

按功能模块组织，涵盖所有产品功能。

#### 4.2.1 账户与设置

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `account-register` | 注册与登录 | 邮箱注册、登录、密码重置流程 |
| `account-settings` | 个人设置 | 主题切换、语言切换、通知偏好、个人信息修改 |
| `account-security` | 账户安全 | 密码安全建议、数据安全说明 |

#### 4.2.2 文档管理

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `upload-documents` | 上传你的知识典籍 | 支持的文件格式（Markdown/PDF/DOCX/PPTX）、大小限制（50MB）、上传步骤 |
| `document-status` | 文档处理状态说明 | processing → ready → failed 状态含义、处理时间预期、失败重试方法 |
| `document-formats` | 多格式解析指南 | 各格式解析特点与建议：Markdown 最稳定、PDF/DOCX/PPTX 通过 MinerU 解析、格式选择建议 |
| `manage-documents` | 管理你的书库 | 文档列表查看、删除、重新处理 |

#### 4.2.3 学习路径与题库

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `learning-paths` | 学习路径详解 | 技能树（单元）→ 关卡（level）结构、路径懒生成机制、版本管理 |
| `question-bank` | AI 题库说明 | AI 如何基于文档生成题目、题型分布、难度分层 |
| `path-regeneration` | 重新生成学习路径 | 重生条件（24h/3次限制）、何时需要重生 |

#### 4.2.4 答题模式

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `mode-overview` | 三大答题模式总览 | 三种模式的定位和适合场景对比 |
| `mode-endless-abyss` | 无尽深渊 | **规则：** 无限答题，答错即止。**计分：** 连续正确加分递增。**策略：** 保持冷静、不确定时跳过优于答错、利用知识广度优势。**奖励：** 深度越高奖励倍率越大 |
| `mode-speed-survival` | 速度生存 | **规则：** 限时答题，速度与正确率并重。**计分：** 剩余时间越多分数越高。**策略：** 快速判断、果断放弃不确定题目、合理分配时间。**奖励：** 剩余时间奖励加成 |
| `mode-knowledge-draft` | 知识草稿 | **规则：** 开放式作答，AI 评分。**计分：** 回答完整度与准确性综合评分。**策略：** 尽量用自己的话表述、关注核心概念、结构化回答得分更高。**奖励：** 高质量回答获得额外奖励 |
| `mode-strategies` | 答题通用策略 | 各模式通用技巧：时间管理、错题利用、知识面扩展建议 |

#### 4.2.5 结算与奖励

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `settlement-overview` | 结算系统详解 | 得分计算、金币/XP 获取方式与用途 |
| `reward-rules` | 奖励规则说明 | 传奇复习递减规则（50%→30%→20%→10%）、旧版本奖励折扣（70%）、免费用户每日封顶（XP 300 / coin 60，UTC+8） |
| `subscription-benefits` | 订阅用户权益 | 免费用户与订阅用户权益对比、订阅用户奖励不封顶 |

#### 4.2.6 错题与复习

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `mistake-book` | 错题本使用指南 | 错题如何产生、错题本查看、错题分类 |
| `mistake-explanation` | AI 错题解析 | AI 解析原理、基于 PageIndex + pgvector 的增强解释、相似错题召回 |
| `review-strategy` | 高效复习策略 | 如何利用错题本提升学习效果：定期复习、关注相似错题、主动回忆法建议 |

#### 4.2.7 钱包与商店

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `wallet-guide` | 钱包使用指南 | 余额查看、金币账本、交易记录 |
| `shop-guide` | 商店与道具 | 道具类型与效果说明、购买步骤、库存查看 |

#### 4.2.8 赛季与排行榜

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `season-rules` | 赛季规则 | 每周赛季（周一至周日，Asia/Shanghai 时区）、段位体系、排名规则 |
| `promotion` | 段位晋升 | 前 5 名晋升机制、段位等级说明、晋升奖励 |

### 4.3 Tab 3：常见问题

#### 4.3.1 功能疑问

| 文章 slug | 问题 |
|-----------|------|
| `faq-upload-fail` | 为什么文档上传/处理失败？ |
| `faq-retry-quiz` | 如何重新做同一组题目？ |
| `faq-mode-difficulty` | 三种模式有什么区别？难度一样吗？ |
| `faq-reward-cap` | 为什么我的金币/经验值不再增加了？ |
| `faq-document-format` | 支持哪些文件格式？ |
| `faq-ai-question-quality` | AI 生成的题目准确吗？ |
| `faq-path-regeneration` | 如何重新生成学习路径？ |

#### 4.3.2 技术问题

| 文章 slug | 问题 |
|-----------|------|
| `faq-network-error` | 遇到网络错误怎么办？ |
| `faq-loading-fail` | 页面加载失败/白屏怎么处理？ |
| `faq-browser-support` | 支持哪些浏览器？ |
| `faq-backend-offline` | 显示"后端离线"是什么意思？ |

#### 4.3.3 账户安全

| 文章 slug | 问题 |
|-----------|------|
| `faq-reset-password` | 忘记密码怎么办？ |
| `faq-data-safety` | 我的文档数据安全吗？ |
| `faq-delete-account` | 如何注销账户？数据会被怎样处理？ |

#### 4.3.4 产品理念

| 文章 slug | 问题 |
|-----------|------|
| `faq-why-gamification` | 为什么用游戏化方式学习？ |
| `faq-why-doc-based` | 为什么要上传自己的文档？与预制课程有什么不同？ |
| `faq-why-ai` | AI 在产品中扮演什么角色？ |

### 4.4 Tab 4：问题排查

每篇排查指南包含：分步排查步骤 + 错误码对照表。

| 文章 slug | 标题 | 内容概要 |
|-----------|------|---------|
| `troubleshoot-upload` | 文档上传问题排查 | 检查文件格式/大小 → 检查网络 → 重试 → 联系社区 |
| `troubleshoot-processing` | 文档处理失败排查 | 查看错误状态 → 检查文件内容 → 重新上传 → 格式转换建议 |
| `troubleshoot-run` | 答题异常排查 | 检查文档状态 → 刷新页面 → 清除缓存 → 检查网络 |
| `troubleshoot-payment` | 商店购买失败排查 | 检查余额 → 检查网络 → 重试 → 查看交易记录 |
| `error-codes` | 错误码对照表 | 后端常见错误码（4xx/5xx）与含义对照，帮助用户理解技术错误 |

### 4.5 Tab 5：更新日志

记录产品版本更新内容，按时间倒序排列。

| 文章 slug | 标题 | 格式 |
|-----------|------|------|
| `changelog` | 版本更新日志 | 按版本号/日期列出更新内容，分为「新增」「改进」「修复」三类 |

---

## 5. 搜索功能

### 5.1 搜索范围

- 全文关键词搜索
- 搜索范围覆盖所有 Tab 下的文章标题和正文内容
- 搜索结果按 Tab 分类展示匹配的文章列表

### 5.2 搜索交互

- 输入即搜索（debounce 300ms）
- 搜索结果高亮匹配关键词
- 无结果时显示友好提示
- 搜索状态与 Tab 联动（清除搜索回到当前 Tab 内容）

---

## 6. 视觉风格

### 6.1 主题一致性

- 延续"地牢学者"的奇幻主题风格
- 暗色调背景 + 金色/琥珀色点缀
- 使用项目现有的 CSS 自定义属性（`--color-*`）
- 字体复用项目设定（`--font-serif` 标题，sans-serif 正文）

### 6.2 组件风格

| 元素 | 样式 |
|------|------|
| 搜索栏 | 圆角输入框，带放大镜图标，暗色半透明背景 |
| Tab 导航 | 下划线式 Tab，活跃态用金色/琥珀色下划线 |
| 文章卡片 | 圆角卡片，悬停时有微光效果，左侧图标 |
| 展开内容 | 复用现有 `doc-content` Markdown 渲染样式 |
| TOC 目录 | 复用现有 `doc-toc` 样式 |
| 空状态/占位 | 延续现有 doc-placeholder 风格 |

### 6.3 图标与装饰

- 每个功能模块使用对应的主题图标（如文档用📜、答题用⚔️、商店用🏪）
- 可使用项目内的 icon_font 或 SVG 图标
- 避免过度装饰影响阅读

---

## 7. 视频内容预留

V1 阶段只做图文内容，但文档结构需预留视频位置：

- 每篇文章的数据结构中包含可选的 `videoUrl` 字段
- 文章详情页在标题下方预留视频播放区域（条件渲染，有视频时显示）
- 关键流程（如上传文档、答题模式演示）标记为"未来添加视频"

---

## 8. 底部链接区

帮助中心页面底部提供以下链接：

| 链接 | 目标 | 说明 |
|------|------|------|
| 社区 | 外部社区/论坛/Discord | 用户交流入口，URL 待定 |
| 隐私政策 | `/settings/privacy-policy` | 已有独立页面 |
| 用户协议 | `/settings/user-agreement` | 已有独立页面 |

---

## 9. 反馈机制

帮助中心本身**不需要**"有帮助/没帮助"投票或反馈表单。游戏体验反馈将在后续通过游戏环节中的智能体实现，用户可报告体验问题，智能体会据此优化提示词等 LLM 相关内容。

---

## 10. 内容数据结构（TypeScript 示意）

```typescript
interface HelpArticle {
  slug: string;
  title: string;
  summary: string;
  category: 'quick-start' | 'guide' | 'faq' | 'troubleshoot' | 'changelog';
  subcategory: string;
  content: string; // Markdown 内容
  tags: string[];
  videoUrl?: string; // 预留
  relatedArticles?: string[]; // slug 引用
  lastUpdated: string; // ISO date
}

interface HelpTab {
  id: string;
  label: string; // i18n key
  icon: string;
  subcategories: {
    id: string;
    label: string; // i18n key
    articles: HelpArticle[];
  }[];
}
```

---

## 11. 与现有代码的集成方案

### 11.1 新建文件

| 文件 | 说明 |
|------|------|
| `frontend/src/pages/DungeonScholarHelpCenterPage.vue` | 帮助中心独立页面组件 |
| `frontend/src/composables/useHelpCenter.ts` | 帮助中心数据与搜索逻辑 |
| `frontend/src/components/help/HelpSearchBar.vue` | 搜索栏组件 |
| `frontend/src/components/help/HelpTabNav.vue` | Tab 导航组件 |
| `frontend/src/components/help/HelpArticleList.vue` | 文章列表组件 |
| `frontend/src/components/help/HelpArticleDetail.vue` | 文章详情（展开态）组件 |
| `frontend/src/components/help/HelpToc.vue` | 左侧目录组件 |

### 11.2 修改文件

| 文件 | 变更 |
|------|------|
| `frontend/src/router/index.ts` | 帮助中心路由指向新组件，新增 `:slug` 子路由 |
| `frontend/src/constants/routes.ts` | 新增 `helpCenter` 和 `helpCenterArticle` 路由常量 |
| `frontend/src/i18n/index.ts` | 新增帮助中心所有文案的多语言内容 |

### 11.3 路由调整

```typescript
// routes.ts 新增
helpCenter: "/settings/help-center",
helpCenterArticle: "/settings/help-center/:slug",

// router/index.ts 调整
{
  path: "/settings/help-center",
  name: "settings-help-center",
  component: DungeonScholarHelpCenterPage,
},
{
  path: "/settings/help-center/:slug",
  name: "settings-help-center-article",
  component: DungeonScholarHelpCenterPage,
},
```

---

## 12. 实施优先级

### P0 — MVP

1. 帮助中心页面骨架（搜索 + Tab + 文章列表 + 展开详情）
2. 快速开始内容
3. 三种答题模式详解
4. 基础 FAQ（10 篇核心问答）

### P1 — 完整版

5. 全部功能指南内容
6. 问题排查 + 错误码对照表
7. 搜索功能
8. 移动端适配优化

### P2 — 增强版

9. 更新日志板块
10. 视频内容填充
11. 相关文章推荐
12. 社区入口集成
