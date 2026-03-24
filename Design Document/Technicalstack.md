1. 前端 (Frontend): “Q 弹”视觉制造机
核心框架： Vue 3 (Composition API) + Vite（启动极快，开发体验拉满）。

UI 与样式： Tailwind CSS（不用再去想类名，直接在 HTML 里写样式，极其适合快速迭代）。

动画引擎 (MLP 的灵魂)：

VueUse： 提供开箱即用的各种钩子（比如获知鼠标位置、滑动方向，用来做“左滑右滑”的极速狂热模式）。

CSS Animations / Anime.js： 不需要重度 3D，就用最简单的 CSS transform: scale() 和弹性（Spring）效果，把卡片的拖拽和点击做得 Q 弹。

Canvas Confetti： 一行代码搞定通关后的“全屏彩纸雨”特效。

PWA 插件： vite-plugin-pwa（打包时自动生成 manifest，让你的网页可以直接安装到手机桌面，图标就是小饕餮）。

2. 后端 (Backend): AI 熔炉与防刷引擎
核心框架： FastAPI（目前 Python 界做轻量级 API 最爽、最快、现代化的框架，自带 Swagger 文档，比 Django/Flask 更适合做这种重 API 的应用）。

数据库： 初期直接用 PostgreSQL 配合 SQLAlchemy（或者更现代的 ORM 如 Prisma Client Python），管理用户的“连胜记录”、“代币余额”和“错题本”。

大模型接入 (The AI Core)：

使用 Python 的 openai 官方库（因为现在几乎所有免费/便宜的大模型 API 如智谱 GLM、DeepSeek、SiliconFlow 都兼容 OpenAI 格式）。

后端的关键任务： 你的 Python 后端要写一段极强的 Prompt，强制大模型返回严格的 JSON 格式（包含题目、选项、真伪、解析），然后直接喂给 Vue 前端渲染成卡片。
agent构建方式： OpenAI agent sdk
rag构建组合：
大脑一：全景生成器 (PageIndex 纯上下文流派)
处理对象： 完整的原始文档。

动作： 我们不切分文档，直接把全文（或超大章节）塞进大模型的超长上下文窗口里。

产出结果： 大模型凭借全局视野，提取出深度的关联逻辑，生成包含【单选、多选、判断、填空】的 JSON 题库。

应用场景： 这就是用户玩【无尽深渊】或【极速狂热】时刷的关卡内容。

大脑二：碎片索引库 (pgvector 向量切块流派)
处理对象： 依然是同一份原始文档。

动作： 我们在后台默默把它切成 500 字左右的小块，转换成向量存进 Supabase 的 pgvector 中。

产出结果： 形成了一个可以按语义精准搜索的“知识碎片索引”。

应用场景（高光时刻）： 假设用户在一道极难的填空题上扣了血（答错了），点击了**“查看解析”。为了省钱和追求极致速度，我们绝不再把原文档重新发给大模型**。我们直接拿这道错题去 pgvector 里搜一下，瞬间捞出原文中最相关的那个 500 字切片。把这 500 字丢给一个便宜极速的大模型，它就能立刻告诉你：“这题你选错了，原文的细节在这里……”

3. 部署 (Deployment): 穷且优雅
前端部署： Vercel 或 Netlify（免费，一键绑定 GitHub 部署，自带 CDN）。

后端部署： Render 或 Zeabur（对 Python FastAPI 支持极好，轻量级，初期几乎免费）。

数据库： Supabase 或 Neon（提供免费的 Postgres 数据库实例）。