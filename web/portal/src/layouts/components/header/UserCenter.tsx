import { useEffect } from 'react'
import { Avatar, Badge, Button, Dropdown, Modal, Space, Tooltip, Typography, message } from 'antd'
import {
  HomeOutlined,
  LogoutOutlined,
  MessageOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import type { DropdownProps, MenuProps } from 'antd'
import { useLocation, useNavigate } from 'react-router-dom'
import { useImWebSocket } from '@/hooks/useImWebSocket'
import { resolveFileUrl } from '@/utils/file'
import { useAuthStore } from '@/stores/auth'
import { useImUnreadStore } from '@/stores/imUnread'

type Props = {
  compact?: boolean
  placement?: DropdownProps['placement']
}

export function UserCenter({ compact = false, placement = 'bottomRight' }: Props) {
  const navigate = useNavigate()
  const location = useLocation()
  const token = useAuthStore((s) => s.token)
  const userInfo = useAuthStore((s) => s.userInfo)
  const logout = useAuthStore((s) => s.logout)
  const messageUnread = useImUnreadStore((s) => s.messageUnread)
  const friendRequestPending = useImUnreadStore((s) => s.friendRequestPending)
  const joinRequestPending = useImUnreadStore((s) => s.joinRequestPending)
  const refreshUnread = useImUnreadStore((s) => s.refresh)
  const bumpMessage = useImUnreadStore((s) => s.bumpMessage)
  const bumpFriendRequest = useImUnreadStore((s) => s.bumpFriendRequest)
  const bumpJoinRequest = useImUnreadStore((s) => s.bumpJoinRequest)
  const resetUnread = useImUnreadStore((s) => s.reset)

  const badgeTotal = messageUnread + friendRequestPending + joinRequestPending

  useEffect(() => {
    if (!token) {
      resetUnread()
      return
    }
    void refreshUnread()
  }, [token, location.pathname, refreshUnread, resetUnread])

  useImWebSocket(Boolean(token), {
    onNewMessage: () => {
      bumpMessage(1)
      void refreshUnread()
    },
    onOfflineMessages: () => {
      void refreshUnread()
    },
    onNewFriendRequest: () => {
      bumpFriendRequest(1)
      void refreshUnread()
    },
    onNewJoinRequest: () => {
      bumpJoinRequest(1)
      void refreshUnread()
    },
  })

  if (!token) {
    if (compact) {
      return (
        <Tooltip title="登录" placement="right">
          <Button
            type="text"
            className="!h-10 !w-10 !px-0"
            icon={<UserOutlined />}
            aria-label="登录"
            onClick={() => navigate('/auth/login')}
          />
        </Tooltip>
      )
    }

    return (
      <Space size={8}>
        <Button onClick={() => navigate('/auth/register')}>注册</Button>
        <Button type="primary" onClick={() => navigate('/auth/login')}>
          登录
        </Button>
      </Space>
    )
  }

  const displayName = userInfo?.nickname || userInfo?.account || '用户'
  const avatarSrc = resolveFileUrl(userInfo?.avatar)

  const items: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人主页',
    },
    {
      key: 'userCenter',
      icon: <SettingOutlined />,
      label: '账号设置',
    },
    { type: 'divider' },
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
    },
  ]

  const onClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'profile') {
      navigate('/profile')
      return
    }
    if (key === 'userCenter') {
      navigate('/usercenter')
      return
    }
    if (key === 'home') {
      navigate('/')
      return
    }
    if (key === 'logout') {
      Modal.confirm({
        title: '退出登录',
        content: '确定退出当前账号？',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
          await logout(location.pathname)
          resetUnread()
          message.success('已退出登录')
        },
      })
    }
  }

  const messageIcon = (
    <Tooltip
      title={
        friendRequestPending + joinRequestPending > 0
          ? `好友申请 ${friendRequestPending} · 入群申请 ${joinRequestPending}`
          : badgeTotal > 0
            ? `${badgeTotal} 条未读`
            : '消息'
      }
      placement={compact ? 'right' : undefined}
    >
      <Badge count={badgeTotal} size="small" offset={[-2, 2]}>
        <Button
          type="text"
          className={compact ? '!h-10 !w-10 !px-0' : undefined}
          icon={<MessageOutlined />}
          aria-label="消息"
          onClick={() => navigate('/messages')}
        />
      </Badge>
    </Tooltip>
  )

  const avatarBtn = (
    <Dropdown menu={{ items, onClick }} trigger={['click']} placement={placement}>
      <Space className="cursor-pointer select-none" size={8}>
        <Avatar src={avatarSrc} icon={<UserOutlined />} size={compact ? 32 : 'default'} />
        {compact ? null : (
          <Typography.Text className="hidden max-w-28 truncate md:inline">
            {displayName}
          </Typography.Text>
        )}
      </Space>
    </Dropdown>
  )

  if (compact) {
    return (
      <div className="flex flex-col items-center gap-2">
        {messageIcon}
        {avatarBtn}
      </div>
    )
  }

  return (
    <Space size={8}>
      {messageIcon}
      {avatarBtn}
    </Space>
  )
}
