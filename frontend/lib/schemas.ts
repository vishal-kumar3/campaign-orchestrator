import { z } from 'zod'

export const contentPlatformSchema = z.enum(['twitter', 'linkedin', 'email', 'blog'])
export const campaignStatusSchema = z.enum([
  'draft',
  'researching',
  'generating',
  'approval_pending',
  'completed',
  'failed',
])
export const contentStatusSchema = z.enum([
  'draft',
  'approved',
  'rejected',
  'published',
  'failed',
])
export const knowledgeScopeSchema = z.enum(['workspace', 'campaign'])

export const workspaceCreateSchema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(255),
  description: z.string().trim().optional().or(z.literal('')),
})

export const workspaceUpdateSchema = workspaceCreateSchema.partial().refine(
  (data) => data.name !== undefined || data.description !== undefined,
  { message: 'At least one field is required' },
)

export const campaignCreateSchema = z.object({
  title: z.string().trim().min(1, 'Title is required').max(255),
  objective: z.string().trim().min(1, 'Objective is required'),
  target_audience: z.string().trim().optional().or(z.literal('')),
  region: z.string().trim().optional().or(z.literal('')),
  platforms: z.array(contentPlatformSchema).optional(),
  knowledge_base_id: z.string().uuid().optional().or(z.literal('')),
  competitor_urls: z
    .array(z.string().trim().url('Enter a valid URL'))
    .max(5, 'At most 5 competitor URLs')
    .optional(),
})

export const campaignUpdateSchema = campaignCreateSchema.partial().extend({
  status: campaignStatusSchema.optional(),
})

export const knowledgeBaseCreateSchema = z
  .object({
    name: z.string().trim().min(1, 'Name is required').max(255),
    scope: knowledgeScopeSchema,
    campaign_id: z.string().uuid().optional().or(z.literal('')),
  })
  .superRefine((data, ctx) => {
    if (data.scope === 'workspace' && data.campaign_id) {
      ctx.addIssue({
        code: 'custom',
        message: 'Campaign must be empty for workspace scope',
        path: ['campaign_id'],
      })
    }
    if (data.scope === 'campaign' && !data.campaign_id) {
      ctx.addIssue({
        code: 'custom',
        message: 'Campaign is required for campaign scope',
        path: ['campaign_id'],
      })
    }
  })

export const documentCreateSchema = z.object({
  file_name: z.string().trim().min(1, 'File name is required'),
  file_url: z.string().trim().url('Enter a valid URL'),
  mime_type: z.string().trim().optional().or(z.literal('')),
})

export const contentCreateSchema = z.object({
  platform: contentPlatformSchema,
  title: z.string().trim().optional().or(z.literal('')),
  content: z.string().trim().min(1, 'Content is required'),
  status: contentStatusSchema.optional(),
})

export const contentUpdateSchema = contentCreateSchema.partial()

export type WorkspaceCreateInput = z.infer<typeof workspaceCreateSchema>
export type WorkspaceUpdateInput = z.infer<typeof workspaceUpdateSchema>
export type CampaignCreateInput = z.infer<typeof campaignCreateSchema>
export type CampaignUpdateInput = z.infer<typeof campaignUpdateSchema>
export type KnowledgeBaseCreateInput = z.infer<typeof knowledgeBaseCreateSchema>
export type DocumentCreateInput = z.infer<typeof documentCreateSchema>
export type ContentCreateInput = z.infer<typeof contentCreateSchema>
export type ContentUpdateInput = z.infer<typeof contentUpdateSchema>
