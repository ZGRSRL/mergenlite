import { useEffect, useState } from 'react'
import {
  Download,
  PictureAsPdf,
  Code,
  ExpandMore,
  ExpandLess,
  OpenInNew,
  Timeline as TimelineIcon,
  ErrorOutline,
  WarningAmber,
  InfoOutlined,
  AutoAwesome,
} from '@mui/icons-material'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Stack,
  Divider,
  Grid,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  listGeneratedFiles,
  getArtifactUrl,
  listAllAnalysisResults,
  AnalysisResult,
  getAnalysisLogs,
  AnalysisLog,
  getAgentOutputs,
  AgentOutput,
} from '../api/pipeline'
import { getOpportunity, Opportunity } from '../api/opportunities'

interface GeneratedFile {
  filename: string
  path: string
  size: number
  modified: number
  notice_id?: string
}

export function Results() {
  const [files, setFiles] = useState<GeneratedFile[]>([])
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([])
  const [opportunities, setOpportunities] = useState<Map<number, Opportunity>>(new Map())
  const [loading, setLoading] = useState(true)
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set())
  const [logsByResult, setLogsByResult] = useState<Record<number, AnalysisLog[]>>({})
  const [agentOutputsByResult, setAgentOutputsByResult] = useState<Record<number, AgentOutput[]>>({})
  const [detailLoading, setDetailLoading] = useState<Record<number, boolean>>({})
  const [detailErrors, setDetailErrors] = useState<Record<number, string | null>>({})

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const [fileData, resultsData] = await Promise.all([
          listGeneratedFiles(),
          listAllAnalysisResults(100),
        ])
        setFiles(fileData)
        setAnalysisResults(resultsData)
        
        // Fetch opportunity details for each analysis
        const oppIds = new Set(resultsData.map(r => r.opportunity_id))
        const oppMap = new Map<number, Opportunity>()
        
        await Promise.all(
          Array.from(oppIds).map(async (oppId) => {
            try {
              const opp = await getOpportunity(oppId)
              oppMap.set(oppId, opp)
            } catch (error) {
              console.error(`Error fetching opportunity ${oppId}:`, error)
            }
          })
        )
        
        setOpportunities(oppMap)
      } catch (error) {
        console.error('Error fetching results:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const loadResultDetails = async (analysisId: number) => {
    if (detailLoading[analysisId]) {
      return
    }

    setDetailErrors((prev) => ({ ...prev, [analysisId]: null }))
    setDetailLoading((prev) => ({ ...prev, [analysisId]: true }))
    try {
      const logs = await getAnalysisLogs(analysisId, 200)
      setLogsByResult((prev) => ({ ...prev, [analysisId]: logs }))

      try {
        const outputs = await getAgentOutputs(analysisId)
        setAgentOutputsByResult((prev) => ({ ...prev, [analysisId]: outputs }))
      } catch (agentErr) {
        console.warn('Agent outputs not available:', agentErr)
        setAgentOutputsByResult((prev) => ({ ...prev, [analysisId]: [] }))
      }
    } catch (error: any) {
      console.error(`Error loading analysis details for ${analysisId}:`, error)
      const errorMsg = error?.response?.data?.detail || error?.message || 'Detaylar yüklenemedi'
      setDetailErrors((prev) => ({ ...prev, [analysisId]: errorMsg }))
    } finally {
      setDetailLoading((prev) => ({ ...prev, [analysisId]: false }))
    }
  }

  const getDownloadUrl = (resultId: number, type: 'pdf' | 'json') => {
    return `/api/pipeline/results/${resultId}/download-${type}`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'running':
        return 'info'
      case 'failed':
        return 'error'
      default:
        return 'default'
    }
  }

  const getAnalysisTypeLabel = (type: string) => {
    switch (type) {
      case 'sow_draft':
        return 'SOW Analizi'
      case 'hotel_match':
        return 'Otel Eşleştirme'
      default:
        return type
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString('tr-TR')
  }

  const toggleExpanded = (id: number) => {
    const newExpanded = new Set(expandedResults)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
      if (!logsByResult[id]) {
        loadResultDetails(id)
      }
    }
    setExpandedResults(newExpanded)
  }

  const getSamGovUrl = (noticeId?: string) => {
    if (!noticeId) return null
    return `https://sam.gov/opp/${noticeId}/view`
  }

  const getLogMeta = (level: string) => {
    const normalized = (level || '').toUpperCase()
    switch (normalized) {
      case 'ERROR':
        return { color: '#ef4444', icon: <ErrorOutline fontSize="small" /> }
      case 'WARNING':
        return { color: '#f59e0b', icon: <WarningAmber fontSize="small" /> }
      case 'INFO':
        return { color: '#3b82f6', icon: <InfoOutlined fontSize="small" /> }
      default:
        return { color: '#10b981', icon: <TimelineIcon fontSize="small" /> }
    }
  }

  const formatDuration = (start?: string, end?: string) => {
    if (!start || !end) return null
    const startDate = new Date(start)
    const endDate = new Date(end)
    const diffSec = Math.max(0, (endDate.getTime() - startDate.getTime()) / 1000)
    if (diffSec < 60) return `${diffSec.toFixed(0)} sn`
    if (diffSec < 3600) return `${(diffSec / 60).toFixed(1)} dk`
    return `${(diffSec / 3600).toFixed(1)} saat`
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Typography variant="h5" sx={{ color: '#1e293b', fontWeight: 600 }}>
        Analiz Sonuçları ve Çıktılar
      </Typography>

      {/* Analysis Results Summary Section */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Tüm Analiz Kayıtları ({analysisResults.length})
          </Typography>
          {loading ? (
            <Typography variant="body2" color="text.secondary">
              Yükleniyor...
            </Typography>
          ) : analysisResults.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              Henüz analiz sonucu bulunamadı. Yeni bir pipeline başlattıktan sonra burada listelenecek.
            </Typography>
          ) : (
            <Stack spacing={2}>
              {analysisResults.map((result) => {
                const isExpanded = expandedResults.has(result.id)
                const hasPdf = !!result.pdf_path
                const opportunity = opportunities.get(result.opportunity_id)
                const resultJson = result.result_json as any
                const documentAnalysis = resultJson?.document_analysis
                const sowAnalysis = resultJson?.sow_analysis
                
                // Get SAM.gov URL
                const samUrl = opportunity?.samGovLink || getSamGovUrl(opportunity?.noticeId || resultJson?.opportunity?.notice_id)

                return (
                  <Card key={result.id} variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ flex: 1 }}>
                          <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap', gap: 1 }}>
                            <Chip
                              label={getAnalysisTypeLabel(result.analysis_type)}
                              size="small"
                              color="primary"
                            />
                            <Chip
                              label={result.status}
                              size="small"
                              color={getStatusColor(result.status) as any}
                            />
                            {result.pipeline_version && (
                              <Chip label={`v${result.pipeline_version}`} size="small" variant="outlined" />
                            )}
                          </Stack>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>
                            Analiz #{result.id}
                          </Typography>
                          
                          {/* Fırsat Başlığı ve SAM Linki */}
                          {opportunity && (
                            <Box sx={{ mb: 1 }}>
                              <Typography variant="body1" sx={{ fontWeight: 500, mb: 0.5 }}>
                                {opportunity.title || 'Başlık Yok'}
                              </Typography>
                              {samUrl && (
                                <Button
                                  size="small"
                                  variant="outlined"
                                  href={samUrl}
                                  target="_blank"
                                  startIcon={<OpenInNew />}
                                  sx={{ textTransform: 'none', mt: 0.5 }}
                                >
                                  SAM.gov'da Aç
                                </Button>
                              )}
                              {opportunity.noticeId && (
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                                  Notice ID: {opportunity.noticeId}
                                </Typography>
                              )}
                            </Box>
                          )}
                          
                          {/* Analiz Özeti */}
                          <Box sx={{ mb: 1 }}>
                            {documentAnalysis && (documentAnalysis.documents_analyzed > 0 || documentAnalysis.total_word_count > 0) && (
                              <Typography variant="body2" color="text.secondary">
                                {documentAnalysis.documents_analyzed || 0} döküman analiz edildi · {documentAnalysis.total_word_count || 0} kelime çıkarıldı
                                {sowAnalysis && ' · AutoGen SOW analizi tamamlandı'}
                              </Typography>
                            )}
                            {(!documentAnalysis || (documentAnalysis.documents_analyzed === 0 && documentAnalysis.total_word_count === 0)) && (
                              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                Döküman analizi yapılmadı
                              </Typography>
                            )}
                          </Box>
                          
                          <Typography variant="caption" color="text.secondary">
                            Oluşturulma: {formatDate(result.created_at)} ·{' '}
                            {result.completed_at ? `Tamamlanma: ${formatDate(result.completed_at)}` : 'Devam ediyor...'}
                          </Typography>
                        </Box>
                        <Stack direction="row" spacing={1}>
                          {hasPdf && (
                            <Button
                              variant="contained"
                              startIcon={<PictureAsPdf />}
                              href={getDownloadUrl(result.id, 'pdf')}
                              target="_blank"
                              size="small"
                              color="error"
                            >
                              PDF
                            </Button>
                          )}
                          <Button
                            variant="outlined"
                            startIcon={<Code />}
                            href={getDownloadUrl(result.id, 'json')}
                            target="_blank"
                            size="small"
                          >
                            JSON
                          </Button>
                          <Button
                            variant="outlined"
                            startIcon={isExpanded ? <ExpandLess /> : <ExpandMore />}
                            onClick={() => toggleExpanded(result.id)}
                            size="small"
                          >
                            {isExpanded ? 'Gizle' : 'Detay'}
                          </Button>
                        </Stack>
                      </Box>

                      {isExpanded && (() => {
                        const isDetailLoading = detailLoading[result.id] || false
                        const detailError = detailErrors[result.id]
                        const logs = logsByResult[result.id] || []
                        const agentOutputs = agentOutputsByResult[result.id] || []
                        
                        // Load details if not already loaded
                        if (!isDetailLoading && logs.length === 0 && !detailError) {
                          loadResultDetails(result.id)
                        }
                        
                        return (
                        <Box sx={{ mt: 2 }}>
                          <Divider sx={{ mb: 2 }} />
                          <Stack spacing={3}>
                            <Grid container spacing={2}>
                              <Grid item xs={12} md={4}>
                                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                  Analiz Detaylari
                                </Typography>
                                <Stack spacing={0.5}>
                                  <Typography variant="body2">
                                    <strong>Firsat ID:</strong> {result.opportunity_id}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Agent:</strong> {result.agent_name || 'N/A'}
                                  </Typography>
                                  {result.confidence && (
                                    <Typography variant="body2">
                                      <strong>Guven:</strong> {(result.confidence * 100).toFixed(1)}%
                                    </Typography>
                                  )}
                                  {result.pipeline_version && (
                                    <Typography variant="body2">
                                      <strong>Pipeline:</strong> v{result.pipeline_version}
                                    </Typography>
                                  )}
                                  <Typography variant="body2">
                                    <strong>Olusturulma:</strong> {formatDate(result.created_at)}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Tamamlanma:</strong> {result.completed_at ? formatDate(result.completed_at) : 'Devam ediyor'}
                                  </Typography>
                                </Stack>
                              </Grid>
                              <Grid item xs={12} md={4}>
                                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                  Ciktilar
                                </Typography>
                                <Stack spacing={1}>
                                  <Stack direction="row" spacing={1} flexWrap="wrap">
                                    {result.pdf_path ? (
                                      <Button
                                        variant="contained"
                                        startIcon={<PictureAsPdf />}
                                        href={getDownloadUrl(result.id, 'pdf')}
                                        target="_blank"
                                        size="small"
                                        color="error"
                                      >
                                        PDF Indir
                                      </Button>
                                    ) : (
                                      <Button
                                        variant="contained"
                                        startIcon={<PictureAsPdf />}
                                        size="small"
                                        color="error"
                                        disabled
                                      >
                                        PDF Indir
                                      </Button>
                                    )}
                                    <Button
                                      variant="outlined"
                                      startIcon={<Code />}
                                      href={getDownloadUrl(result.id, 'json')}
                                      target="_blank"
                                      size="small"
                                    >
                                      JSON Indir
                                    </Button>
                                  </Stack>
                                  {!result.pdf_path && (
                                    <Alert severity="warning" variant="outlined">
                                      PDF henuz olusturulmadi. Pipeline tamamlandiginda otomatik kaydedilir.
                                    </Alert>
                                  )}
                                  {result.pdf_path && (
                                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                                      <strong>PDF:</strong> {result.pdf_path}
                                    </Typography>
                                  )}
                                  {result.json_path && (
                                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                                      <strong>JSON:</strong> {result.json_path}
                                    </Typography>
                                  )}
                                </Stack>
                              </Grid>
                              <Grid item xs={12} md={4}>
                                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                  Oz Summary
                                </Typography>
                                <Stack spacing={0.5}>
                                  <Typography variant="body2">
                                    <strong>Dokuman sayisi:</strong> {documentAnalysis?.documents_analyzed ?? 0}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Kelime sayisi:</strong> {documentAnalysis?.total_word_count ?? 0}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Toplam ek:</strong> {resultJson?.attachment_count ?? '-'}
                                  </Typography>
                                  {sowAnalysis && (
                                    <Typography variant="body2">
                                      <strong>SOW segmenti:</strong> {Object.keys(sowAnalysis).length} alan
                                    </Typography>
                                  )}
                                </Stack>
                              </Grid>
                            </Grid>

                            <Box>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                AutoGen Timeline
                              </Typography>
                              {isDetailLoading ? (
                                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                                  <CircularProgress size={24} />
                                </Box>
                              ) : detailError ? (
                                <Alert severity="error">{detailError}</Alert>
                              ) : logs.length === 0 ? (
                                <Alert severity="info">Henüz log kaydi bulunmuyor.</Alert>
                              ) : (
                                <Stack spacing={1.5} sx={{ borderLeft: '2px solid #e5e7eb', pl: 2 }}>
                                  {logs.map((log) => {
                                    const meta = getLogMeta(log.level)
                                    return (
                                      <Box key={log.id} sx={{ display: 'flex', gap: 1.5 }}>
                                        <Box sx={{ color: meta.color, mt: 0.3 }}>{meta.icon}</Box>
                                        <Box>
                                          <Typography variant="caption" color="text.secondary">
                                            {log.timestamp ? new Date(log.timestamp).toLocaleString('tr-TR') : '—'}
                                            {log.step && ` · ${log.step}`}
                                          </Typography>
                                          <Typography variant="body2">{log.message}</Typography>
                                        </Box>
                                      </Box>
                                    )
                                  })}
                                </Stack>
                              )}
                            </Box>

                            <Box>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                AutoGen Eylemleri
                              </Typography>
                              {isDetailLoading ? (
                                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                                  <CircularProgress size={24} />
                                </Box>
                              ) : agentOutputs.length === 0 ? (
                                <Alert severity="info">Bu analiz icin ajan akisi kaydi bulunamadi.</Alert>
                              ) : (
                                <Stack spacing={2}>
                                  {agentOutputs.map((output) => {
                                    const run = output.agent_run
                                    const duration = formatDuration(run.started_at, run.finished_at)
                                    return (
                                      <Card key={run.id} variant="outlined">
                                        <CardContent>
                                          <Stack
                                            direction={{ xs: 'column', sm: 'row' }}
                                            spacing={1}
                                            justifyContent="space-between"
                                            alignItems={{ xs: 'flex-start', sm: 'center' }}
                                          >
                                            <Stack direction="row" spacing={1} flexWrap="wrap">
                                              <Chip
                                                icon={<AutoAwesome fontSize="small" />}
                                                label={run.run_type}
                                                size="small"
                                                color="secondary"
                                              />
                                              <Chip
                                                label={run.status}
                                                size="small"
                                                color={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'warning'}
                                                variant="outlined"
                                              />
                                              {duration && <Chip label={duration} size="small" />}
                                            </Stack>
                                            {run.started_at && (
                                              <Typography variant="caption" color="text.secondary">
                                                {new Date(run.started_at).toLocaleString('tr-TR')}
                                                {run.finished_at ? ` → ${new Date(run.finished_at).toLocaleString('tr-TR')}` : ''}
                                              </Typography>
                                            )}
                                          </Stack>
                                          {run.error_message && (
                                            <Alert severity="error" sx={{ mt: 1 }}>
                                              {run.error_message}
                                            </Alert>
                                          )}
                                          <Divider sx={{ my: 1.5 }} />
                                          <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                            Mesajlar
                                          </Typography>
                                          {output.messages.length === 0 ? (
                                            <Typography variant="body2" color="text.secondary">
                                              Mesaj kaydi bulunamadi.
                                            </Typography>
                                          ) : (
                                            <Stack spacing={1}>
                                              {output.messages.slice(0, 4).map((message) => (
                                                <Box key={message.id} sx={{ p: 1.5, bgcolor: '#f9fafb', borderRadius: 1 }}>
                                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                                    {(message.agent_name || message.role || 'Ajan')}{' '}
                                                    {message.created_at ? `· ${new Date(message.created_at).toLocaleString('tr-TR')}` : ''}
                                                  </Typography>
                                                  <Typography variant="body2">
                                                    {message.content || 'Mesaj içeriği bulunamadı.'}
                                                  </Typography>
                                                </Box>
                                              ))}
                                              {output.messages.length > 4 && (
                                                <Typography variant="caption" color="text.secondary">
                                                  +{output.messages.length - 4} mesaj daha...
                                                </Typography>
                                              )}
                                            </Stack>
                                          )}
                                          {output.llm_calls.length > 0 && (
                                            <>
                                              <Divider sx={{ my: 1.5 }} />
                                              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                                LLM Cagrilari
                                              </Typography>
                                              <Stack spacing={1}>
                                                {output.llm_calls.slice(0, 3).map((call) => (
                                                  <Box key={call.id}>
                                                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                                      {call.model || call.provider || 'LLM'} · {call.agent_name || 'Ajan'}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                                      {call.created_at ? new Date(call.created_at).toLocaleString('tr-TR') : ''}
                                                      {typeof call.total_tokens === 'number' && ` · ${call.total_tokens} token`}
                                                      {typeof call.latency_ms === 'number' && ` · ${(call.latency_ms / 1000).toFixed(1)} sn`}
                                                    </Typography>
                                                    {call.response && (
                                                      <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                                                        {call.response.length > 300 ? `${call.response.slice(0, 300)}...` : call.response}
                                                      </Typography>
                                                    )}
                                                  </Box>
                                                ))}
                                                {output.llm_calls.length > 3 && (
                                                  <Typography variant="caption" color="text.secondary">
                                                    +{output.llm_calls.length - 3} çağrı daha...
                                                  </Typography>
                                                )}
                                              </Stack>
                                            </>
                                          )}
                                        </CardContent>
                                      </Card>
                                    )
                                  })}
                                </Stack>
                              )}
                            </Box>

                            {result.result_json && (
                              <Box>
                                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                  Analiz Ozeti (JSON onizleme)
                                </Typography>
                                <Box
                                  sx={{
                                    p: 2,
                                    bgcolor: '#f5f5f5',
                                    borderRadius: 1,
                                    maxHeight: 300,
                                    overflow: 'auto',
                                  }}
                                >
                                  <Typography
                                    variant="body2"
                                    component="pre"
                                    sx={{
                                      fontFamily: 'monospace',
                                      fontSize: '0.75rem',
                                      whiteSpace: 'pre-wrap',
                                      wordBreak: 'break-word',
                                    }}
                                  >
                                    {JSON.stringify(result.result_json, null, 2).substring(0, 2000)}
                                    {JSON.stringify(result.result_json, null, 2).length > 2000 && '...'}
                                  </Typography>
                                </Box>
                              </Box>
                            )}
                          </Stack>
                        </Box>
                        )
                      })()}
                    </CardContent>
                  </Card>
                )
              })}
            </Stack>
          )}
        </CardContent>
      </Card>

      {/* Generated Files Section */}
      {files.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Üretilmiş Dosyalar ({files.length})
            </Typography>
            <Stack spacing={2}>
              {files.map((file) => {
                const match = file.filename.match(/analysis_(\d+)\.(pdf|json)/)
                const analysisId = match ? parseInt(match[1]) : null
                const fileType = match ? match[2] : 'unknown'

                return (
                  <Card key={file.path} variant="outlined">
                    <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap', gap: 1 }}>
                          <Chip
                            label={fileType.toUpperCase()}
                            size="small"
                            color={fileType === 'pdf' ? 'error' : 'default'}
                          />
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {file.filename}
                          </Typography>
                        </Stack>
                        <Typography variant="body2" color="text.secondary">
                          Notice: {file.notice_id || 'N/A'} · {(file.size / 1024).toFixed(1)} KB ·{' '}
                          {new Date(file.modified * 1000).toLocaleString('tr-TR')}
                        </Typography>
                      </Box>
                      <Stack direction="row" spacing={1}>
                        {fileType === 'pdf' && analysisId && (
                          <Button
                            variant="contained"
                            startIcon={<PictureAsPdf />}
                            href={getDownloadUrl(analysisId, 'pdf')}
                            target="_blank"
                            size="small"
                            color="error"
                          >
                            PDF İndir
                          </Button>
                        )}
                        {analysisId && (
                          <Button
                            variant="outlined"
                            startIcon={<Code />}
                            href={getDownloadUrl(analysisId, 'json')}
                            target="_blank"
                            size="small"
                          >
                            JSON İndir
                          </Button>
                        )}
                        <Button
                          variant="outlined"
                          startIcon={<Download />}
                          href={getArtifactUrl(file.path)}
                          target="_blank"
                          size="small"
                        >
                          Dosya İndir
                        </Button>
                      </Stack>
                    </CardContent>
                  </Card>
                )
              })}
            </Stack>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}
