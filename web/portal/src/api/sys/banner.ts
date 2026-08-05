import { http } from '@/utils'

const bannerPrefix = '/api/v1/portal/sys/banners'

/** 门户公开展示图列表（不携带 token） */
export function listBanners(params: any) {
  return http.get<any>(`${bannerPrefix}/list`, {
    params,
    addToken: false,
  })
}

/** 记录展示图点击交互 */
export function recordBannerInteraction(id: string) {
  return http.post<any>(
    `${bannerPrefix}/interaction`,
    { id },
    { addToken: false },
  )
}
