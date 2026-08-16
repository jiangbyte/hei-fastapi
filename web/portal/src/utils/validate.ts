/** Author: Charlie */

export function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())
}

export function isValidPhone(value: string) {
  return /^1\d{10}$/.test(value.trim())
}

/**
 * 仅允许同源相对路径：以单个 / 开头，禁止 // 与 /auth 前缀。
 */
export function getSafeRedirect(redirect?: string | null) {
  const home = import.meta.env.VITE_HOME_PATH || '/'
  const value = String(redirect ?? '').trim()
  if (!value) {
    return home
  }
  if (!value.startsWith('/') || value.startsWith('//') || value.startsWith('/auth')) {
    return home
  }
  if (value.includes('://')) {
    return home
  }
  return value
}
