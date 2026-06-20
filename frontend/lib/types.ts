export type CampaignStatus =
  | 'draft'
  | 'researching'
  | 'generating'
  | 'approval_pending'
  | 'completed'
  | 'failed'

export type ContentPlatform = 'twitter' | 'linkedin' | 'email' | 'blog'

export type ContentStatus = 'draft' | 'approved' | 'rejected' | 'published' | 'failed'

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
  knowledge_base_id: string | null
  competitor_urls: string[] | null
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
  processing_error?: string | null
  created_at: string
}

export interface DocumentUploadResponse {
  document_id: string
  file_name: string
  file_url: string
  mime_type: string | null
  status: DocumentStatus
}

export interface DocumentProcessResponse {
  document_id: string
  status: DocumentStatus
  message: string
}

export interface RetrievedChunk {
  chunk_id: string
  document_id: string
  chunk_index: number
  content: string
  score: number
  metadata: Record<string, unknown> | null
}

export interface RetrieveResponse {
  query: string
  knowledge_base_id: string
  chunks: RetrievedChunk[]
}

export interface CampaignContent {
  id: string
  campaign_id: string
  platform: ContentPlatform
  title: string | null
  content: string
  status: ContentStatus
  external_post_id?: string | null
  published_at?: string | null
  variant?: string
  scheduled_at?: string | null
  engagement_metrics?: Record<string, number>
  created_at: string
  updated_at: string
}

export type AgentStatus = 'running' | 'completed' | 'failed'

export interface ResearchSnapshot {
  id: string
  campaign_id: string
  summary: string | null
  raw_data: Record<string, unknown> | null
  created_at: string
}

export interface AgentRun {
  id: string
  campaign_id: string
  agent_name: string
  status: AgentStatus
  input: Record<string, unknown> | null
  output: Record<string, unknown> | null
  started_at: string
  completed_at: string | null
}

export interface AgentLog {
  id: string
  run_id: string
  node_name: string
  level: 'info' | 'warning' | 'error'
  message: string
  metadata: Record<string, unknown> | null
  created_at: string
}

export interface ExecuteCampaignResponse {
  campaign_id: string
  status: CampaignStatus
  thread_id: string
  message: string
}

export interface ContentApprovalItem {
  id: string
  content?: string | null
  status: 'approved' | 'rejected'
  scheduled_at?: string | null
}

export interface ApproveCampaignRequest {
  contents: ContentApprovalItem[]
  reject_all_to_draft?: boolean
}

export interface ApproveCampaignResponse {
  campaign_id: string
  status: CampaignStatus
  approved_count: number
  rejected_count: number
  resuming: boolean
}

export interface PlatformSummary {
  platform: ContentPlatform
  impressions: number
  engagements: number
  clicks: number
  engagement_rate: number
  ctr: number
}

export interface VariantComparison {
  platform: ContentPlatform
  variant_a_rate: number
  variant_b_rate: number
  winner: string
}

export interface ContentAnalyticsItem {
  content_id: string
  platform: ContentPlatform
  variant: string
  status: ContentStatus
  engagement_metrics: Record<string, number>
  scheduled_at?: string | null
  published_at?: string | null
  external_post_id?: string | null
}

export interface CampaignAnalyticsResponse {
  campaign_id: string
  totals: {
    impressions: number
    engagements: number
    clicks: number
    engagement_rate: number
    ctr: number
  }
  by_platform: PlatformSummary[]
  variants: VariantComparison[]
  contents: ContentAnalyticsItem[]
}
