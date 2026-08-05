# HEI Portal (React)

Vite + React + TypeScript + Ant Design + UnoCSS 门户脚手架。

## 开发

```bash
pnpm install
pnpm dev
```

默认端口见 `.env` 的 `VITE_PORT`（5174）。若被占用，Vite 会自动换端口。

## 脚本

- `pnpm dev` / `build` / `preview`
- `pnpm lint` / `lint:fix`
- `pnpm format` / `format:check`

## 目录

- `src/api` 接口（auth / message / sys）
- `src/utils/axios` HTTP 解包与拦截器
- `src/stores` Zustand
- `src/router` 路由与守卫
- `src/layouts` / `src/pages` / `src/components`

## 已包含页面

- 首页、登录 / 注册 / 找回密码
- 个人主页、账号中心
- 站内消息（IM）
- 公告列表与详情
