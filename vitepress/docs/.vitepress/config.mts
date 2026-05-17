import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'zh-CN',
  title: 'Hei FastAPI',
  description: 'Hei FastAPI - 基于 FastAPI + SQLAlchemy 的 Python 快速开发框架官方文档',
  base: '/hei-fastapi',

  head: [['link', { rel: 'icon', href: '/logo.svg' }]],

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide/' },
      { text: '架构', link: '/architecture/' },
      { text: '功能', link: '/features/' },
      { text: '模块开发', link: '/modules/' },
      {
        text: '相关项目',
        items: [
          { text: 'Hei Boot (Java)', link: 'https://github.com/jiangbyte/hei-boot' },
          { text: 'Hei Gin (Go)', link: 'https://github.com/jiangbyte/hei-gin' },
          { text: 'Hei Admin Vue', link: 'https://github.com/jiangbyte/hei-admin-vue' },
        ],
      },
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/jiangbyte' },
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2026-present Charlie',
    },

    search: {
      provider: 'local',
    },

    outline: {
      level: [2, 3],
      label: '本页目录',
    },

    sidebar: {
      '/guide/': [
        { text: '框架介绍', link: '/overview' },
        { text: '快速开始', link: '/guide/quickstart' },
        { text: '安装配置', link: '/guide/installation' },
        { text: '配置文件说明', link: '/guide/config' },
      ],
      '/architecture/': [
        { text: '架构概述', link: '/architecture/overview' },
        { text: '项目结构', link: '/architecture/structure' },
      ],
      '/features/': [
        { text: '功能概览', link: '/features/' },
        { text: '双端认证', link: '/features/auth' },
        { text: '权限管理', link: '/features/permission' },
        { text: '中间件体系', link: '/features/middleware' },
        { text: '文件存储', link: '/features/storage' },
        { text: '操作日志', link: '/features/log' },
      ],
      '/modules/': [
        { text: '模块开发规范', link: '/modules/development' },
      ],
    },
  },

  markdown: {
    lineNumbers: true,
  },

  ignoreDeadLinks: true,
})
