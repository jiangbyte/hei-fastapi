# HEI FastAPI Admin

`web/admin` 是 HEI FastAPI 的管理端前端应用，面向系统管理员和运营人员。它使用 `ADMIN`
账号体系，只调用 `/api/v1/admin/*` 和公共文件接口，不与 portal 用户体系混用。

## 功能范围

- 认证：HttpOnly Cookie 会话；登录、退出、找回/重置密码；Admin TOTP / WebAuthn MFA。
- 用户中心：头像上传、基础资料、密码与双因素认证。
- 动态路由和菜单：根据后端资源树生成菜单、页面和按钮权限。
- IAM/RBAC：账号、角色、部门、用户组、岗位、资源、权限注册与角色授权。
- 系统模块：字典、Banner、文件管理、操作审计。
- 消息模块：通知、公告、反馈。
- 会话管理：在线账号、在线 token、强制下线。
- Dashboard 和常规错误页。

## 技术栈

- Vue 3 / Vite / TypeScript
- Naive UI / Pro Naive UI
- Pinia / pinia-plugin-persistedstate
- Vue Router
- axios
- UnoCSS
- Iconify
- vue-advanced-cropper

## 本地开发

```bash
pnpm install
pnpm dev
```

默认环境变量见 `.env`：

```env
VITE_PORT=5173
VITE_HOME_PATH="/dashboard"
VITE_ROUTE_LOAD_MODE="dynamic"
VITE_API_URL="http://127.0.0.1:8000"
```

开发模式下请求会直接发到 `VITE_API_URL`。后端默认地址是 `http://127.0.0.1:8000`，管理端主要接口
前缀是 `/api/v1/admin/*`。

## 常用命令

```bash
pnpm dev
pnpm lint
pnpm lint:fix
pnpm build
pnpm preview
pnpm format
pnpm format:check
```

## 生产构建

```bash
pnpm build
```

生产构建读取 `.env.production`。当前生产配置中：

```env
VITE_API_URL=""
```

这表示前端产物使用同源 `/api/` 请求，由 nginx 在容器内反向代理到后端。不要在浏览器端写死后端
内网地址；容器启动时用 `BACKEND_URL` 指定后端。

## Docker

在 `web/admin` 目录内构建：

```bash
docker build -t hei-fastapi-admin .
docker run -d \
  --name hei-fastapi-admin \
  -e BACKEND_URL="http://host.docker.internal:8000" \
  -p 8081:81 \
  hei-fastapi-admin
```

也可以在仓库根目录构建：

```bash
docker build -t hei-fastapi-admin web/admin
```

镜像说明：

- Node 22 alpine 构建 `dist/`。
- nginx 1.27 alpine 托管静态资源。
- 容器内 nginx 监听 `81`。
- `BACKEND_URL` 在容器启动时渲染到 nginx 配置中。
- `CLIENT_MAX_BODY_SIZE` 控制上传体积限制，默认 `10m`。
- `CONTENT_SECURITY_POLICY` 和 `HSTS_HEADER` 可在启动时覆盖。
- nginx 已配置 SPA fallback、`/assets/` 长缓存、`/api/` 反向代理和 SSE 支持。

## 目录结构

```text
src/
  api/          admin API 封装
  components/   通用组件和业务组件
  hooks/        组合式工具
  layouts/      管理端布局
  plugins/      图标等插件初始化
  router/       静态路由、动态路由和守卫
  stores/       Pinia 状态
  style.css     全局样式
  typing/       类型声明
  utils/        axios、权限、字典、文件 URL 等工具
  views/        页面
nginx/          生产 nginx 模板
```

## 路由和菜单

管理端默认使用动态资源模式：

```env
VITE_ROUTE_LOAD_MODE="dynamic"
```

登录后前端会调用 `/api/v1/admin/sys/resources/current` 获取按模块分组的当前用户可见资源；所有模块资源用于生成动态路由，侧栏菜单按当前选中模块显示。
静态内置路由主要包括认证页、错误页、用户中心和固定布局页。

权限边界：

- admin 前端不应调用 `/api/v1/portal/*`。
- 按钮和页面权限来自后端资源树与权限 key。
- 文件预览、头像等 URL 通过工具函数处理，兼容同源 `/api/` 与外部对象存储 URL。
