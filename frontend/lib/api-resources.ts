import type {
  AgentLog,
  AgentRun,
  ApproveCampaignRequest,
  ApproveCampaignResponse,
  Campaign,
  CampaignContent,
  Document,
  DocumentProcessResponse,
  DocumentUploadResponse,
  ExecuteCampaignResponse,
  KnowledgeBase,
  PaginatedResponse,
  ResearchSnapshot,
  RetrieveResponse,
  Workspace,
} from '@/lib/types'
import type { ApiClient } from '@/lib/api-client'

export const queryKeys = {
  workspaces: ['workspaces'] as const,
  workspace: (id: string) => ['workspaces', id] as const,
  campaigns: (wsId: string) => ['workspaces', wsId, 'campaigns'] as const,
  campaign: (wsId: string, id: string) => ['workspaces', wsId, 'campaigns', id] as const,
  knowledgeBases: (wsId: string) => ['workspaces', wsId, 'knowledge-bases'] as const,
  knowledgeBase: (wsId: string, id: string) =>
    ['workspaces', wsId, 'knowledge-bases', id] as const,
  documents: (wsId: string, kbId: string) =>
    ['workspaces', wsId, 'knowledge-bases', kbId, 'documents'] as const,
  document: (wsId: string, kbId: string, id: string) =>
    ['workspaces', wsId, 'knowledge-bases', kbId, 'documents', id] as const,
  contents: (wsId: string, campId: string) =>
    ['workspaces', wsId, 'campaigns', campId, 'contents'] as const,
  researchSnapshots: (wsId: string, campId: string) =>
    ['workspaces', wsId, 'campaigns', campId, 'research-snapshots'] as const,
  agentRuns: (wsId: string, campId: string) =>
    ['workspaces', wsId, 'campaigns', campId, 'agent-runs'] as const,
  agentLogs: (wsId: string, campId: string, runId: string) =>
    ['workspaces', wsId, 'campaigns', campId, 'agent-runs', runId, 'logs'] as const,
}

export const apiPaths = {
  workspaces: '/workspaces/',
  workspace: (id: string) => `/workspaces/${id}`,
  campaigns: (wsId: string) => `/workspaces/${wsId}/campaigns/`,
  campaign: (wsId: string, id: string) => `/workspaces/${wsId}/campaigns/${id}`,
  campaignExecute: (wsId: string, id: string) => `/workspaces/${wsId}/campaigns/${id}/execute`,
  campaignStream: (wsId: string, id: string) => `/workspaces/${wsId}/campaigns/${id}/stream`,
  campaignApprove: (wsId: string, id: string) => `/workspaces/${wsId}/campaigns/${id}/approve`,
  researchSnapshots: (wsId: string, campId: string) =>
    `/workspaces/${wsId}/campaigns/${campId}/research-snapshots`,
  agentRuns: (wsId: string, campId: string) =>
    `/workspaces/${wsId}/campaigns/${campId}/agent-runs`,
  agentLogs: (wsId: string, campId: string, runId: string) =>
    `/workspaces/${wsId}/campaigns/${campId}/agent-runs/${runId}/logs`,
  knowledgeBases: (wsId: string) => `/workspaces/${wsId}/knowledge-bases/`,
  knowledgeBase: (wsId: string, id: string) => `/workspaces/${wsId}/knowledge-bases/${id}`,
  documents: (wsId: string, kbId: string) =>
    `/workspaces/${wsId}/knowledge-bases/${kbId}/documents/`,
  document: (wsId: string, kbId: string, id: string) =>
    `/workspaces/${wsId}/knowledge-bases/${kbId}/documents/${id}`,
  documentUpload: (wsId: string, kbId: string) =>
    `/workspaces/${wsId}/knowledge-bases/${kbId}/documents/upload`,
  documentProcess: (wsId: string, kbId: string, id: string) =>
    `/workspaces/${wsId}/knowledge-bases/${kbId}/documents/${id}/process`,
  kbRetrieve: (wsId: string, kbId: string) =>
    `/workspaces/${wsId}/knowledge-bases/${kbId}/retrieve`,
  contents: (wsId: string, campId: string) =>
    `/workspaces/${wsId}/campaigns/${campId}/contents/`,
  content: (wsId: string, campId: string, id: string) =>
    `/workspaces/${wsId}/campaigns/${campId}/contents/${id}`,
}

export function createResourceApi(client: ApiClient) {
  return {
    listWorkspaces: () => client.get<PaginatedResponse<Workspace>>(apiPaths.workspaces),
    getWorkspace: (id: string) => client.get<Workspace>(apiPaths.workspace(id)),
    createWorkspace: (body: { name: string; description?: string | null }) =>
      client.post<Workspace>(apiPaths.workspaces, body),
    updateWorkspace: (id: string, body: { name?: string; description?: string | null }) =>
      client.patch<Workspace>(apiPaths.workspace(id), body),
    deleteWorkspace: (id: string) => client.delete<void>(apiPaths.workspace(id)),

    listCampaigns: (wsId: string) =>
      client.get<PaginatedResponse<Campaign>>(apiPaths.campaigns(wsId)),
    getCampaign: (wsId: string, id: string) =>
      client.get<Campaign>(apiPaths.campaign(wsId, id)),
    createCampaign: (wsId: string, body: Record<string, unknown>) =>
      client.post<Campaign>(apiPaths.campaigns(wsId), body),
    updateCampaign: (wsId: string, id: string, body: Record<string, unknown>) =>
      client.patch<Campaign>(apiPaths.campaign(wsId, id), body),
    deleteCampaign: (wsId: string, id: string) =>
      client.delete<void>(apiPaths.campaign(wsId, id)),
    executeCampaign: (wsId: string, id: string) =>
      client.post<ExecuteCampaignResponse>(apiPaths.campaignExecute(wsId, id)),
    approveCampaign: (wsId: string, id: string, body: ApproveCampaignRequest) =>
      client.post<ApproveCampaignResponse>(apiPaths.campaignApprove(wsId, id), body),
    listResearchSnapshots: (wsId: string, campId: string) =>
      client.get<PaginatedResponse<ResearchSnapshot>>(apiPaths.researchSnapshots(wsId, campId)),
    listAgentRuns: (wsId: string, campId: string) =>
      client.get<PaginatedResponse<AgentRun>>(apiPaths.agentRuns(wsId, campId)),
    listAgentLogs: (wsId: string, campId: string, runId: string) =>
      client.get<PaginatedResponse<AgentLog>>(apiPaths.agentLogs(wsId, campId, runId)),

    listKnowledgeBases: (wsId: string) =>
      client.get<PaginatedResponse<KnowledgeBase>>(apiPaths.knowledgeBases(wsId)),
    getKnowledgeBase: (wsId: string, id: string) =>
      client.get<KnowledgeBase>(apiPaths.knowledgeBase(wsId, id)),
    createKnowledgeBase: (wsId: string, body: Record<string, unknown>) =>
      client.post<KnowledgeBase>(apiPaths.knowledgeBases(wsId), body),
    updateKnowledgeBase: (wsId: string, id: string, body: Record<string, unknown>) =>
      client.patch<KnowledgeBase>(apiPaths.knowledgeBase(wsId, id), body),
    deleteKnowledgeBase: (wsId: string, id: string) =>
      client.delete<void>(apiPaths.knowledgeBase(wsId, id)),

    listDocuments: (wsId: string, kbId: string) =>
      client.get<PaginatedResponse<Document>>(apiPaths.documents(wsId, kbId)),
    getDocument: (wsId: string, kbId: string, id: string) =>
      client.get<Document>(apiPaths.document(wsId, kbId, id)),
    uploadDocument: (wsId: string, kbId: string, file: File) => {
      const form = new FormData()
      form.append('file', file)
      return client.post<DocumentUploadResponse>(apiPaths.documentUpload(wsId, kbId), form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    processDocument: (wsId: string, kbId: string, id: string) =>
      client.post<DocumentProcessResponse>(apiPaths.documentProcess(wsId, kbId, id)),
    retrieveChunks: (wsId: string, kbId: string, q: string, k = 3) =>
      client.get<RetrieveResponse>(apiPaths.kbRetrieve(wsId, kbId), {
        params: { q, k },
      }),
    createDocument: (wsId: string, kbId: string, body: Record<string, unknown>) =>
      client.post<Document>(apiPaths.documents(wsId, kbId), body),
    deleteDocument: (wsId: string, kbId: string, id: string) =>
      client.delete<void>(apiPaths.document(wsId, kbId, id)),

    listContents: (wsId: string, campId: string) =>
      client.get<PaginatedResponse<CampaignContent>>(apiPaths.contents(wsId, campId)),
    createContent: (wsId: string, campId: string, body: Record<string, unknown>) =>
      client.post<CampaignContent>(apiPaths.contents(wsId, campId), body),
    updateContent: (wsId: string, campId: string, id: string, body: Record<string, unknown>) =>
      client.patch<CampaignContent>(apiPaths.content(wsId, campId, id), body),
    deleteContent: (wsId: string, campId: string, id: string) =>
      client.delete<void>(apiPaths.content(wsId, campId, id)),
  }
}
