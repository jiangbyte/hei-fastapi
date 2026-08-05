import type { RouteRecordRaw } from 'vue-router'
import { RouterLink } from 'vue-router'
import { h } from 'vue'
import Layout from '@/layouts/index.vue'
import { renderIcon } from '@/utils/icon'

// 能参与前端路由体系的资源类型。按钮、动作、接口分组只用于权限控制，不生成页面路由。
const routeResourceTypes: AppRoute.ResourceType[] = ['CATALOG', 'MENU', 'PAGE']

// 能点击跳转的资源类型。目录只承担分组作用，不直接渲染 RouterLink。
const clickableResourceTypes: AppRoute.ResourceType[] = ['MENU', 'PAGE']

const innerAppRoutes: RouteRecordRaw[] = [
  {
    path: '/usercenter',
    name: 'usercenter',
    component: () => import('@/views/usercenter/index.vue'),
    meta: {
      code: 'usercenter',
      name: '个人中心',
      resource_type: 'PAGE',
      is_visible: false,
      is_cache: false,
      is_affix: false,
      status: 'ENABLED',
    },
  },
]

/**
 * 根据资源列表生成 Vue Router 动态路由。
 *
 * 后端资源字段 component 存的是 views 下的相对组件路径，例如 /dashboard/index.vue；
 * 这里通过 import.meta.glob 建立组件映射，再把 MENU/PAGE 资源转换成真实组件路由。
 */
export function createRoutes(resources: AppRoute.RowRoute[]): RouteRecordRaw {
  const resultRoutes = buildRoutes(resources.filter((resource) => !isFullscreenResource(resource)))

  // 所有授权页面都挂在 appRoot 下，统一使用后台 Layout。
  const appRootRoute: RouteRecordRaw = {
    path: '/appRoot',
    name: 'appRoot',
    redirect: import.meta.env.VITE_HOME_PATH,
    component: Layout,
    meta: {},
    children: [],
  }

  setRedirect(resultRoutes)
  appRootRoute.children = [...innerAppRoutes, ...(resultRoutes as unknown as RouteRecordRaw[])]

  return appRootRoute
}

/**
 * 提取独立全屏路由。
 *
 * 这些路由不挂载到后台 Layout 下，适合 IM、登录页之外的独立工作区页面。
 */
export function createFullscreenRoutes(resources: AppRoute.RowRoute[]): RouteRecordRaw[] {
  return buildRoutes(resources.filter((resource) => isFullscreenResource(resource))).map(
    (item) => ({
      path: item.path,
      name: item.name,
      component: item.component,
      meta: item.meta,
    }),
  )
}

/**
 * 根据资源列表生成侧边菜单。
 *
 * 菜单只展示 is_visible=true 的资源；隐藏页面仍可生成路由，但不会出现在侧边菜单中。
 */
export function createMenus(resources: AppRoute.RowRoute[]): AppRoute.MenuOption[] {
  const visibleMenus = standardizeRoutes(resources).filter((route) => route.meta.is_visible)
  return arrayToTree(transformRoutesToMenus(visibleMenus))
}

/**
 * 生成 keep-alive 的 include 列表。
 *
 * 当前动态路由名按 module_id + code 生成，避免跨模块同 code 资源冲突。
 */
export function generateCacheRoutes(resources: AppRoute.RowRoute[]) {
  return resources
    .filter(
      (resource) =>
        isRouteResource(resource) && resource.is_cache && !isFullscreenResource(resource),
    )
    .map(createRouteName)
}

/**
 * 计算当前应该高亮的菜单路径。
 *
 * 如果当前页面本身可见且可点击，直接高亮它自己；
 * 如果当前页面是隐藏页面，则沿 parent_id 向上查找最近的可见父级资源。
 */
export function getActiveMenuPath(resources: AppRoute.RowRoute[], path: string) {
  const routeResources = resources.filter(isRouteResource)
  const current =
    routeResources.find((resource) => resource.path === path) ??
    routeResources.find((resource) => matchResourcePath(resource.path, path))

  if (!current) {
    return path
  }

  if (current.is_visible && isClickableResource(current.resource_type) && current.path) {
    return current.path
  }

  const resourceMap = new Map(routeResources.map((resource) => [resource.id, resource]))
  let parentId = current.parent_id

  while (parentId) {
    const parent = resourceMap.get(parentId)
    if (!parent) {
      break
    }
    if (parent.is_visible && parent.path) {
      return parent.path
    }
    parentId = parent.parent_id
  }

  return current.path ?? path
}

/** Match `/biz/foo/edit/:id` style resource paths against a concrete URL. */
function matchResourcePath(pattern: string | null | undefined, path: string) {
  if (!pattern || !pattern.includes(':')) {
    return false
  }
  const escaped = pattern
    .split('/')
    .map((segment) => (segment.startsWith(':') ? '[^/]+' : segment.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))
    .join('/')
  return new RegExp(`^${escaped}$`).test(path)
}

/**
 * 判断资源是否能进入前端路由系统。
 *
 * 只有启用、有 path、且类型属于 CATALOG/MENU/PAGE 的资源才会被转换。
 */
export function isRouteResource(resource: AppRoute.RowRoute) {
  return (
    resource.status === 'ENABLED' &&
    Boolean(resource.path) &&
    routeResourceTypes.includes(resource.resource_type)
  )
}

/**
 * 判断资源类型是否能点击跳转。
 *
 * CATALOG 目录需要出现在菜单树里，但不应该生成 RouterLink。
 */
export function isClickableResource(resourceType?: AppRoute.ResourceType) {
  return Boolean(resourceType && clickableResourceTypes.includes(resourceType))
}

/**
 * 标准化资源为内部路由节点。
 *
 * route.name 使用 module_id + code，meta 保留完整 SysResource 字段，避免跨模块同 code 冲突。
 */
function standardizeRoutes(resources: AppRoute.RowRoute[]) {
  return resources.filter(isRouteResource).map((resource) => {
    const route: AppRoute.Route = {
      id: resource.id,
      parent_id: resource.parent_id,
      code: resource.code,
      name: createRouteName(resource),
      resource_type: resource.resource_type,
      module_id: resource.module_id,
      module_id_name: resource.module_id_name,
      path: resource.path!,
      redirect: resource.redirect ?? undefined,
      icon: resource.icon,
      href: resource.href,
      sort: resource.sort,
      is_visible: resource.is_visible,
      is_cache: resource.is_cache,
      is_affix: resource.is_affix,
      status: resource.status,
      description: resource.description,
      layout: resource.layout ?? null,
      meta: { ...resource },
    }

    return route
  })
}

function buildRoutes(resources: AppRoute.RowRoute[]) {
  const routes = standardizeRoutes(resources)

  // Vite 会在构建时静态分析 glob，只有存在于 src/views 下的页面组件能被加载。
  const modules = import.meta.glob('@/views/**/*.vue')
  routes.forEach((item) => {
    const resourceComponent = item.meta.component
    if (isClickableResource(item.meta.resource_type) && resourceComponent && !item.redirect) {
      item.component = modules[`/src/views${resourceComponent}`] as RouteRecordRaw['component']
    }
  })

  // MENU/PAGE that already render a leaf page must not nest other pages as vue-router
  // children — otherwise create/edit/sub-pages stay stuck on the parent CRUD view.
  return hoistLeafPageChildren(arrayToTree(routes))
}

/**
 * Hoist nested page routes out from under leaf MENU/PAGE parents.
 *
 * Vue Router nests by tree shape. A parent with its own component needs a
 * `<router-view>` for children; our list pages don't have one, so hidden form /
 * child-table routes must be siblings instead. parent_id is unchanged so menu
 * highlighting via getActiveMenuPath still works.
 */
function hoistLeafPageChildren(routes: AppRoute.Route[]): AppRoute.Route[] {
  const result: AppRoute.Route[] = []
  for (const route of routes) {
    if (route.children?.length) {
      route.children = hoistLeafPageChildren(route.children)
    }
    const hasLeafComponent = Boolean(route.component) && isClickableResource(route.meta.resource_type)
    if (hasLeafComponent && route.children?.length) {
      const nested = route.children
      route.children = undefined
      result.push(route)
      result.push(...nested)
      continue
    }
    result.push(route)
  }
  return result
}

function createRouteName(resource: AppRoute.RowRoute) {
  return resource.module_id ? `${resource.module_id}:${resource.code}` : resource.code
}

function isFullscreenResource(resource: AppRoute.RowRoute) {
  return resource.layout === 'fullscreen'
}

/**
 * 把内部路由节点转换为菜单节点。
 *
 * 菜单 key 使用 path，保证 Naive UI 菜单选中态和路由路径保持一致。
 */
function transformRoutesToMenus(routes: AppRoute.Route[]): AppRoute.MenuOption[] {
  return routes
    .sort((a, b) => (a.meta.sort ?? 99) - (b.meta.sort ?? 99))
    .map((item) => {
      const label = () => item.meta.name ?? String(item.name)
      const menu: AppRoute.MenuOption = {
        key: item.path,
        label: isClickableResource(item.meta.resource_type)
          ? () =>
              h(
                RouterLink,
                {
                  to: {
                    path: item.path,
                  },
                },
                { default: label },
              )
          : label,
        icon: item.meta.icon ? renderIcon(item.meta.icon) : undefined,
      }

      // 轻量菜单类型额外保留资源 id/parent_id，供 arrayToTree 组装父子关系。
      Reflect.set(menu, 'id', item.id)
      Reflect.set(menu, 'parent_id', item.parent_id)

      return menu
    })
}

/**
 * 为目录节点补默认重定向。
 *
 * 后端未配置 redirect 时，自动跳转到第一个可见子节点；子节点按 sort 升序选择。
 */
function setRedirect(routes: AppRoute.Route[]) {
  routes.forEach((route) => {
    if (!route.children?.length) {
      return
    }

    if (!route.redirect) {
      const visibleChildren = route.children.filter((child) => child.meta.is_visible)
      const target = [...visibleChildren].sort(
        (a, b) => (a.meta.sort ?? 99) - (b.meta.sort ?? 99),
      )[0]

      if (target) {
        route.redirect = target.path
      }
    }

    setRedirect(route.children)
  })
}

/**
 * 把扁平资源列表转换成树。
 *
 * 使用 id/parent_id 建立父子关系；找不到父节点的资源会被视为根节点，避免异常数据导致菜单丢失。
 */
function arrayToTree<T extends { id?: string; parent_id?: string | null; children?: T[] }>(
  items: T[],
) {
  const nodeMap = new Map<string, T>()
  const tree: T[] = []

  items.forEach((item) => {
    if (item.id !== undefined) {
      nodeMap.set(item.id, item)
    }
  })

  items.forEach((item) => {
    if (item.parent_id === null || item.parent_id === undefined || !nodeMap.has(item.parent_id)) {
      tree.push(item)
      return
    }

    const parent = nodeMap.get(item.parent_id)
    if (!parent) {
      tree.push(item)
      return
    }

    parent.children = parent.children ?? []
    parent.children.push(item)
  })

  return tree
}

/**
 * 将扁平资源列表按 module_id 分组为 ResourceModule[]。
 *
 * 模块元信息（name、code、client 等）从资源附带的 module_id_name 推导，
 * icon、color、sort 使用默认值。后续可以从独立模块接口补充。
 */
export function groupResourcesByModule(resources: AppRoute.RowRoute[]): AppRoute.ResourceModule[] {
  const moduleMap = new Map<
    string,
    {
      id: string
      name: string
      code: string
      client: 'ADMIN' | 'PORTAL'
      icon: string | null
      color: string | null
      sort: number
      resources: AppRoute.RowRoute[]
    }
  >()

  for (const resource of resources) {
    if (!resource.module_id) continue
    if (!moduleMap.has(resource.module_id)) {
      moduleMap.set(resource.module_id, {
        id: resource.module_id,
        name: resource.module_id_name ?? resource.module_id,
        code: resource.module_id_name ?? resource.module_id,
        client: 'ADMIN',
        icon: null,
        color: null,
        sort: 99,
        resources: [],
      })
    }
    moduleMap.get(resource.module_id)!.resources.push(resource)
  }

  return Array.from(moduleMap.values()).sort((a, b) => a.sort - b.sort)
}
