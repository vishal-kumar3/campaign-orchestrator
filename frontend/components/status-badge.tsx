import type {
  CampaignStatus,
  ContentPlatform,
  ContentStatus,
  DocumentStatus,
  KnowledgeScope,
} from '@/lib/types'
import { Badge } from '@/components/ui/badge'

const campaignStatusVariant: Record<
  CampaignStatus,
  'secondary' | 'warning' | 'success' | 'destructive' | 'outline'
> = {
  draft: 'secondary',
  researching: 'warning',
  generating: 'warning',
  approval_pending: 'warning',
  completed: 'success',
  failed: 'destructive',
}

const contentStatusVariant: Record<
  ContentStatus,
  'secondary' | 'success' | 'destructive' | 'warning' | 'outline'
> = {
  draft: 'secondary',
  approved: 'success',
  rejected: 'destructive',
  published: 'success',
  failed: 'destructive',
}

const documentStatusVariant: Record<
  DocumentStatus,
  'secondary' | 'warning' | 'success' | 'destructive'
> = {
  pending: 'secondary',
  processing: 'warning',
  indexed: 'success',
  failed: 'destructive',
}

function formatLabel(value: string) {
  return value.replace(/_/g, ' ')
}

export function CampaignStatusBadge({ status }: { status: CampaignStatus }) {
  return (
    <Badge variant={campaignStatusVariant[status]} className="capitalize">
      {formatLabel(status)}
    </Badge>
  )
}

export function ContentStatusBadge({ status }: { status: ContentStatus }) {
  return (
    <Badge variant={contentStatusVariant[status]} className="capitalize">
      {formatLabel(status)}
    </Badge>
  )
}

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <Badge variant={documentStatusVariant[status]} className="capitalize">
      {formatLabel(status)}
    </Badge>
  )
}

export function PlatformBadge({ platform }: { platform: ContentPlatform }) {
  return <Badge variant="outline" className="capitalize">{platform}</Badge>
}

export function ScopeBadge({ scope }: { scope: KnowledgeScope }) {
  return <Badge variant="outline" className="capitalize">{scope}</Badge>
}
