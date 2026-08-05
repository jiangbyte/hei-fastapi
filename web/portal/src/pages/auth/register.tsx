import { useRef, useState } from 'react'
import { Button, ConfigProvider, Form, Input, message } from 'antd'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '@/api'
import { CaptchaInput, type CaptchaInputHandle } from '@/components/common/CaptchaInput'
import { PasswordStrength } from '@/components/common/PasswordStrength'
import { encryptPasswords } from '@/utils/security'
import { isValidEmail } from '@/utils/validate'
import { AuthSplit } from './AuthSplit'

type FormValues = {
  account: string
  email: string
  password: string
  confirmPassword: string
  captcha_id: string
  captcha_value: string
}

export function RegisterPage() {
  const [form] = Form.useForm<FormValues>()
  const [loading, setLoading] = useState(false)
  const captchaRef = useRef<CaptchaInputHandle>(null)
  const navigate = useNavigate()
  const captchaId = Form.useWatch('captcha_id', form) || ''
  const captchaValue = Form.useWatch('captcha_value', form) || ''
  const password = Form.useWatch('password', form) || ''

  async function onFinish(values: FormValues) {
    const account = values.account.trim()
    const email = values.email.trim()

    if (account.length < 3 || account.length > 64) {
      message.warning('用户名需 3-64 个字符')
      return
    }
    if (!isValidEmail(email) || email.length > 128) {
      message.warning('邮箱格式不正确')
      return
    }

    setLoading(true)
    try {
      const encrypted = await encryptPasswords({ password: values.password })
      await authApi.register({
        account,
        email,
        password: encrypted.values.password || '',
        password_key_id: encrypted.password_key_id,
        captcha_id: values.captcha_id,
        captcha_value: values.captcha_value,
      })
      message.success('注册成功，请登录')
      navigate('/auth/login')
    } catch {
      await captchaRef.current?.refresh()
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthSplit
      title="注册"
      headerExtra={
        <>
          已有账号？<Link to="/auth/login">点此登录</Link>
        </>
      }
    >
      <ConfigProvider componentSize="large">
        <Form
          form={form}
          layout="vertical"
          requiredMark={false}
          initialValues={{ captcha_id: '', captcha_value: '' }}
          onFinish={onFinish}
        >
          <Form.Item
            name="account"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, max: 64, message: '用户名需 3-64 个字符' },
            ]}
          >
            <Input placeholder="用户名" allowClear />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
              { max: 128, message: '邮箱最多 128 个字符' },
            ]}
          >
            <Input placeholder="邮箱地址" allowClear />
          </Form.Item>

          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password placeholder="密码（至少 8 位，含大小写、数字与特殊字符）" />
          </Form.Item>
          <PasswordStrength password={password} />

          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次密码输入不一致'))
                },
              }),
            ]}
          >
            <Input.Password placeholder="确认密码" />
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

          <Form.Item name="captcha_id" hidden>
            <Input />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              立即注册
            </Button>
          </Form.Item>
        </Form>
      </ConfigProvider>
    </AuthSplit>
  )
}
