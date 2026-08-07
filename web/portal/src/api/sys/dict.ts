/** Author: Charlie */

import { http } from '@/utils'

const dictPrefix = '/api/v1/portal/sys/dicts'

export function tree(params?: { category?: string }) {
  // 门户字典公开接口（public：401 不跳登录）
  return http.get<any[]>(`${dictPrefix}/tree`, { params, public: true })
}
