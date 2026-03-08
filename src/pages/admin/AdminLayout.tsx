import type { AdminUser } from '../../types'
import { LoadingScreen } from '../../components/LoadingScreen'
import { AdminAccessDenied } from './AdminAccessDenied'
import { AdminErrorState } from './AdminErrorState'
import { AdminHome } from './AdminHome'
import { AdminUserDetail } from './AdminUserDetail'
import { AdminUsersList } from './AdminUsersList'

type AdminLayoutProps = {
  path: string
  isSuperuser: boolean
  isLoading: boolean
  error: string
  users: AdminUser[]
  selectedUser: AdminUser | null
  onGoProfile: () => void
  onGoUsers: () => void
  onSelectUser: (userId: number) => void
}

export function AdminLayout({
  path,
  isSuperuser,
  isLoading,
  error,
  users,
  selectedUser,
  onGoProfile,
  onGoUsers,
  onSelectUser,
}: AdminLayoutProps) {
  if (!isSuperuser) {
    return <AdminAccessDenied onGoProfile={onGoProfile} />
  }

  if (isLoading) {
    return <LoadingScreen message="Loading admin data..." />
  }

  if (error) {
    return <AdminErrorState message={error} onBackToUsers={onGoUsers} />
  }

  if (path === '/admin') {
    return <AdminHome onOpenUsers={onGoUsers} />
  }

  if (path.startsWith('/admin/users/')) {
    return (
      <AdminUserDetail
        user={selectedUser}
        onBack={onGoUsers}
        onGoProfile={onGoProfile}
      />
    )
  }

  return (
    <AdminUsersList users={users} onSelectUser={onSelectUser} onGoProfile={onGoProfile} />
  )
}
