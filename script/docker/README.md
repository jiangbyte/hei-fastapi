# Docker / SnailJob scripts

## SnailJob Server（本地）

不管理业务 Postgres/Redis；假定本机已有 Postgres（如 `dev-postgres`），并单独建库 `snail_job`。

```bash
# greenfield：schema + hei-fastapi 种子
./script/docker/snailjob-flyway.sh

# 若库已由 hei-boot 迁过，只补本仓幂等种子
./script/docker/seed_fastapi_only.sh

docker compose -f script/docker/docker-compose.snailjob.yml up -d
```

| 端口 | 用途 |
|---|---|
| 9189 | 控制台 → 容器 8080 |
| 17888 | Server RPC |

控制台默认：`http://127.0.0.1:9189/snail-job`，种子后 `admin` / `123456`。

本仓种子使用独立 namespace `hei-fastapi`（`a8c3e5f17b924d6e9f0a1b2c3d4e5f60`）与 group `hei_fastapi_admin`，可与 hei-boot 共存于同一 Server。
