import { Suspense } from 'react'

import { WorkspaceDetailPage } from '@/components/workspace-detail-page'
import { Skeleton } from '@/components/ui/skeleton'

export default async function WorkspacePage({
  params,
}: {
  params: Promise<{ wsId: string }>
}) {
  const { wsId } = await params

  return (
    <Suspense
      fallback={
        <div className="space-y-4 p-6">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-48 w-full" />
        </div>
      }
    >
      <WorkspaceDetailPage workspaceId={wsId} />
    </Suspense>
  )
}
