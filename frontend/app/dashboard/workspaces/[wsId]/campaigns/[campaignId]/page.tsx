import { CampaignDetailPage } from '@/components/campaign-detail-page'

export default async function CampaignPage({
  params,
}: {
  params: Promise<{ wsId: string; campaignId: string }>
}) {
  const { wsId, campaignId } = await params
  return <CampaignDetailPage workspaceId={wsId} campaignId={campaignId} />
}
