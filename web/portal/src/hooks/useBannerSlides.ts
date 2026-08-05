import { useEffect, useState } from 'react'
import { bannerApi } from '@/api'
import type { PromoSlide } from '@/components/common/PromoCarousel'

function isExternalUrl(url: string) {
  return /^https?:\/\//i.test(url)
}

function bannerToSlide(banner: any): PromoSlide {
  const link = banner.url?.trim() || undefined
  const slide: PromoSlide = {
    key: banner.id,
    title: banner.title,
    desc: banner.summary || banner.description || '',
    imageUrl: banner.image,
    cta: link ? '了解更多' : undefined,
    onClick: () => {
      void bannerApi.recordBannerInteraction(banner.id).catch(() => undefined)
    },
  }

  if (!link || banner.link_type === 'NONE') {
    return slide
  }

  if (banner.link_type === 'ROUTE' || (!isExternalUrl(link) && link.startsWith('/'))) {
    slide.to = link.startsWith('/') ? link : `/${link}`
    return slide
  }

  slide.href = link
  return slide
}

export function useBannerSlides(query: any) {
  const [slides, setSlides] = useState<PromoSlide[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    void bannerApi.listBanners(query)
      .then((res) => {
        if (cancelled) return
        setSlides(res.data.map(bannerToSlide))
      })
      .catch(() => {
        if (!cancelled) setSlides([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
    // position/category/type are stable string literals at call sites
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query.position, query.category, query.type])

  return { slides, loading }
}
