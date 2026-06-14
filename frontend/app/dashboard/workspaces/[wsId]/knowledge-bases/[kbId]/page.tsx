import { KnowledgeBaseDetailPage } from '@/components/knowledge-base-detail-page'

export default async function KnowledgeBasePage({
  params,
}: {
  params: Promise<{ wsId: string; kbId: string }>
}) {
  const { wsId, kbId } = await params
  return <KnowledgeBaseDetailPage workspaceId={wsId} kbId={kbId} />
}
