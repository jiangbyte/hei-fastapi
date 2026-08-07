/** Author: Charlie */

import { defineStore } from 'pinia'
import { router } from '@/router'
import { authApi } from '@/api'
import { clearDict, refreshDict, syncDictTree } from '@/utils/dict'
import { useRouteStore } from './route'
import { useTabStore } from './tab'

interface AuthUserInfo {
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
  permissionKeys: string[]
  buttonCodes: string[]
  profile?: Record<string, unknown> | null
  loginAt: number
}

interface AuthState {
  userInfo: AuthUserInfo | null
  sessionChecked: boolean
}

const userInfoKey = 'userInfo'
const loginPath = '/auth/login'
const userCenterPasswordPath = '/usercenter?tab=password'

function getStoredUserInfo() {
  const raw = localStorage.getItem(userInfoKey)
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as AuthUserInfo
  } catch {
    localStorage.removeItem(userInfoKey)
    return null
  }
}

function getSafeRedirect(redirect?: string) {
  if (!redirect || redirect.startsWith('/auth')) {
    return import.meta.env.VITE_HOME_PATH
  }
  return redirect
}

export const useAuthStore = defineStore('auth-store', {
  state: (): AuthState => ({
    userInfo: getStoredUserInfo(),
    sessionChecked: false,
  }),
  getters: {
    isLogin: (state) => Boolean(state.userInfo?.accountId),
  },
  actions: {
    async ensureSession() {
      if (this.sessionChecked) {
        return this.isLogin
      }
      this.sessionChecked = true
      try {
        await this.refreshUserInfo()
        return true
      } catch {
        this.clearAuthStorage()
        return false
      }
    },

    async login(
      account: string,
      password: string,
      redirect?: string,
      rememberMe?: boolean,
      identityType = 'ACCOUNT',
      security?: { password_key_id: string; captcha_id: string; captcha_value: string },
    ): Promise<
      | { mfaRequired: true; challengeId: string; webauthnOptions?: Record<string, unknown> | null }
      | { mfaRequired: false }
    > {
      const response = await authApi.login({
        account,
        password,
        identity_type: identityType,
        remember_me: rememberMe ?? true,
        password_key_id: security?.password_key_id,
        captcha_id: security?.captcha_id,
        captcha_value: security?.captcha_value,
      })
      if (response.data?.mfa_required && response.data?.challenge_id) {
        return {
          mfaRequired: true,
          challengeId: String(response.data.challenge_id),
          webauthnOptions: response.data.webauthn_options ?? null,
        }
      }

      this.sessionChecked = true

      const passwordExpired = response.data.password_expired ?? false
      if (passwordExpired) {
        await this.finishLogin(userCenterPasswordPath)
        return { mfaRequired: false }
      }

      await this.finishLogin(redirect)
      return { mfaRequired: false }
    },

    async completeMfaLogin(
      challengeId: string,
      code: string,
      redirect?: string,
      webauthnCredential?: Record<string, unknown>,
    ) {
      const response = await authApi.loginMfa({
        challenge_id: challengeId,
        code: code || undefined,
        webauthn_credential: webauthnCredential,
      })
      this.sessionChecked = true
      if (response.data.password_expired) {
        await this.finishLogin(userCenterPasswordPath)
        return
      }
      await this.finishLogin(redirect)
    },

    async finishLogin(redirect?: string) {
      await this.refreshUserInfo()

      const routeStore = useRouteStore()
      await routeStore.initAuthRoute()
      syncDictTree()
      await refreshDict()
      await router.push(getSafeRedirect(redirect))
    },

    async refreshUserInfo() {
      const meResponse = await authApi.me()
      const userInfo: AuthUserInfo = {
        ...(this.userInfo ?? { loginAt: Date.now() }),
        accountId: meResponse.data.account_id,
        account: meResponse.data.account,
        accountType: meResponse.data.account_type,
        name: meResponse.data.name,
        nickname: meResponse.data.nickname,
        avatar: meResponse.data.avatar,
        roleIds: meResponse.data.role_ids ?? [],
        deptIds: meResponse.data.dept_ids ?? [],
        groupIds: meResponse.data.group_ids ?? [],
        roleIdNames: meResponse.data.role_id_names ?? [],
        deptIdNames: meResponse.data.dept_id_names ?? [],
        groupIdNames: meResponse.data.group_id_names ?? [],
        permissionKeys: meResponse.data.permission_keys ?? [],
        buttonCodes: meResponse.data.button_codes ?? [],
        profile: meResponse.data.profile ?? null,
        loginAt: this.userInfo?.loginAt ?? Date.now(),
      }

      localStorage.setItem(userInfoKey, JSON.stringify(userInfo))
      this.userInfo = userInfo
      return meResponse.data
    },

    hasPermission(permissionKey: string) {
      const keys = this.userInfo?.permissionKeys ?? []
      const buttonCodes = this.userInfo?.buttonCodes ?? []
      return (
        keys.includes('*:*:*') ||
        keys.includes(permissionKey) ||
        buttonCodes.includes(permissionKey)
      )
    },

    clearAuthStorage() {
      localStorage.removeItem(userInfoKey)
      this.userInfo = null
    },

    resetSession() {
      this.clearAuthStorage()
      this.sessionChecked = true

      const routeStore = useRouteStore()
      routeStore.resetRouteStore()

      const tabStore = useTabStore()
      tabStore.clearAllTabs()

      clearDict()
    },

    async logout(redirect?: string) {
      const currentRoute = router.currentRoute.value
      const finalRedirect = redirect ?? currentRoute.fullPath

      try {
        await authApi.logout()
      } catch {
        // 后端登出失败不阻塞本地会话清理。
      } finally {
        this.resetSession()
      }

      await router.push({
        path: loginPath,
        query: finalRedirect.startsWith('/auth') ? undefined : { redirect: finalRedirect },
      })
    },
  },
})
