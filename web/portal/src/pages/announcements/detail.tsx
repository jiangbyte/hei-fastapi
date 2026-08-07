/** Author: Charlie */

import { useEffect, useMemo, useState } from 'react'
import { Button, Empty, Skeleton, Tag } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { Link, useParams } from 'react-router-dom'
import DOMPurify from 'dompurify'
import { Markdown } from '@/components/common/Markdown'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/time'
import { readPageMeta } from '@/utils/wire'
import { announcementApi } from '@/api'

async function findAnnouncementById(id: string) {
  const pageSize = 50
  let current = 1
  let total = Infinity

  while ((current - 1) * pageSize < total) {
    const res = await announcementApi.list({ current, size: pageSize })
    const records = res.data.records ?? []
    total = readPageMeta(res.data).total
    const found = records.find((row: any) => String(row.id) === String(id))
    if (found) return found
    if (!records.length) break
    current += 1
  }
  return null
}

export function AnnouncementDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isLogin = useAuthStore((s) => s.isLogin)
  const loggedIn = isLogin()

  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState<any>(null)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!id) {
      setNotFound(true)
      setLoading(false)
      return
    }

    let mounted = true

    async function load() {
      setLoading(true)
      setNotFound(false)
      try {
        let item: any = null
        if (isLogin()) {
          try {
            const res = await announcementApi.myDetail(id!)
            item = res.data
          } catch {
            // 回退到公开列表查找
          }
        }

        if (!item) {
          item = await findAnnouncementById(id!)
        }

        if (!mounted) return
        if (!item) {
          setDetail(null)
          setNotFound(true)
          return
        }

        setDetail(item)

        if (isLogin() && !item.is_read) {
          try {
            await announcementApi.read([item.id])
            if (mounted) setDetail((curr: any) => (curr ? { ...curr, is_read: true } : curr))
          } catch {
            // 标已读失败不影响阅读
          }
        }
      } catch {
        if (!mounted) return
        setDetail(null)
        setNotFound(true)
      } finally {
        if (mounted) setLoading(false)
      }
    }

    void load()
    return () => {
      mounted = false
    }
  }, [id, loggedIn])

  return (
    <div className="page-shell">
      <div className="mb-4">
        <Link to="/announcements">
          <Button type="text" icon={<ArrowLeftOutlined />} className="!px-0">
            返回公告列表
          </Button>
        </Link>
      </div>

      <section className="panel rounded-xl p-5 md:p-8">
        <Skeleton active loading={loading} paragraph={{ rows: 8 }}>
          {detail ? (
            <article>
              <h1 className="text-xl font-semibold md:text-2xl">{detail.title}</h1>
              <div className="muted-text mt-3 flex flex-wrap items-center gap-2 text-xs">
                {detail.is_pinned ? <Tag color="warning">置顶</Tag> : null}
                {detail.publish_at ? <span>发布于 {formatDateTime(detail.publish_at)}</span> : null}
              </div>
              <div className="mt-6 border-t border-[var(--ant-color-border)] pt-6">
                {detail.content_type === 'html' ? (
                  <div
                    className="prose max-w-none text-sm leading-7"
                    dangerouslySetInnerHTML={{
                      __html: DOMPurify.sanitize(detail.content || ''),
                    }}
                  />
                ) : detail.content_type === 'markdown' ? (
                  <Markdown content={detail.content || ''} />
                ) : (
                  <div className="whitespace-pre-wrap text-sm leading-7 text-[var(--ant-color-text)]">
                    {detail.content}
                  </div>
                )}
              </div>
            </article>
          ) : notFound ? (
            <Empty description="公告不存在或已下线">
              <Link to="/announcements">
                <Button type="primary">返回列表</Button>
              </Link>
            </Empty>
          ) : null}
        </Skeleton>
      </section>
    </div>
  )
}
