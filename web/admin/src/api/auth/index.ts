/** Author: Charlie */

import { http } from '@/utils'

const authPrefix = '/api/v1/admin'

export function login(data: any) {
  return http.post<any>(`${authPrefix}/login`, data, {
    public: true,
  })
}

export function loginMfa(data: {
  challenge_id: string
  code?: string
  webauthn_credential?: Record<string, unknown>
}) {
  return http.post<any>(`${authPrefix}/login/mfa`, data, {
    public: true,
  })
}

export function mfaStatus() {
  return http.get<any>(`${authPrefix}/auth/mfa/status`)
}

export function mfaSetup() {
  return http.post<any>(`${authPrefix}/auth/mfa/setup`)
}

export function mfaConfirm(data: { code: string }) {
  return http.post<any>(`${authPrefix}/auth/mfa/confirm`, data)
}

export function mfaDisable(data: any) {
  return http.post<any>(`${authPrefix}/auth/mfa/disable`, data)
}

export function webauthnRegisterOptions() {
  return http.post<any>(`${authPrefix}/auth/mfa/webauthn/register/options`)
}

export function webauthnRegisterVerify(credential: Record<string, unknown>) {
  return http.post<any>(`${authPrefix}/auth/mfa/webauthn/register/verify`, { credential })
}

export function captcha() {
  return http.get<any>(`${authPrefix}/captcha`, {
    public: true,
  })
}

export function passwordKey() {
  return http.get<any>(`${authPrefix}/password-key`, {
    public: true,
  })
}

export function forgotPassword(data: any) {
  return http.post<any>(`${authPrefix}/forgot-password`, data, {
    public: true,
  })
}

export function resetPassword(data: any) {
  return http.post<any>(`${authPrefix}/reset-password`, data, {
    public: true,
  })
}

export function logout() {
  return http.post<any>(`${authPrefix}/logout`)
}

export function me() {
  return http.get<any>(`${authPrefix}/me`)
}

export function updateUserCenterProfile(data: any) {
  return http.post<any>(`${authPrefix}/user-center/profile/update`, data)
}

export function uploadUserCenterAvatar(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<any>(`${authPrefix}/user-center/avatar/upload`, formData)
}

export function updateUserCenterPassword(data: any) {
  return http.post<any>(`${authPrefix}/user-center/password/update`, data)
}

export function updateUserCenterPhone(data: any) {
  return http.post<any>(`${authPrefix}/user-center/phone/update`, data)
}

export function updateUserCenterEmail(data: any) {
  return http.post<any>(`${authPrefix}/user-center/email/update`, data)
}
