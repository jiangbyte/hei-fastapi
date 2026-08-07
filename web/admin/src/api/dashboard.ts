/** Author: Charlie */

import { http } from '@/utils'

const prefix = '/api/v1/admin/dashboard'

export function overview() {
  return http.get<any>(`${prefix}/overview`)
}
