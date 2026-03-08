import type React from 'react'
import type { ProfileForm, StatusType } from '../../types'
import { ProfileLanding } from './ProfileLanding'
import { ProfilePage } from './ProfilePage'

type ProfileRouterProps = {
  path: string
  userEmail: string
  isSuperuser: boolean
  profileForm: ProfileForm
  setProfileForm: React.Dispatch<React.SetStateAction<ProfileForm>>
  isSavingProfile: boolean
  statusType: StatusType
  statusMessage: string
  avatarUrl: string | null
  onAvatarUpload: (file: File) => Promise<void>
  onAvatarDownload: () => Promise<void>
  onSave: (event: React.FormEvent<HTMLFormElement>) => Promise<void>
  onLogout: () => void
  onGoProfile: () => void
  onOpenAdmin: () => void
}

export function ProfileRouter({
  path,
  userEmail,
  isSuperuser,
  profileForm,
  setProfileForm,
  isSavingProfile,
  statusType,
  statusMessage,
  avatarUrl,
  onAvatarUpload,
  onAvatarDownload,
  onSave,
  onLogout,
  onGoProfile,
  onOpenAdmin,
}: ProfileRouterProps) {
  if (path !== '/profile') {
    return <ProfileLanding userEmail={userEmail} onGoToProfile={onGoProfile} />
  }

  return (
    <ProfilePage
      userEmail={userEmail}
      isSuperuser={isSuperuser}
      profileForm={profileForm}
      setProfileForm={setProfileForm}
      isSavingProfile={isSavingProfile}
      statusType={statusType}
      statusMessage={statusMessage}
      avatarUrl={avatarUrl}
      onAvatarUpload={onAvatarUpload}
      onAvatarDownload={onAvatarDownload}
      onSave={onSave}
      onLogout={onLogout}
      onOpenAdmin={onOpenAdmin}
    />
  )
}
