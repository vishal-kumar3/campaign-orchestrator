import { auth, currentUser } from "@clerk/nextjs/server"

import { api } from "@/lib/api"

const DashboardPage = async () => {
  await auth.protect()

  const user = await currentUser()
  const health = await api.get<{ message: string }>("/health/")

  return (
    <div>
      User: {user?.fullName}
      <p>API: {health.message}</p>
    </div>
  )
}

export default DashboardPage
