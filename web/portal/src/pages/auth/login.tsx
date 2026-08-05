import { useRef, useState } from 'react'
import { Button, Checkbox, ConfigProvider, Form, Input, Tabs, message } from 'antd'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { CaptchaInput, type CaptchaInputHandle } from '@/components/common/CaptchaInput'
import { useAuthStore } from '@/stores/auth'
import { encryptPasswords } from '@/utils/security'
import { isValidEmail, isValidPhone } from '@/utils/validate'
import { AuthSplit } from './AuthSplit'

type LoginType = 'ACCOUNT' | 'EMAIL' | 'PHONE'

type FormValues = {
  account?: string
  email?: string
  phone?: string
  password: string
  captcha_id: string
  captcha_value: string
  remember: boolean
}

const tabItems = [
  { key: 'ACCOUNT', label: '账号', placeholder: '请输入账号' },
  { key: 'EMAIL', label: '邮箱', placeholder: '请输入登录邮箱' },
  { key: 'PHONE', label: '手机号', placeholder: '请输入登录手机号' },
]

export function LoginPage() {
  const [form] = Form.useForm<FormValues>()
  const [activeType, setActiveType] = useState<LoginType>('ACCOUNT')
  const [loading, setLoading] = useState(false)
  const captchaRef = useRef<CaptchaInputHandle>(null)
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const login = useAuthStore((s) => s.login)
  const captchaId = Form.useWatch('captcha_id', form) || ''
  const captchaValue = Form.useWatch('captcha_value', form) || ''

  async function onFinish(values: FormValues) {
    const identity =
      activeType === 'ACCOUNT'
        ? values.account?.trim()
        : activeType === 'EMAIL'
          ? values.email?.trim()
          : values.phone?.trim()

    if (!identity) {
      message.warning(`请输入${tabItems.find((t) => t.key === activeType)?.label}`)
      return
    }
    if (activeType === 'EMAIL' && !isValidEmail(identity)) {
      message.warning('请输入有效邮箱')
      return
    }
    if (activeType === 'PHONE' && !isValidPhone(identity)) {
      message.warning('请输入有效手机号')
      return
    }

    setLoading(true)
    try {
      const encrypted = await encryptPasswords({ password: values.password })
      const redirect = await login(
        identity,
        encrypted.values.password || '',
        params.get('redirect') || undefined,
        values.remember,
        activeType,
        {
          password_key_id: encrypted.password_key_id,
          captcha_id: values.captcha_id,
          captcha_value: values.captcha_value,
        },
      )
      message.success('登录成功')
      navigate(redirect)
    } catch {
      await captchaRef.current?.refresh()
    } finally {
      setLoading(false)
    }
  }

  const activeField = activeType.toLowerCase() as 'account' | 'email' | 'phone'

  return (
    <AuthSplit
      title="登录"
      headerExtra={
        <>
          没有账号？<Link to="/auth/register">点击注册</Link>
        </>
      }
    >
      <ConfigProvider componentSize="large">
        <Form
          form={form}
          layout="vertical"
          requiredMark={false}
          initialValues={{ remember: true, captcha_id: '', captcha_value: '' }}
          onFinish={onFinish}
        >
          <Tabs
            activeKey={activeType}
            items={tabItems.map((item) => ({ key: item.key, label: item.label }))}
            onChange={(key) => setActiveType(key as LoginType)}
          />

          <Form.Item
            name={activeField}
            rules={[{ required: true, message: '请填写登录身份' }]}
          >
            <Input
              placeholder={tabItems.find((t) => t.key === activeType)?.placeholder}
              allowClear
            />
          </Form.Item>

          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          <Form.Item name="captcha_id" hidden>
            <Input />
          </Form.Item>

          <Form.Item name="captcha_value" rules={[{ required: true, message: '请输入验证码' }]}>
            <CaptchaInput
              ref={captchaRef}
              size="large"
              captchaId={captchaId}
              captchaValue={captchaValue}
              onCaptchaIdChange={(v) => form.setFieldValue('captcha_id', v)}
              onCaptchaValueChange={(v) => form.setFieldValue('captcha_value', v)}
            />
          </Form.Item>

          <Form.Item>
            <div className="flex items-center justify-between">
              <Form.Item name="remember" valuePropName="checked" noStyle>
                <Checkbox>记住我</Checkbox>
              </Form.Item>
              <Link to="/auth/forgot-password">已有账号，忘记密码？</Link>
            </div>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              登录
            </Button>
          </Form.Item>
        </Form>
      </ConfigProvider>
    </AuthSplit>
  )
}
