# Cloudflare R2 对象存储集成方案

> 状态：方案设计阶段，待与 Creem 支付、订阅功能一起落地实现
> 更新时间：2026-04-14

---

## 一、为什么选择 Cloudflare R2

| 维度 | R2 优势 | 对比说明 |
|------|---------|----------|
| **S3 兼容 API** | 完全兼容 AWS S3 SDK， boto3 / aiobotocore 可直接使用 | 无需学习新 API，迁移成本低 |
| **零出站流量费** | 从 R2 读取文件不产生 egress 费用 | 对 Render/Vercel 频繁拉取文件的场景极有利 |
| **全球 CDN 集成** | 可绑定 Cloudflare CDN，文件分发到边缘节点 | 适合前端直接预览用户上传的文档/图片 |
| **定价友好** | 存储 $0.015/GB/月，操作 $0.36/百万次请求 | 早期项目成本几乎可忽略 |
| **免信用卡** | 免费额度充足（10GB 存储/月，100万次读/月） | 适合 MVP 和早期验证阶段 |

---

## 二、架构设计

### 2.1 存储层抽象

保持现有的 `DocumentStorage` 抽象接口不变，新增 `R2DocumentStorage` 实现：

```
app/services/documents/
├── storage.py              # DocumentStorage 抽象基类
├── storage_local.py        # LocalDocumentStorage（本地开发保留）
├── storage_r2.py           # R2DocumentStorage（新增）
└── storage_object.py       # 废弃或重命名为 storage_r2
```

### 2.2 部署环境映射

| 环境 | STORAGE_MODE | 说明 |
|------|-------------|------|
| 本地开发 | `local` | 继续写入 `.data/uploads`，无需 R2 |
| Render 生产 | `r2` | 所有上传文件写入 Cloudflare R2 |
| CI/测试 | `local` 或 mock | 测试环境不依赖真实 R2 |

---

## 三、R2 配置项

### 3.1 需要在 Cloudflare Dashboard 获取的信息

1. **Account ID**（R2 区域标识）
2. **Access Key ID** + **Secret Access Key**（S3 兼容凭证）
3. **Bucket Name**（如 `xirang-uploads-prod`）
4. **Public/Private 策略**（根据是否需要前端直接访问决定）

### 3.2 后端环境变量扩展

在现有 `.env` / `render.yaml` 中新增以下变量：

```bash
# 存储模式切换：local | r2
STORAGE_MODE=r2

# R2 核心配置
R2_BUCKET_NAME=xirang-uploads-prod
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key

# 可选：自定义 Public Base URL（用于生成可直接访问的文件链接）
R2_PUBLIC_URL=https://pub-xxx.r2.dev
```

### 3.3 Render.yaml 更新

```yaml
envVars:
  - key: STORAGE_MODE
    value: r2
  - key: R2_BUCKET_NAME
    value: xirang-uploads-prod
  - key: R2_ACCOUNT_ID
    sync: false
  - key: R2_ACCESS_KEY_ID
    sync: false
  - key: R2_SECRET_ACCESS_KEY
    sync: false
  - key: R2_PUBLIC_URL
    sync: false
```

---

## 四、后端实现方案

### 4.1 依赖库

```toml
# pyproject.toml 新增
dependencies = [
    "boto3>=1.34.0",
    "aiobotocore>=2.12.0",
]
```

或使用 `boto3` 的同步客户端在异步函数中通过 `asyncio.to_thread()` 调用，避免引入 `aiobotocore` 的复杂度。

### 4.2 R2DocumentStorage 核心实现

```python
# app/services/documents/storage_r2.py（设计稿）
import boto3
from botocore.config import Config

class R2DocumentStorage(DocumentStorage):
    def __init__(self, *, bucket: str, endpoint_url: str, access_key: str, secret_key: str):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )

    def save_bytes(self, *, owner_id: str, file_name: str, content: bytes, media_type: str) -> StoredFile:
        storage_key = f"{owner_id}/{uuid4().hex}-{sanitize_file_name(file_name)}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=storage_key,
            Body=content,
            ContentType=media_type,
        )
        return StoredFile(
            storage_key=storage_key,
            storage_path=storage_key,  # R2 中 storage_path 与 storage_key 一致
            file_name=file_name,
            file_size_bytes=len(content),
            media_type=media_type,
        )

    def delete(self, storage_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_key)

    def read_bytes(self, storage_key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=storage_key)
        return response["Body"].read()

    def read_text(self, storage_key: str) -> str:
        return self.read_bytes(storage_key).decode("utf-8", errors="ignore")
```

### 4.3 配置解析扩展

```python
# app/core/config.py 新增字段
r2_bucket_name: str | None = None
r2_account_id: str | None = None
r2_access_key_id: str | None = None
r2_secret_access_key: str | None = None
r2_public_url: str | None = None

@property
def r2_endpoint_url(self) -> str | None:
    if self.r2_account_id:
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"
    return None
```

### 4.4 Storage 构建器更新

```python
# app/services/documents/storage.py
def build_storage(*, storage_mode: StorageMode, upload_dir: Path | None = None) -> DocumentStorage:
    if storage_mode == StorageMode.LOCAL:
        from app.services.documents.storage_local import LocalDocumentStorage
        return LocalDocumentStorage(root_dir=upload_dir or Path(".data/uploads"))

    if storage_mode == StorageMode.R2:
        from app.services.documents.storage_r2 import R2DocumentStorage
        settings = get_settings()
        return R2DocumentStorage(
            bucket=settings.r2_bucket_name,
            endpoint_url=settings.r2_endpoint_url,
            access_key=settings.r2_access_key_id,
            secret_key=settings.r2_secret_access_key,
        )

    raise ValueError(f"Unsupported storage mode: {storage_mode}")
```

---

## 五、Worker 层改造

### 5.1 当前 Worker 文件读取逻辑的问题

`app/workers/main.py` 中 `_read_document_bytes` / `_read_document_content` 目前强依赖 `storage.root_dir` 这个属性来拼接本地路径。R2 存储没有 `root_dir`。

### 5.2 改进方案

在 `DocumentStorage` 抽象基类中新增标准读取方法：

```python
class DocumentStorage:
    def read_bytes(self, storage_key: str) -> bytes:
        raise NotImplementedError

    def read_text(self, storage_key: str) -> str:
        return self.read_bytes(storage_key).decode("utf-8", errors="ignore")
```

Worker 中 `_load_document_markdown` 和 `_read_document_bytes` 统一改为调用 `storage.read_bytes(storage_key)`，不再直接访问文件系统。

对于 Markdown/TXT，仍然保持**数据库 `content_text` 优先**的策略（这是上一版修复的核心），R2 仅作为二进制格式的回退和文件持久化层。

---

## 六、数据迁移策略

### 方案 A：零停机切换（推荐）

1. 在生产数据库上运行 Alembic 迁移，添加 `content_text`（已完成）
2. 部署支持 R2 的后端代码
3. 将 `STORAGE_MODE` 从 `local` 切到 `r2`
4. **新上传文件** → 直接进入 R2
5. **旧文件** → 仍保留在 Render 的 `/tmp` 中，但 Render 每次重启都会丢失这些文件，因此旧文件本来就已经不可用了。对于仍然有效的旧文件，可以写一个一次性迁移脚本将其上传到 R2。

### 方案 B：渐进式迁移

如果希望保留旧文件：
1. 写一个 `migrate_local_to_r2.py` 脚本
2. 遍历数据库中所有 `documents`
3. 对于本地文件仍存在的，调用 `R2DocumentStorage.save_bytes` 上传
4. 更新 `storage_path` 为 R2 的 `storage_key`

考虑到目前 Render free/starter plan 的容器是无状态且会定期重启的，**实际上旧文件大部分已经丢失**，方案 A 足够。

---

## 七、安全与权限

### 7.1 Bucket 访问策略

建议采用 **Private Bucket + 预签名 URL** 模式：
- Bucket 默认不公开
- API 层如需返回文件下载链接，使用 boto3 `generate_presigned_url()` 生成 15 分钟有效期的临时链接
- 避免将 R2 凭证暴露给前端

### 7.2 CORS 配置（如需要前端直传）

如果未来计划实现**前端直传 R2**（绕过后端带宽），需要在 R2 Bucket 上配置 CORS：

```xml
<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>https://xirang.vercel.app</AllowedOrigin>
    <AllowedMethod>PUT</AllowedMethod>
    <AllowedMethod>POST</AllowedMethod>
    <AllowedHeader>*</AllowedHeader>
  </CORSRule>
</CORSConfiguration>
```

> 初期建议保留后端代理上传模式（API 接收文件 → 转存 R2），逻辑更简单，安全性更高。

---

## 八、成本估算

以项目早期规模估算（1000 用户，每月上传 5000 个文档，平均 2MB/个）：

| 项目 | 估算 |
|------|------|
| 月新增存储 | ~10 GB |
| 月读请求（Worker 解析） | ~5000 次 |
| R2 存储费 | $0.15/月 |
| R2 操作费 | ~$0.001/月 |
| ** egress 费** | **$0** |
| **总计** | **≈ $0.15/月** |

在 Cloudflare 免费额度内（10GB 存储 + 100万读请求/月），早期甚至可以**完全免费**。

---

## 九、下一步待办清单

- [ ] 注册 Cloudflare 账号并创建 R2 Bucket
- [ ] 生成 R2 API Token（S3 兼容的 Access Key + Secret Key）
- [ ] 在 Render 环境变量中配置 `R2_*` 系列变量
- [ ] 实现 `R2DocumentStorage` 类
- [ ] 扩展 `StorageMode` 枚举，新增 `R2 = "r2"`
- [ ] 在 `DocumentStorage` 基类中新增 `read_bytes` / `read_text` 方法
- [ ] 重构 Worker 的文件读取逻辑，统一调用 `storage.read_bytes()`
- [ ] 更新 `render.yaml`，将 `STORAGE_MODE` 改为 `r2`
- [ ] 本地环境保持 `STORAGE_MODE=local` 不变
- [ ] 编写 R2 存储适配器的单元测试（使用 moto 或 Fake R2 Client）
- [ ] 部署验证：上传 PDF/DOC/Markdown，确认 Worker 能正常拉取并解析

---

## 十、参考文档

- [Cloudflare R2 - S3 Compatible API](https://developers.cloudflare.com/r2/api/s3/api/)
- [Cloudflare R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [Boto3 S3 Client - generate_presigned_url](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_url.html)
