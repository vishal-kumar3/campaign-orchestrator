import { currentUser, auth } from "@clerk/nextjs/server"
import { redirect } from "next/navigation"


const DashboardPage = async () => {
  

  const token = await auth()
  if (!token) redirect("/")

  const user = await currentUser()

  return <>
    <div>
    User: {user?.fullName}
    Token: {await token.getToken()}
    </div>
  </>
}

export default DashboardPage
