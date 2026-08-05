import { create } from 'zustand'
import { message } from 'antd'
import { authApi } from '@/api'
import { refreshDict, syncDictTree } from '@/utils/dict'
import {
  clearAuthStorage,
  getStoredUserInfo,
  getToken,
  setStoredUserInfo,
  setToken,
} from '@/utils/storage'
import { getSafeRedirect } from '@/utils/validate'

export interface AuthUserInfo {
  accountId: string
  account: string
  accountType: string
  name?: string | null
  nickname?: string | null
  avatar?: string | null
  roleIds: string[]
  deptIds: string[]
  groupIds: string[]
  roleIdNames?: { id: string; name: string }[]
  deptIdNames?: { id: string; name: string }[]
  groupIdNames?: { id: string; name: string }[]
  profile?: Record<string, unknown> | null
  loginAt: number
}

interface AuthState {
  token: string
  userInfo: AuthUserInfo | null
  isLogin: () => boolean
  login: (
    account: string,
    password: string,
    redirect?: string,
    rememberMe?: boolean,
    identityType?: string,
    security?: { password_key_id: string; captcha_id: string; captcha_value: string },
  ) => Promise<string>
  refreshUserInfo: () => Promise<any>
  logout: (redirect?: string) => Promise<void>
  resetSession: () => void
}

function mapMe(data: any, loginAt = Date.now()): AuthUserInfo {
  return {
    accountId: data.account_id,
    account: data.account,
    accountType: data.account_type,
    name: data.name,
    nickname: data.nickname,
    avatar: data.avatar,
    roleIds: data.role_ids ?? [],
    deptIds: data.dept_ids ?? [],
    groupIds: data.group_ids ?? [],
    roleIdNames: data.role_id_names ?? [],
    deptIdNames: data.dept_id_names ?? [],
    groupIdNames: data.group_id_names ?? [],
    profile: data.profile ?? null,
    loginAt,
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: getToken(),
  userInfo: getStoredUserInfo<AuthUserInfo>(),

  isLogin: () => Boolean(get().token),

  login: async (
    account,
    password,
    redirect,
    rememberMe = true,
    identityType = 'ACCOUNT',
    security,
  ) => {
    const response = await authApi.login({
      account,
      password,
      identity_type: identityType,
      remember_me: rememberMe,
      password_key_id: security?.password_key_id || '',
      captcha_id: security?.captcha_id || '',
      captcha_value: security?.captcha_value || '',
    })

    const token = response.data.token
    setToken(token)
    set({ token })

    if (response.data.password_expired) {
      message.warning('密码已过期，请登录后尽快修改密码')
    }

    const meResponse = await authApi.me()
    const userInfo = mapMe(meResponse.data)
    setStoredUserInfo(userInfo)
    set({ userInfo })

    syncDictTree()
    await refreshDict()

    return getSafeRedirect(redirect)
  },

  refreshUserInfo: async () => {
    const meResponse = await authApi.me()
    const userInfo = mapMe(meResponse.data, get().userInfo?.loginAt ?? Date.now())
    setStoredUserInfo(userInfo)
    set({ userInfo })
    return meResponse.data
  },

  resetSession: () => {
    // 门户字典公开缓存，登出不清理
    clearAuthStorage()
    set({ token: '', userInfo: null })
  },

  logout: async (redirect) => {
    try {
      await authApi.logout()
    } catch {
      // ignore
    } finally {
      get().resetSession()
    }

    const query =
      redirect && !redirect.startsWith('/auth') ? `?redirect=${encodeURIComponent(redirect)}` : ''
    window.location.assign(`/auth/login${query}`)
  },
}))
