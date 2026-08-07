/** Author: Charlie */

import { useEffect, useState } from 'react'
import { Avatar, Empty, Spin } from 'antd'
import { UserOutlined } from '@ant-design/icons'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import { resolveFileUrl } from '@/utils/file'
import { authApi } from '@/api'

export function ProfilePage() {
  const [params] = useSearchParams()
  const userInfo = useAuthStore((s) => s.userInfo)
  const accountId = params.get('account_id') || userInfo?.accountId || ''
  const isSelf = Boolean(userInfo?.accountId && accountId === userInfo.accountId)

  const [loading, setLoading] = useState(true)
  const [profile, setProfile] = useState<any>(null)

  useEffect(() => {
    if (!accountId) {
      setLoading(false)
      setProfile(null)
      return
    }
    void (async () => {
      setLoading(true)
      try {
        const spaceRes = await authApi.getPublicSpace(accountId)
        setProfile(spaceRes.data)
      } catch {
        setProfile(null)
      } finally {
        setLoading(false)
      }
    })()
  }, [accountId])

  const displayName =
    profile?.nickname ||
    profile?.name ||
    (isSelf ? userInfo?.nickname || userInfo?.name || userInfo?.account : null) ||
    '未命名用户'
  const avatarSrc = resolveFileUrl(profile?.avatar || (isSelf ? userInfo?.avatar : null))
  const signature = profile?.signature?.trim() || ''

  if (!accountId) {
    return (
      <div className="page-shell py-20">
        <Empty description="请先登录查看个人主页" />
      </div>
    )
  }

  return (
    <div className="page-shell">
      <Spin spinning={loading}>
        <div className="panel mx-auto max-w-xl rounded-xl p-8">
          {profile || isSelf ? (
            <div className="flex flex-col items-center text-center">
              <Avatar size={96} src={avatarSrc || undefined} icon={<UserOutlined />} />
              <div className="mt-4 text-xl font-semibold">{displayName}</div>
              {signature ? <div className="muted-text mt-2 text-sm">{signature}</div> : null}
              {isSelf ? (
                <Link to="/usercenter" className="mt-5 text-sm text-[var(--ant-color-primary)]">
                  编辑个人资料 / 账号设置
                </Link>
              ) : null}
            </div>
          ) : (
            <Empty description="用户不存在或资料未公开" />
          )}
        </div>
      </Spin>
    </div>
  )
}
