import api from './client'

const API_BASE = '/api/opportunities'

export type RiskLevel = 'low' | 'medium' | 'high'

export interface Opportunity {
  id: number
  noticeId: string
  title: string
  agency?: string
  postedDate?: string
  responseDeadline?: string
  naicsCode?: string
  status?: string
  daysLeft: number
  analyzed: boolean
  risk?: RiskLevel
  samGovLink?: string
  description?: string
}

export interface OpportunityFilters {
  noticeId?: string
  naicsCode?: string
  keyword?: string
  page?: number
  pageSize?: number
}

export interface SyncJobStatus {
  jobId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  countNew?: number
  countUpdated?: number
  countAttachments?: number
  totalProcessed?: number
  errorMessage?: string
}

export interface DownloadJobStatus {
  jobId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  downloaded?: number
  failed?: number
  errorMessage?: string
}

export interface Attachment {
  id: number
  opportunity_id: number
  name: string
  source_url?: string
  local_path?: string
  downloaded: boolean
  created_at?: string
}

const computeDaysLeft = (responseDeadline?: string): number => {
  if (!responseDeadline) return 0
  const deadline = new Date(responseDeadline)
  const diff = Math.ceil((deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  return diff > 0 ? diff : 0
}

const computeRisk = (daysLeft: number): RiskLevel => {
  if (daysLeft <= 5) return 'high'
  if (daysLeft <= 10) return 'medium'
  return 'low'
}

export async function loadOpportunities(filters?: OpportunityFilters): Promise<Opportunity[]> {
  const params: Record<string, any> = {
    page: filters?.page ?? 1,
    page_size: filters?.pageSize ?? 20,
  }
  if (filters?.noticeId) params.notice_id = filters.noticeId
  if (filters?.naicsCode) params.naics_code = filters.naicsCode
  if (filters?.keyword) params.keyword = filters.keyword

  const { data } = await api.get(`${API_BASE}`, { params })
  return (data || []).map((opp: any) => {
    const daysLeft = computeDaysLeft(opp.response_deadline || opp.responseDeadline)
    return {
      id: opp.id,
      noticeId: opp.notice_id || opp.noticeId || '',
      title: opp.title || 'Başlık Yok',
      agency: opp.agency,
      postedDate: opp.posted_date || opp.postedDate,
      responseDeadline: opp.response_deadline || opp.responseDeadline,
      naicsCode: opp.naics_code || opp.naicsCode,
      status: opp.status,
      daysLeft,
      analyzed: opp.analyzed || false,
      risk: computeRisk(daysLeft),
      samGovLink: opp.sam_gov_link || opp.samGovLink,
      description: opp.description || opp.raw_data?.description,
    } as Opportunity
  })
}

export async function getOpportunity(id: number): Promise<Opportunity> {
  const { data } = await api.get(`${API_BASE}/${id}`)
  const daysLeft = computeDaysLeft(data.response_deadline)
  return {
    id: data.id,
    noticeId: data.notice_id,
    title: data.title,
    agency: data.agency,
    postedDate: data.posted_date,
    responseDeadline: data.response_deadline,
    naicsCode: data.naics_code,
    status: data.status,
    daysLeft,
    analyzed: data.analyzed || false,
    risk: computeRisk(daysLeft),
    samGovLink: data.sam_gov_link,
    description: data.description || data.raw_data?.description,
  }
}

export async function getAttachments(opportunityId: number): Promise<Attachment[]> {
  const { data } = await api.get(`${API_BASE}/${opportunityId}/attachments`)
  return data || []
}

export async function startSamSync(params: {
  naics?: string
  keyword?: string
  daysBack?: number
  limit?: number
}) {
  const { data } = await api.post(`${API_BASE}/sync`, null, {
    params: {
      naics: params.naics ?? '721110',
      keyword: params.keyword,
      days_back: params.daysBack ?? 30,
      limit: params.limit ?? 1000,
    },
  })
  return data
}

export async function getSyncJob(jobId: string) {
  const { data } = await api.get(`${API_BASE}/sync/jobs/${jobId}`)
  return data
}

export async function getSyncLogs(jobId: string, limit = 100) {
  const { data } = await api.get(`${API_BASE}/sync/jobs/${jobId}/logs`, {
    params: { limit },
  })
  return data || []
}

export async function listSyncJobs(limit = 20) {
  const { data } = await api.get(`${API_BASE}/sync/jobs`, { params: { limit } })
  return data || []
}

export async function startAttachmentDownload(opportunityId: number) {
  const { data } = await api.post(`${API_BASE}/${opportunityId}/download-attachments`)
  return data
}

export async function getDownloadJob(jobId: string) {
  const { data } = await api.get(`${API_BASE}/download/jobs/${jobId}`)
  return data
}

export async function getDownloadLogs(jobId: string, limit = 100) {
  const { data } = await api.get(`${API_BASE}/download/jobs/${jobId}/logs`, {
    params: { limit },
  })
  return data || []
}

export async function listDownloadJobs(opportunityId?: number, limit = 20) {
  const params: Record<string, any> = { limit }
  if (opportunityId) params.opportunity_id = opportunityId
  const { data } = await api.get(`${API_BASE}/download/jobs`, { params })
  return data || []
}

// History / learning data

export interface OpportunityHistoryEntry {
  id: number
  old_status?: string
  new_status: string
  changed_by: string
  change_source?: string
  meta?: any
  created_at: string
}

export interface AgentRunSummary {
  id: number
  run_type: string
  status: string
  started_at?: string
  finished_at?: string
  error_message?: string
}

export interface TrainingExampleSummary {
  id: number
  example_type: string
  outcome?: string
  rating?: number
  created_at: string
}

export interface DecisionPattern {
  key_hash: string
  pattern_desc?: string
  recommended_hotels?: any
  created_at: string
  extra_metadata?: any
}

export interface DecisionCacheLookupResponse {
  key_hash: string
  signature: Record<string, string>
  matched: boolean
  pattern?: DecisionPattern
}

export interface DecisionCacheContextRequest {
  notice_id?: string
  city?: string
  state?: string
  location?: string
  participants?: number
  date_range?: string
  nights?: number
  budget_total?: number
  naics_code?: string
}

export async function getOpportunityHistory(opportunityId: number, limit = 50) {
  const { data } = await api.get(`${API_BASE}/${opportunityId}/history`, { params: { limit } })
  return data as OpportunityHistoryEntry[]
}

export async function getAgentRuns(opportunityId: number, limit = 20) {
  const { data } = await api.get(`${API_BASE}/${opportunityId}/agent-runs`, { params: { limit } })
  return data as AgentRunSummary[]
}

export async function getTrainingExamples(opportunityId: number, limit = 20) {
  const { data } = await api.get(`${API_BASE}/${opportunityId}/training-examples`, { params: { limit } })
  return data as TrainingExampleSummary[]
}

export async function lookupDecisionPattern(
  opportunityId: number,
  context?: DecisionCacheContextRequest,
): Promise<DecisionCacheLookupResponse | null> {
  try {
    const payload = context ?? {}
    const { data } = await api.post(`${API_BASE}/${opportunityId}/decision-cache/lookup`, payload)
    return data as DecisionCacheLookupResponse
  } catch (error) {
    return null
  }
}

export interface EmailLogEntry {
  id: number
  direction: string
  subject?: string
  from_address?: string
  to_address?: string
  parsed_summary?: string
  created_at: string
}

export async function getEmailLogs(opportunityId: number, limit = 50) {
  const { data } = await api.get(`${API_BASE}/${opportunityId}/emails`, { params: { limit } })
  return data as EmailLogEntry[]
}

export interface HotelMatchResult {
  id: number
  generated_at?: string
  reasoning?: string
  hotels: Array<{
    name?: string
    amadeus_hotel_id?: string
    score?: number
    currency?: string
    total_price?: number
    notes?: string
  }>
  decision_metadata?: Record<string, any>
}

export async function getHotelMatches(opportunityId: number, limit = 3) {
  const { data } = await api.get(`${API_BASE}/${opportunityId}/hotel-matches`, { params: { limit } })
  return data as HotelMatchResult[]
}
