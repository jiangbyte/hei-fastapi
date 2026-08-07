/** Author: Charlie */

import { Navigate, type RouteObject } from 'react-router-dom'
import { MainLayout } from '@/layouts'
import { HomePage } from '@/pages/home'
import { LoginPage } from '@/pages/auth/login'
import { RegisterPage } from '@/pages/auth/register'
import { ForgotPasswordPage } from '@/pages/auth/forgot-password'
import { NotFoundPage } from '@/pages/error/not-found'
import { UserCenterPage } from '@/pages/usercenter'
import { ProfilePage } from '@/pages/profile'
import { MessagesPage } from '@/pages/messages'
import { AnnouncementListPage } from '@/pages/announcements'
import { AnnouncementDetailPage } from '@/pages/announcements/detail'
import { guestOnly, requireAuth } from './guard'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <HomePage /> },
      {
        path: 'messages',
        loader: requireAuth,
        element: <MessagesPage />,
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: 'usercenter',
        loader: requireAuth,
        element: <UserCenterPage />,
      },
      {
        path: 'announcements',
        element: <AnnouncementListPage />,
      },
      {
        path: 'announcements/:id',
        element: <AnnouncementDetailPage />,
      },
      {
        path: 'auth/login',
        loader: guestOnly,
        element: <LoginPage />,
      },
      {
        path: 'auth/register',
        loader: guestOnly,
        element: <RegisterPage />,
      },
      {
        path: 'auth/forgot-password',
        loader: guestOnly,
        element: <ForgotPasswordPage />,
      },
    ],
  },
  { path: '/404', element: <NotFoundPage /> },
  { path: '*', element: <Navigate to="/404" replace /> },
]
