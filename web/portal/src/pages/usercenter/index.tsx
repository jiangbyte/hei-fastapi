import { useEffect, useState } from 'react'
import {
  Avatar,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Form,
  Input,
  Modal,
  Row,
  Spin,
  Switch,
  Tabs,
  Typography,
  message,
} from 'antd'
import { UserOutlined } from '@ant-design/icons'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { encryptPasswords } from '@/utils/security'
import { resolveFileUrl } from '@/utils/file'
import { isValidEmail } from '@/utils/validate'
import { PasswordStrength } from '@/components/common/PasswordStrength'
import { AvatarUploadModal } from './components/AvatarUploadModal'
import './usercenter.css'

const mapNames = (items?: { id: string; name: string }[]) =>
  (items ?? []).map((item) => item.name).filter(Boolean).join(' / ')

const displayValue = (value: unknown) => (value ? String(value) : '未设置')

type BindConfirmState = {
  show: boolean
  type: 'phone' | 'email'
  password: string
  loading: boolean
}

export function UserCenterPage() {
  const refreshUserInfo = useAuthStore((s) => s.refreshUserInfo)

  const [loading, setLoading] = useState(true)
  const [me, setMe] = useState<any>(null)
  const [avatarModalShow, setAvatarModalShow] = useState(false)

  const [profileForm] = Form.useForm()
  const [passwordForm] = Form.useForm()
  const [phoneForm] = Form.useForm()
  const [emailForm] = Form.useForm()

  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)
  const [savingBind, setSavingBind] = useState(false)

  const newPassword = Form.useWatch('new_password', passwordForm) || ''

  const [bindConfirm, setBindConfirm] = useState<BindConfirmState>({
    show: false,
    type: 'phone',
    password: '',
    loading: false,
  })

  useEffect(() => {
    void loadMe()
  }, [])

  async function loadMe() {
    setLoading(true)
    try {
      await refreshMe()
    } finally {
      setLoading(false)
    }
  }

  async function refreshMe() {
    const data = await refreshUserInfo()
    setMe(data)
    syncForms(data)
  }

  function syncForms(data: any) {
    const profile = (data.profile ?? {}) as any
    profileForm.setFieldsValue({
      name: data.name ?? profile.name ?? '',
      nickname: data.nickname ?? profile.nickname ?? '',
      signature: profile.signature ?? '',
    })
    phoneForm.setFieldsValue({
      phone: profile.phone ?? '',
      phone_login_enabled: Boolean(profile.phone_login_enabled),
    })
    emailForm.setFieldsValue({
      email: profile.email ?? '',
      email_login_enabled: Boolean(profile.email_login_enabled),
    })
  }

  async function saveProfile() {
    setSavingProfile(true)
    try {
      const values = await profileForm.validateFields()
      await authApi.updateUserCenterProfile({
        name: values.name || null,
        nickname: values.nickname || null,
        signature: values.signature || null,
      })
      await refreshMe()
      message.success('保存成功')
    } finally {
      setSavingProfile(false)
    }
  }

  async function savePassword() {
    const values = await passwordForm.validateFields()
    if (values.new_password !== values.confirm_password) {
      message.warning('两次输入的新密码不一致')
      return
    }
    setSavingPassword(true)
    try {
      const encrypted = await encryptPasswords({
        old_password: values.old_password,
        new_password: values.new_password,
      })
      await authApi.updateUserCenterPassword({
        old_password: encrypted.values.old_password || '',
        new_password: encrypted.values.new_password || '',
        password_key_id: encrypted.password_key_id,
      })
      passwordForm.resetFields()
      message.success('密码已更新')
    } finally {
      setSavingPassword(false)
    }
  }

  async function savePhone() {
    await phoneForm.validateFields()
    openBindConfirm('phone')
  }

  async function saveEmail() {
    const values = await emailForm.validateFields()
    const email = (values.email ?? '').trim()
    if (email && !isValidEmail(email)) {
      message.warning('请输入有效邮箱')
      return
    }
    openBindConfirm('email')
  }

  function openBindConfirm(type: 'phone' | 'email') {
    setBindConfirm({ show: true, type, password: '', loading: false })
  }

  async function confirmBind() {
    if (!bindConfirm.password) {
      message.warning('请输入当前密码')
      return
    }
    setBindConfirm((s) => ({ ...s, loading: true }))
    setSavingBind(true)
    try {
      const encrypted = await encryptPasswords({ password: bindConfirm.password })
      if (bindConfirm.type === 'phone') {
        const values = phoneForm.getFieldsValue()
        await authApi.updateUserCenterPhone({
          password: encrypted.values.password || '',
          password_key_id: encrypted.password_key_id,
          phone: values.phone || null,
          phone_login_enabled: Boolean(values.phone_login_enabled),
        })
      } else {
        const values = emailForm.getFieldsValue()
        await authApi.updateUserCenterEmail({
          password: encrypted.values.password || '',
          password_key_id: encrypted.password_key_id,
          email: (values.email ?? '').trim() || null,
          email_login_enabled: Boolean(values.email_login_enabled),
        })
      }
      setBindConfirm((s) => ({ ...s, show: false, password: '' }))
      await refreshMe()
      message.success('绑定已更新')
    } finally {
      setBindConfirm((s) => ({ ...s, loading: false }))
      setSavingBind(false)
    }
  }

  const profile = (me?.profile ?? {}) as any
  const displayName = me?.nickname || me?.name || '-'
  const avatarUrl = resolveFileUrl(me?.avatar || profile.avatar)
  const roleNames = mapNames(me?.role_id_names)
  const contactParts = [profile.phone, profile.email].filter(Boolean)
  const contactText = contactParts.length ? contactParts.join(' / ') : '未设置'

  const tabItems = [
    {
      key: 'basic_info',
      label: '基本信息',
      children: (
        <Form form={profileForm} layout="vertical" className="max-w-140 min-w-0">
          <Form.Item label="账号">
            <Input value={me?.account} disabled />
          </Form.Item>
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ max: 64, message: '姓名最多 64 个字符' }]}
          >
            <Input placeholder="请输入姓名" allowClear />
          </Form.Item>
          <Form.Item
            name="nickname"
            label="昵称"
            rules={[{ max: 64, message: '昵称最多 64 个字符' }]}
          >
            <Input placeholder="请输入昵称" allowClear />
          </Form.Item>
          <Form.Item name="signature" label="个性签名">
            <Input.TextArea rows={3} placeholder="介绍一下自己" allowClear />
          </Form.Item>
          <Form.Item>
            <Button type="primary" loading={savingProfile} onClick={() => void saveProfile()}>
              保存
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'password',
      label: '密码',
      children: (
        <Form form={passwordForm} layout="vertical" className="max-w-140 min-w-0">
          <Form.Item
            name="old_password"
            label="旧密码"
            rules={[{ required: true, message: '请输入旧密码' }]}
          >
            <Input.Password placeholder="请输入旧密码" />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[{ required: true, message: '请输入新密码' }]}
          >
            <Input.Password placeholder="至少 8 个字符，含大小写、数字与特殊字符" />
          </Form.Item>
          <PasswordStrength password={newPassword} />
          <Form.Item
            name="confirm_password"
            label="确认密码"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的新密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password placeholder="再次输入新密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" loading={savingPassword} onClick={() => void savePassword()}>
              修改密码
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'phone',
      label: '手机号',
      children: (
        <Form form={phoneForm} layout="vertical" className="max-w-140 min-w-0">
          <Form.Item name="phone" label="手机号">
            <Input placeholder="请输入手机号" allowClear />
          </Form.Item>
          <Form.Item
            name="phone_login_enabled"
            label="启用手机号登录"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
          <Form.Item>
            <Button type="primary" loading={savingBind} onClick={() => void savePhone()}>
              修改手机号
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'email',
      label: '邮箱',
      children: (
        <Form form={emailForm} layout="vertical" className="max-w-140 min-w-0">
          <Form.Item
            name="email"
            label="邮箱"
            rules={[{ type: 'email', message: '邮箱格式不正确' }]}
          >
            <Input placeholder="your@example.com" allowClear />
          </Form.Item>
          <Form.Item
            name="email_login_enabled"
            label="启用邮箱登录"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
          <Form.Item>
            <Button type="primary" loading={savingBind} onClick={() => void saveEmail()}>
              修改邮箱
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ]

  return (
    <div className="w-full min-w-0">
      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={7} className="min-w-0">
            <Card className="h-full" styles={{ body: { minWidth: 0 } }}>
              <div className="flex flex-col items-center text-center">
                <button
                  type="button"
                  className="avatar-trigger"
                  title="更换头像"
                  onClick={() => setAvatarModalShow(true)}
                >
                  <Avatar
                    size={104}
                    src={avatarUrl}
                    icon={<UserOutlined />}
                    style={{ display: 'block' }}
                  />
                </button>
                <div className="mt-4 max-w-full truncate text-xl font-medium">
                  {displayName}
                </div>
                <div className="mt-1 max-w-full truncate text-sm text-[var(--ant-color-text-secondary)]">
                  {me?.account}
                </div>
              </div>

              <Divider />

              <Descriptions column={1} labelStyle={{ width: 72 }}>
                <Descriptions.Item label="角色">
                  {roleNames || '未设置'}
                </Descriptions.Item>
                <Descriptions.Item label="联系方式">{contactText}</Descriptions.Item>
              </Descriptions>

              <Divider />

              <div className="text-sm font-medium">个性签名</div>
              <div className="mt-2 min-h-16 rounded border border-[var(--ant-color-border)] p-3 text-sm text-[var(--ant-color-text-secondary)]">
                {displayValue(profile.signature)}
              </div>
            </Card>
          </Col>

          <Col xs={24} lg={17} className="min-w-0">
            <Card className="w-full min-w-0" styles={{ body: { minWidth: 0 } }}>
              <Tabs items={tabItems} />
            </Card>
          </Col>
        </Row>
      </Spin>

      <Modal
        open={bindConfirm.show}
        title={bindConfirm.type === 'phone' ? '确认更新手机号' : '确认更新邮箱'}
        okText="确认"
        cancelText="取消"
        confirmLoading={bindConfirm.loading}
        maskClosable={false}
        onOk={() => void confirmBind()}
        onCancel={() => setBindConfirm((s) => ({ ...s, show: false }))}
      >
        <Form layout="vertical">
          <Form.Item label="当前密码">
            <Input.Password
              value={bindConfirm.password}
              placeholder="请输入当前密码"
              onChange={(e) => setBindConfirm((s) => ({ ...s, password: e.target.value }))}
              onPressEnter={() => void confirmBind()}
            />
          </Form.Item>
        </Form>
        <Typography.Text type="secondary">
          为保障账号安全，修改{bindConfirm.type === 'phone' ? '手机号' : '邮箱'}需验证当前密码。
        </Typography.Text>
      </Modal>

      <AvatarUploadModal
        open={avatarModalShow}
        avatar={avatarUrl}
        onClose={() => setAvatarModalShow(false)}
        onUploaded={() => void refreshMe()}
      />
    </div>
  )
}
