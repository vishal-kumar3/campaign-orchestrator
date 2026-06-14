export type CampaignStatus =
  | 'draft'
  | 'researching'
  | 'generating'
  | 'approval_pending'
  | 'completed'
  | 'failed'

export type ContentPlatform = 'twitter' | 'linkedin' | 'email' | 'blog'

export type ContentStatus = 'draft' | 'approved' | 'rejected'

export type KnowledgeScope = 'workspace' | 'campaign'

export type DocumentStatus = 'pending' | 'processing' | 'indexed' | 'failed'

export interface PaginatedResponse<T> {
  items: T[]
  total: number
}

export interface Workspace {
  id: string
  owner_id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Campaign {
  id: string
  workspace_id: string
  title: string
  objective: string
  target_audience: string | null
  region: string | null
  platforms: ContentPlatform[] | null
  status: CampaignStatus
  created_at: string
  updated_at: string
}

export interface KnowledgeBase {
  id: string
  workspace_id: string
  campaign_id: string | null
  scope: KnowledgeScope
  name: string
  created_at: string
}

export interface Document {
  id: string
  knowledge_base_id: string
  file_name: string
  file_url: string
  mime_type: string | null
  status: DocumentStatus
  created_at: string
}

export interface CampaignContent {
  id: string
  campaign_id: string
  platform: ContentPlatform
  title: string | null
  content: string
  status: ContentStatus
  created_at: string
  updated_at: string
}
