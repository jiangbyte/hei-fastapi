/** Author: Charlie */

import { http } from '@/utils'

const prefix = '/api/v1/portal'

export const announcementApi = {
  list: (params?: any) =>
    http.get<any>(`${prefix}/message/announcements/list`, {
      params,
      // Cookie 会话存在时可用于填充 is_read；游客也可访问
    }),
  myDetail: (id: string) =>
    http.get<any>(`${prefix}/message/announcements/my-detail`, {
      params: { id },
    }),
  read: (ids: string[]) =>
    http.post<any>(`${prefix}/message/announcements/read`, { ids }),
}
