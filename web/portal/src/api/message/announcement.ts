import { http } from '@/utils'

const prefix = '/api/v1/portal'

export const announcementApi = {
  list: (params?: any) =>
    http.get<any>(`${prefix}/message/announcements/list`, {
      params,
      // 有 token 时带上，便于填充 is_read；无 token 也可访问
    }),
  myDetail: (id: string) =>
    http.get<any>(`${prefix}/message/announcements/my-detail`, {
      params: { id },
    }),
  read: (ids: string[]) =>
    http.post<any>(`${prefix}/message/announcements/read`, { ids }),
}
