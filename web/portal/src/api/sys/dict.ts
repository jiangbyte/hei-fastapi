import { http } from '@/utils'

const dictPrefix = '/api/v1/portal/sys/dicts'

export function tree(params?: { category?: string }) {
  // 门户字典公开接口，不携带 token，避免过期登录态误伤
  return http.get<any[]>(`${dictPrefix}/tree`, { params, addToken: false })
}
