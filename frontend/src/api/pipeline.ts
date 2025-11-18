import api from './client'

const API_BASE = '/api/pipeline'

export interface PipelineRunPayload {
  opportunityId: number
  attachmentIds?: number[]
  analysisType?: string
  pipelineVersion?: string
  agentName?: string
  options?: Record<string, unknown>
}

export interface PipelineRunResponse {
  analysis_result_id: number
  status: string
  message?: string
}

export interface AnalysisResult {
  id: number
  opportunity_id: number
  analysis_type: string
  status: string
  pipeline_version?: string
  agent_name?: string
  result_json?: Record<string, unknown>
  confidence?: number
  pdf_path?: string
  json_path?: string
  markdown_path?: string
  created_at?: string
  updated_at?: string
  completed_at?: string
}

export interface AnalysisLog {
  id: number
  analysis_result_id: number
  step?: string
  level: string
  message: string
  timestamp?: string
}

export async function runPipelineJob(payload: PipelineRunPayload): Promise<PipelineRunResponse> {
  const { data } = await api.post(`${API_BASE}/run`, {
    opportunity_id: payload.opportunityId,
    attachment_ids: payload.attachmentIds,
    analysis_type: payload.analysisType,
    pipeline_version: payload.pipelineVersion,
    agent_name: payload.agentName,
    options: payload.options,
  })
  return data
}

export async function getAnalysisResult(analysisResultId: number): Promise<AnalysisResult> {
  const { data } = await api.get(`${API_BASE}/results/${analysisResultId}`)
  return data
}

export async function getAnalysisLogs(analysisResultId: number, limit = 100): Promise<AnalysisLog[]> {
  const { data } = await api.get(`${API_BASE}/results/${analysisResultId}/logs`, {
    params: { limit },
  })
  return data || []
}

export async function listAnalysisResults(opportunityId: number, limit = 20): Promise<AnalysisResult[]> {
  const { data } = await api.get(`${API_BASE}/opportunity/${opportunityId}/results`, {
    params: { limit },
  })
  return data || []
}

export async function listGeneratedFiles() {
  const { data } = await api.get(`${API_BASE}/files/list`)
  return data.files || []
}

export async function listAllAnalysisResults(limit = 50, status?: string, analysisType?: string): Promise<AnalysisResult[]> {
  const params: Record<string, unknown> = { limit }
  if (status) params.status = status
  if (analysisType) params.analysis_type = analysisType
  const { data } = await api.get(`${API_BASE}/results`, { params })
  return data || []
}

export function getArtifactUrl(path: string) {
  return `${API_BASE}/files/sow-pdf?path=${encodeURIComponent(path)}`
}
