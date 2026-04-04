# Xirang Scripts

用于本地开发/联调的辅助脚本目录（非 `backend/tests/` 的 pytest 测试目录）。

## 当前保留脚本

### 1) `init_db.py`

初始化本地 PostgreSQL 数据库。

#### 用法

```bash
# Show help
uv run python scripts/init_db.py --help

# Initialize with default settings (from .env)
uv run python scripts/init_db.py

# Initialize with custom database URL
uv run python scripts/init_db.py --database-url "postgresql://user:pass@localhost:5432/xirang"

# Drop and recreate (DESTRUCTIVE)
uv run python scripts/init_db.py --reset

# Skip pgvector bootstrap when the extension is not installed yet
uv run python scripts/init_db.py --skip-vector-extension
```

#### 作用

1. 若不存在则创建数据库
2. 启用 `pgvector` 扩展
3. 执行 Alembic 到最新迁移
4. 通过 smoke query 验证

#### 相关环境变量

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |

---

### 2) `e2e_mineru_flow_check.py`

端到端联调脚本，验证完整链路：

`上传文档 -> ingestion 完成 -> 获取学习路径(path-options) -> 基于 path_id 创建 run 生成题目`

该脚本已强制“先路径后出题”，用于校验真实业务顺序。

#### 用法

```bash
# 在 backend 目录执行
MINERU_TIMEOUT_SECONDS=1800 E2E_READY_TIMEOUT_SECONDS=2400 uv run python ../scripts/e2e_mineru_flow_check.py
```

#### 说明

- 默认测试文件：`D:/project/Xirang/tmp_uploads/13、-AI行业落地案例补充知识.pdf`
- 依赖本地服务：
  - backend API (`http://127.0.0.1:8000`)
  - MinerU (`http://127.0.0.1:8300`)
  - PageIndex（建议可用）

---

## 清理策略

- `scripts/` 只保留可复用脚本。
- 一次性排障脚本不长期保留，避免目录噪音和误用。

## Notes

- 建议从仓库根目录执行命令。
- 脚本仅面向本地开发和联调，不用于生产环境。
