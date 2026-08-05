import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { refreshDict, syncDictTree } from '@/utils/dict'
import { AppFooter, AppHeader, HEADER_HEIGHT } from './components'
import { Content } from './Content'

export function MainLayout() {
  const { pathname } = useLocation()
  const hideFooter = pathname === '/messages' || pathname.startsWith('/messages/')

  useEffect(() => {
    syncDictTree()
    void refreshDict()
  }, [])

  return (
    <div className="flex min-h-screen flex-col bg-[var(--ant-color-bg-layout)] text-[var(--ant-color-text)]">
      <AppHeader />
      <div className="flex flex-1 flex-col" style={{ paddingTop: HEADER_HEIGHT }}>
        <Content />
        {hideFooter ? null : <AppFooter />}
      </div>
    </div>
  )
}
