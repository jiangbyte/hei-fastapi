import { authApi } from '@/api'

export async function encryptPasswords<T extends Record<string, string | null | undefined>>(
  fields: T,
) {
  const response = await authApi.passwordKey()
  const publicKey = await importPublicKey(response.data.public_key)
  const result: Record<string, string | null> = {}

  for (const [key, value] of Object.entries(fields)) {
    result[key] = value ? await encryptText(publicKey, value) : null
  }

  return {
    password_key_id: response.data.key_id,
    values: result as { [K in keyof T]: string | null },
  }
}

async function importPublicKey(pem: string) {
  const binary = window.atob(
    pem
      .replace('-----BEGIN PUBLIC KEY-----', '')
      .replace('-----END PUBLIC KEY-----', '')
      .replace(/\s/g, ''),
  )
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return window.crypto.subtle.importKey(
    'spki',
    bytes.buffer,
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    false,
    ['encrypt'],
  )
}

async function encryptText(publicKey: CryptoKey, value: string) {
  const encrypted = await window.crypto.subtle.encrypt(
    { name: 'RSA-OAEP' },
    publicKey,
    new TextEncoder().encode(value),
  )
  return arrayBufferToBase64(encrypted)
}

function arrayBufferToBase64(buffer: ArrayBuffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let index = 0; index < bytes.byteLength; index += 1) {
    binary += String.fromCharCode(bytes[index])
  }
  return window.btoa(binary)
}
