import { http } from '@/utils'

const prefix = '/api/v1/portal'

export function captcha(format: 'svg' | 'png' = 'svg') {
  return http.get<any>(`${prefix}/captcha`, { params: { format }, addToken: false })
}

export function passwordKey() {
  return http.get<any>(`${prefix}/password-key`, { addToken: false })
}

export function login(data: any) {
  return http.post<any>(`${prefix}/login`, data, { addToken: false })
}

export function register(data: any) {
  return http.post<any>(`${prefix}/register`, data, { addToken: false })
}

export function forgotPassword(data: any) {
  return http.post<any>(`${prefix}/forgot-password`, data, { addToken: false })
}

export function resetPassword(data: any) {
  return http.post<any>(`${prefix}/reset-password`, data, { addToken: false })
}

export function me() {
  return http.get<any>(`${prefix}/me`)
}

export function logout() {
  return http.post<any>(`${prefix}/logout`)
}

export function updateUserCenterProfile(data: any) {
  return http.post<any>(`${prefix}/user-center/profile/update`, data)
}

export function updateUserCenterPassword(data: any) {
  return http.post<any>(`${prefix}/user-center/password/update`, data)
}

export function updateUserCenterPhone(data: any) {
  return http.post<any>(`${prefix}/user-center/phone/update`, data)
}

export function updateUserCenterEmail(data: any) {
  return http.post<any>(`${prefix}/user-center/email/update`, data)
}

export function uploadUserCenterAvatar(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<any>(`${prefix}/user-center/avatar/upload`, formData)
}

export function getPublicSpace(accountId: string) {
  return http.get<any>(`${prefix}/spaces/detail`, {
    addToken: false,
    params: { account_id: accountId },
  })
}
