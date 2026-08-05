const PUBLIC_FILE_PATH = '/api/v1/files'

function isAbsoluteUrl(value: string) {
  return /^(https?:|data:|blob:)/i.test(value)
}

function toPublicFilePath(value: string) {
  const rawValue = value.trim()
  if (!rawValue || isAbsoluteUrl(rawValue)) {
    return rawValue
  }
  if (rawValue.startsWith(`${PUBLIC_FILE_PATH}?`)) {
    return rawValue
  }
  const legacyPrefix = `${PUBLIC_FILE_PATH}/`
  if (rawValue.startsWith(legacyPrefix)) {
    const objectName = rawValue.slice(legacyPrefix.length).replace(/^\/+/, '')
    return objectName ? `${PUBLIC_FILE_PATH}?object_name=${encodeURIComponent(objectName)}` : PUBLIC_FILE_PATH
  }
  if (!rawValue.startsWith('/')) {
    return `${PUBLIC_FILE_PATH}?object_name=${encodeURIComponent(rawValue)}`
  }
  return rawValue
}

export function resolveFileUrl(value?: string | null) {
  if (!value) {
    return undefined
  }
  const rawValue = String(value).trim()
  if (!rawValue) {
    return undefined
  }
  if (isAbsoluteUrl(rawValue)) {
    return rawValue
  }
  const path = toPublicFilePath(rawValue)
  const baseURL = import.meta.env.VITE_API_URL || ''
  if (!baseURL) {
    return path
  }
  return `${baseURL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`
}

export function isImageFile(
  file?:
    | string
    | null
    | {
        type?: string | null
        name?: string | null
        content_type?: string | null
        url?: string | null
      },
) {
  if (!file) return false
  if (typeof file === 'string') {
    return /\.(png|jpe?g|gif|webp|bmp|svg)(\?|$)/i.test(file)
  }
  const type = file.type || file.content_type || ''
  if (type.startsWith('image/')) return true
  return /\.(png|jpe?g|gif|webp|bmp|svg)(\?|$)/i.test(file.name || file.url || '')
}
