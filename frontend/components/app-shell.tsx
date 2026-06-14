'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FolderKanban, LayoutDashboard, Library } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Separator } from '@/components/ui/separator'

const navItems = [
  { href: '/dashboard', label: 'Workspaces', icon: LayoutDashboard, exact: true },
]

export function AppShell({
  children,
  workspaceId,
  workspaceName,
}: {
  children: React.ReactNode
  workspaceId?: string
  workspaceName?: string
}) {
  const pathname = usePathname()

  const workspaceNav = workspaceId
    ? [
        {
          href: `/dashboard/workspaces/${workspaceId}`,
          label: workspaceName ?? 'Workspace',
          icon: FolderKanban,
          exact: true,
        },
        {
          href: `/dashboard/workspaces/${workspaceId}?tab=campaigns`,
          label: 'Campaigns',
          icon: FolderKanban,
        },
        {
          href: `/dashboard/workspaces/${workspaceId}?tab=knowledge`,
          label: 'Knowledge',
          icon: Library,
        },
      ]
    : []

  return (
    <div className="min-h-[calc(100vh-4rem)]">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 lg:flex-row lg:px-6">
        <aside className="w-full shrink-0 lg:w-56">
          <nav className="space-y-1 rounded-lg border p-2">
            {navItems.map((item) => {
              const active = item.exact ? pathname === item.href : pathname.startsWith(item.href)
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                    active ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
                  )}
                >
                  <Icon className="size-4 shrink-0" />
                  {item.label}
                </Link>
              )
            })}
            {workspaceNav.length > 0 && (
              <>
                <Separator className="my-2" />
                {workspaceNav.map((item) => {
                  const active = item.exact
                    ? pathname === item.href.split('?')[0]
                    : pathname.startsWith(item.href.split('?')[0])
                  const Icon = item.icon
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                        active ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
                      )}
                    >
                      <Icon className="size-4 shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  )
                })}
              </>
            )}
          </nav>
        </aside>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  )
}
