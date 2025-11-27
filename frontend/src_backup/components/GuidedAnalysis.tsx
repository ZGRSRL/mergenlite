import { useEffect, useMemo, useState } from 'react'
import {
  ArrowBack,
  Download,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  OpenInNew,
  PlayArrow,
  Hotel,
  Description,
  Timeline as TimelineIcon,
  ExpandMore,
  Refresh,
  FilePresent,
  AccessTime,
  Storage,
  LocationOn,
  AttachMoney,
  Star
} from '@mui/icons-material'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Tooltip,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  LinearProgress,
  TableSortLabel,
  Divider,
  IconButton,
} from '@mui/material'
import {
  Opportunity,
  getOpportunityHistory,
  getAgentRuns,
  getTrainingExamples,
  lookupDecisionPattern,
  getEmailLogs,
  getHotelMatches,
  getAttachments,
  startAttachmentDownload,
  getDownloadJob,
  OpportunityHistoryEntry,
  AgentRunSummary,
  TrainingExampleSummary,
  DecisionCacheLookupResponse,
  EmailLogEntry,
  HotelMatchResult,
  getDownloadLogs
} from '../api/opportunities'
import {
  runPipelineJob,
  listAnalysisResults,
  getAnalysisResult,
  getAnalysisLogs,
  AnalysisResult,
  AnalysisLog,
} from '../api/pipeline'
import { EmailHistory } from './EmailHistory'


interface GuidedAnalysisProps {
  opportunity: Opportunity | null
  onBack: () => void
}

type TimelineEventType = 'history'

interface TimelineEvent {
  id: string
  type: TimelineEventType
  timestamp: string
  title: string
  description?: string
  context?: string
}

export function GuidedAnalysis({ opportunity, onBack }: GuidedAnalysisProps) {
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([])
  const [selectedResult, setSelectedResult] = useState<AnalysisResult | null>(null)
  const [logs, setLogs] = useState<AnalysisLog[]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<OpportunityHistoryEntry[]>([])
  const [agentRuns, setAgentRuns] = useState<AgentRunSummary[]>([])
  const [trainingExamples, setTrainingExamples] = useState<TrainingExampleSummary[]>([])
  const [decisionLookup, setDecisionLookup] = useState<DecisionCacheLookupResponse | null>(null)
  const [emailLogs, setEmailLogs] = useState<EmailLogEntry[]>([])
  const [hotelMatches, setHotelMatches] = useState<HotelMatchResult[]>([])
  const [hotelLoading, setHotelLoading] = useState(false)
  const [attachments, setAttachments] = useState<import('../api/opportunities').Attachment[]>([])
  const [downloadLoading, setDownloadLoading] = useState(false)
  const [downloadJobId, setDownloadJobId] = useState<string | null>(null)
  const [sortField, setSortField] = useState<'name' | 'status' | 'size' | 'date'>('name')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const latestHotelMatch = hotelMatches[0] ?? null

  // Sort attachments
  const sortedAttachments = useMemo(() => {
    const sorted = [...attachments]
    sorted.sort((a, b) => {
      let aVal: any, bVal: any
      switch (sortField) {
        case 'name':
          aVal = a.name || ''
          bVal = b.name || ''
          break
        case 'status':
          aVal = a.downloaded && a.local_path ? 1 : 0
          bVal = b.downloaded && b.local_path ? 1 : 0
          break
        case 'size':
          aVal = (a as any).size_bytes || 0
          bVal = (b as any).size_bytes || 0
          break
        case 'date':
          aVal = a.created_at ? new Date(a.created_at).getTime() : 0
          bVal = b.created_at ? new Date(b.created_at).getTime() : 0
          break
        default:
          return 0
      }
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
      return 0
    })
    return sorted
  }, [attachments, sortField, sortDirection])

  const handleSort = (field: 'name' | 'status' | 'size' | 'date') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const timelineEvents = useMemo<TimelineEvent[]>(() => {
    return history
      .map((entry) => ({
        id: `history-${entry.id}`,
        type: 'history' as const,
        timestamp: entry.created_at,
        title: entry.new_status
          ? `Durum: ${entry.new_status}`
          : 'Durum güncellendi',
        description: entry.changed_by,
        context:
          entry.old_status
            ? `Önce: ${entry.old_status}`
            : entry.change_source || entry.meta?.notes,
      }))
      .filter((event) => Boolean(event.timestamp))
      .sort(
        (a, b) =>
          new Date(b.timestamp).getTime() -
          new Date(a.timestamp).getTime(),
      )
  }, [history])

  const timelineTypeMeta: Record<
    TimelineEventType,
    { label: string; color: string }
  > = {
    history: { label: 'Fırsat', color: '#1976d2' },
  }

  const formatTimestamp = (value?: string) => {
    if (!value) return '-'
    return new Date(value).toLocaleString()
  }

  useEffect(() => {
    if (!opportunity) return
    fetchResults(opportunity.id)
    fetchTimeline(opportunity.id)
    fetchAttachments(opportunity.id)
  }, [opportunity])

  const fetchAttachments = async (opportunityId: number) => {
    try {
      const atts = await getAttachments(opportunityId)
      setAttachments(atts)
    } catch (err) {
      console.error('Error fetching attachments:', err)
    }
  }

  const handleDownloadAttachments = async () => {
    if (!opportunity) return

    // Check if there are attachments to download
    const undownloaded = attachments.filter(att => !att.downloaded || !att.local_path)
    if (undownloaded.length === 0) {
      setError('Tüm dokümanlar zaten indirilmiş')
      return
    }

    // Check if attachments have source_url
    const attachmentsWithoutUrl = undownloaded.filter(att => !att.source_url)
    if (attachmentsWithoutUrl.length > 0) {
      console.warn('Some attachments missing source_url:', attachmentsWithoutUrl)
      setError(`${attachmentsWithoutUrl.length} dokümanın kaynak linki yok. Sync işlemini tekrar çalıştırın.`)
      return
    }

    console.log('Starting download for opportunity:', opportunity.id)
    console.log('Attachments to download:', undownloaded.map(att => ({ id: att.id, name: att.name, source_url: att.source_url })))

    setDownloadLoading(true)
    setError(null)
    try {
      const response = await startAttachmentDownload(opportunity.id)
      console.log('Download response:', response)

      if (response?.job_id) {
        setDownloadJobId(response.job_id)
        // Poll job status
        pollDownloadJob(response.job_id)
      } else {
        console.error('No job_id in response:', response)
        setError('İndirme job\'u başlatılamadı: response.job_id bulunamadı')
        setDownloadLoading(false)
      }
    } catch (err: any) {
      console.error('Download error:', err)
      const errorMsg = err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'İndirme başlatılamadı'
      console.error('Error details:', {
        status: err?.response?.status,
        statusText: err?.response?.statusText,
        data: err?.response?.data
      })
      setError(errorMsg)
      setDownloadLoading(false)
    }
  }

  const pollDownloadJob = async (jobId: string) => {
    try {
      console.log('Polling download job:', jobId)
      const job = await getDownloadJob(jobId)
      console.log('Job status:', job.status, 'Downloaded:', job.downloaded_count, 'Failed:', job.failed_count)

      if (job.status === 'completed' || job.status === 'failed') {
        setDownloadLoading(false)
        setDownloadJobId(null)
        // Refresh attachments
        if (opportunity) {
          await fetchAttachments(opportunity.id)
        }
        if (job.status === 'failed' || (job.failed_count && job.failed_count > 0)) {
          // Fetch logs to see what went wrong
          try {
            const logs = await getDownloadLogs(jobId, 50)
            const errorLogs = logs.filter((log: any) => log.level === 'ERROR' || log.level === 'WARNING')
            console.error('Download failed. Error logs:', errorLogs)
            // Log each error in detail
            errorLogs.forEach((log: any, idx: number) => {
              console.error(`Error ${idx + 1}:`, {
                level: log.level,
                message: log.message,
                attachment: log.attachment_name,
                step: log.step,
                metadata: log.extra_metadata,
                timestamp: log.timestamp
              })
            })
            if (errorLogs.length > 0) {
              const errorMessages = errorLogs.map((log: any) =>
                `${log.attachment_name || 'Genel'}: ${log.message}`
              ).join('; ')
              setError(`İndirme başarısız: ${errorMessages}`)
            } else {
              setError(job.error_message || `İndirme başarısız: ${job.failed_count || 0} dosya indirilemedi`)
            }
          } catch (logErr) {
            console.error('Error fetching download logs:', logErr)
            setError(job.error_message || 'İndirme başarısız oldu')
          }
        } else {
          // Success - show success message
          const successMsg = `İndirme tamamlandı: ${job.downloaded_count || 0} başarılı, ${job.failed_count || 0} başarısız`
          console.log(successMsg)
          setError(null)
          // Show success alert temporarily
          setTimeout(() => {
            // Could show a success snackbar here
          }, 100)
        }
      } else {
        // Still running, poll again in 2 seconds
        setTimeout(() => pollDownloadJob(jobId), 2000)
      }
    } catch (err: any) {
      console.error('Error polling download job:', err)
      setDownloadLoading(false)
      setDownloadJobId(null)
      const errorMsg = `İndirme durumu kontrol edilemedi: ${err?.response?.data?.detail || err?.message || 'Bilinmeyen hata'}`
      setError(errorMsg)
    }
  }

  // Helper function to format file size
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Helper function to format date
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('tr-TR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Calculate download progress
  const downloadProgress = useMemo(() => {
    const total = attachments.length
    const downloaded = attachments.filter(att => att.downloaded && att.local_path).length
    return total > 0 ? (downloaded / total) * 100 : 0
  }, [attachments])

  // Calculate status chips for opportunity summary
  const getStatusChips = () => {
    const downloadedCount = attachments.filter(att => att.downloaded && att.local_path).length
    const totalAttachments = attachments.length
    const hasAnalysis = analysisResults.length > 0
    const hasHotelMatch = hotelMatches.length > 0

    return {
      documents: {
        label: `Dokümanlar: ${downloadedCount}/${totalAttachments}`,
        color: downloadedCount === totalAttachments && totalAttachments > 0 ? 'success' :
          downloadedCount > 0 ? 'warning' : 'error',
        icon: downloadedCount === totalAttachments && totalAttachments > 0 ? <CheckCircle /> :
          downloadedCount > 0 ? <Warning /> : <ErrorIcon />
      },
      pipeline: {
        label: `Pipeline: ${hasAnalysis ? analysisResults.length : 0} analiz`,
        color: hasAnalysis ? 'success' : 'default',
        icon: hasAnalysis ? <CheckCircle /> : <Description />
      },
      hotel: {
        label: `Otel: ${hasHotelMatch ? 'Eşleştirildi' : 'Beklemede'}`,
        color: hasHotelMatch ? 'success' : 'default',
        icon: hasHotelMatch ? <CheckCircle /> : <Hotel />
      }
    }
  }

  useEffect(() => {
    if (!selectedResult) return
    const fetchLogs = async () => {
      const logEntries = await getAnalysisLogs(selectedResult.id, 50)
      setLogs(logEntries)
    }
    fetchLogs()
  }, [selectedResult?.id])

  const fetchResults = async (opportunityId: number) => {
    try {
      const results = await listAnalysisResults(opportunityId, 10)
      setAnalysisResults(results)
      setSelectedResult(results[0] ?? null)
      if (results.length === 0) {
        setLogs([])
      }
    } catch (err: any) {
      setError(err?.message || 'Analiz sonuçları yüklenemedi')
    }
  }

  const fetchTimeline = async (opportunityId: number) => {
    try {
      const [historyData, runData, exampleData, emails, hotelData] = await Promise.all([
        getOpportunityHistory(opportunityId, 20),
        getAgentRuns(opportunityId, 10),
        getTrainingExamples(opportunityId, 10),
        getEmailLogs(opportunityId, 20),
        getHotelMatches(opportunityId, 5),
      ])
      setHistory(historyData)
      setAgentRuns(runData)
      setTrainingExamples(exampleData)
      setEmailLogs(emails)
      setHotelMatches(hotelData)

      try {
        const decision = await lookupDecisionPattern(opportunityId, {
          notice_id: opportunity?.noticeId,
        })
        setDecisionLookup(decision)
      } catch {
        setDecisionLookup(null)
      }
    } catch (err: any) {
      console.error('Timeline verileri yüklenemedi', err)
    }
  }

  const startAnalysis = async () => {
    if (!opportunity) {
      setError('Fırsat seçilmedi')
      return
    }

    console.log('Starting pipeline for opportunity:', opportunity.id)
    setRunning(true)
    setError(null)

    try {
      // Fetch attachments first
      console.log('Fetching attachments...')
      const attachments = await getAttachments(opportunity.id)
      console.log('Attachments fetched:', attachments.length)
      const attachmentIds = attachments.map(att => att.id)

      console.log('Calling runPipelineJob with:', {
        opportunityId: opportunity.id,
        analysisType: 'sow_draft',
        pipelineVersion: 'v1',
        attachmentIds: attachmentIds.length > 0 ? attachmentIds : undefined,
      })

      const response = await runPipelineJob({
        opportunityId: opportunity.id,
        analysisType: 'sow_draft',
        pipelineVersion: 'v1',
        attachmentIds: attachmentIds.length > 0 ? attachmentIds : undefined,
      })

      console.log('Pipeline job started:', response)

      if (response?.analysis_result_id) {
        await pollAnalysis(response.analysis_result_id)
        await fetchAttachments(opportunity.id)
        await fetchResults(opportunity.id)
      } else {
        setError('Pipeline başlatılamadı: analysis_result_id bulunamadı')
      }
    } catch (err: any) {
      console.error('Pipeline start error:', err)
      const errorMsg = err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Pipeline başlatılamadı'
      console.error('Error details:', {
        status: err?.response?.status,
        statusText: err?.response?.statusText,
        data: err?.response?.data,
        url: err?.config?.url
      })
      setError(errorMsg)
    } finally {
      setRunning(false)
    }
  }

  const startHotelMatch = async () => {
    if (!opportunity) return
    setHotelLoading(true)
    setError(null)
    try {
      // Fetch attachments first (hotel match might also need them)
      const attachments = await getAttachments(opportunity.id)
      const attachmentIds = attachments.map(att => att.id)

      const response = await runPipelineJob({
        opportunityId: opportunity.id,
        analysisType: 'hotel_match',
        pipelineVersion: 'v1',
        attachmentIds: attachmentIds.length > 0 ? attachmentIds : undefined,
        options: {
          city_name: opportunity.title?.split('-').pop()?.trim(),
        },
      })
      await pollAnalysis(response.analysis_result_id)
      await fetchTimeline(opportunity.id)
      await fetchAttachments(opportunity.id)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Hotel matcher başlatılamadı')
    } finally {
      setHotelLoading(false)
    }
  }

  const pollAnalysis = async (analysisResultId: number) => {
    const result = await getAnalysisResult(analysisResultId)
    await fetchResults(result.opportunity_id)
    if (result.status === 'completed' || result.status === 'failed') {
      setSelectedResult(result)
      return
    }
    setTimeout(() => pollAnalysis(analysisResultId), 3000)
  }

  if (!opportunity) {
    return (
      <Box sx={{ textAlign: 'center', py: 6 }}>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          Lütfen önce bir fırsat seçin.
        </Typography>
        <Button variant="outlined" onClick={onBack} startIcon={<ArrowBack />}>
          Fırsat Merkezine Dön
        </Button>
      </Box>
    )
  }

  const statusChips = getStatusChips()
  const [logTab, setLogTab] = useState(0)
  const [expandedAccordions, setExpandedAccordions] = useState<Set<string>>(new Set(['pipeline']))

  const handleAccordionChange = (panel: string) => {
    const newExpanded = new Set(expandedAccordions)
    if (newExpanded.has(panel)) {
      newExpanded.delete(panel)
    } else {
      newExpanded.add(panel)
    }
    setExpandedAccordions(newExpanded)
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Button onClick={onBack} startIcon={<ArrowBack />}>
          Geri
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            onClick={startAnalysis}
            disabled={running}
            startIcon={running ? <CircularProgress size={16} /> : <PlayArrow />}
          >
            {running ? 'Pipeline Çalışıyor...' : 'Yeni Pipeline Başlat'}
          </Button>
          <Button
            variant="outlined"
            onClick={startHotelMatch}
            disabled={hotelLoading}
            startIcon={hotelLoading ? <CircularProgress size={16} /> : <Hotel />}
          >
            {hotelLoading ? 'Otel aranıyor...' : 'Otel Önerisi'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() => setError(null)}
        >
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
            Hata:
          </Typography>
          {error}
          <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.8 }}>
            Detaylar için browser console'u açın (F12)
          </Typography>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Left Column - Main Content */}
        <Grid item xs={12} md={8}>
          {/* 1. Fırsat Özeti Kartı */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={8}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                    {opportunity.title || 'Fırsat Başlığı Yok'}
                  </Typography>
                  <Stack spacing={1}>
                    {opportunity.noticeId && (
                      <Typography variant="body2" color="text.secondary">
                        Notice ID: <strong>{opportunity.noticeId}</strong>
                      </Typography>
                    )}
                    {opportunity.agency && (
                      <Typography variant="body2" color="text.secondary">
                        Ajans: {opportunity.agency}
                      </Typography>
                    )}
                    {opportunity.responseDeadline && (
                      <Typography variant="body2" color="text.secondary">
                        Son Tarih: {new Date(opportunity.responseDeadline).toLocaleDateString()}
                      </Typography>
                    )}
                    {opportunity.samGovLink && (
                      <Box>
                        <Button
                          variant="outlined"
                          size="small"
                          href={opportunity.samGovLink}
                          target="_blank"
                          startIcon={<OpenInNew />}
                          sx={{
                            textTransform: 'none',
                            mt: 0.5
                          }}
                        >
                          SAM.gov'da Aç
                        </Button>
                      </Box>
                    )}
                  </Stack>
                  {opportunity.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      {opportunity.description.substring(0, 200)}...
                    </Typography>
                  )}
                </Grid>
                <Grid item xs={12} md={4}>
                  <Stack spacing={1} alignItems="flex-end">
                    <Chip
                      icon={statusChips.documents.icon}
                      label={statusChips.documents.label}
                      color={statusChips.documents.color as any}
                      size="small"
                    />
                    <Chip
                      icon={statusChips.pipeline.icon}
                      label={statusChips.pipeline.label}
                      color={statusChips.pipeline.color as any}
                      size="small"
                    />
                    <Chip
                      icon={statusChips.hotel.icon}
                      label={statusChips.hotel.label}
                      color={statusChips.hotel.color as any}
                      size="small"
                    />
                  </Stack>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* 2. Doküman Yönetimi Kartı */}
          <Card sx={{ mb: 3 }}>
            <CardHeader
              title="Doküman Yönetimi"
              action={
                <Button
                  size="small"
                  variant="outlined"
                  onClick={handleDownloadAttachments}
                  startIcon={downloadLoading ? <CircularProgress size={16} /> : <Download />}
                  disabled={attachments.length === 0 || downloadLoading}
                >
                  {downloadLoading ? 'İndiriliyor...' : 'Dokümanları İndir'}
                </Button>
              }
            />
            <CardContent>
              {attachments.length === 0 ? (
                <Alert severity="info">
                  Bu fırsat için henüz döküman eklenmemiş. Sync işlemi yaparak dökümanları yükleyebilirsiniz.
                  <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
                    Not: Sync işlemi sırasında SAM.gov'dan attachment metadata'sı (URL, isim vb.) veritabanına kaydedilir,
                    ancak dosyalar otomatik indirilmez. Dosyaları indirmek için "Dokümanları İndir" butonunu kullanın.
                  </Typography>
                </Alert>
              ) : (
                <>
                  {/* Progress Bar */}
                  {attachments.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
                        <Box sx={{ flex: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={downloadProgress}
                            sx={{ height: 8, borderRadius: 1 }}
                            color={downloadProgress === 100 ? 'success' : 'primary'}
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {attachments.filter(att => att.downloaded && att.local_path).length} / {attachments.length}
                        </Typography>
                      </Stack>
                    </Box>
                  )}

                  {downloadJobId && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                      İndirme işlemi devam ediyor (Job ID: {downloadJobId.substring(0, 8)}...)
                    </Alert>
                  )}
                  {attachments.filter(att => !att.downloaded || !att.local_path).length > 0 && !downloadLoading && (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      {attachments.filter(att => !att.downloaded || !att.local_path).length} döküman henüz indirilmemiş.
                      Pipeline çalıştırmadan önce "Dokümanları İndir" butonuna tıklayın.
                    </Alert>
                  )}
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>
                            <TableSortLabel
                              active={sortField === 'name'}
                              direction={sortField === 'name' ? sortDirection : 'asc'}
                              onClick={() => handleSort('name')}
                            >
                              <strong>Dosya</strong>
                            </TableSortLabel>
                          </TableCell>
                          <TableCell>
                            <TableSortLabel
                              active={sortField === 'status'}
                              direction={sortField === 'status' ? sortDirection : 'asc'}
                              onClick={() => handleSort('status')}
                            >
                              <strong>Durum</strong>
                            </TableSortLabel>
                          </TableCell>
                          <TableCell><strong>Boyut</strong></TableCell>
                          <TableCell><strong>Kaynak Link</strong></TableCell>
                          <TableCell><strong>Aksiyon</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {sortedAttachments.map((att) => (
                          <TableRow key={att.id} hover>
                            <TableCell>
                              <Stack direction="row" spacing={1} alignItems="center">
                                <FilePresent fontSize="small" color="action" />
                                <Typography variant="body2">{att.name || 'İsimsiz'}</Typography>
                              </Stack>
                            </TableCell>
                            <TableCell>
                              {att.downloaded && att.local_path ? (
                                <Chip
                                  size="small"
                                  label="İndirildi"
                                  color="success"
                                  icon={<CheckCircle />}
                                />
                              ) : att.downloaded === false ? (
                                <Chip
                                  size="small"
                                  label="İndirilmedi"
                                  color="warning"
                                  icon={<Warning />}
                                />
                              ) : (
                                <Chip size="small" label="Bilinmiyor" color="default" />
                              )}
                            </TableCell>
                            <TableCell>
                              <Stack direction="row" spacing={0.5} alignItems="center">
                                <Storage fontSize="small" color="action" />
                                <Typography variant="body2" color="text.secondary">
                                  {formatFileSize((att as any).size_bytes)}
                                </Typography>
                              </Stack>
                              {att.created_at && (
                                <Stack direction="row" spacing={0.5} alignItems="center" sx={{ mt: 0.5 }}>
                                  <AccessTime fontSize="small" color="action" sx={{ fontSize: 12 }} />
                                  <Typography variant="caption" color="text.secondary">
                                    {formatDate(att.created_at)}
                                  </Typography>
                                </Stack>
                              )}
                            </TableCell>
                            <TableCell>
                              {att.source_url ? (
                                <Button
                                  size="small"
                                  href={att.source_url}
                                  target="_blank"
                                  startIcon={<OpenInNew />}
                                  sx={{ textTransform: 'none' }}
                                >
                                  Kaynak Link
                                </Button>
                              ) : (
                                <Tooltip title="Kaynak link bulunmuyor">
                                  <Chip size="small" label="Link yok" color="error" variant="outlined" />
                                </Tooltip>
                              )}
                            </TableCell>
                            <TableCell>
                              <Stack direction="row" spacing={1}>
                                {att.local_path ? (
                                  <>
                                    <Button
                                      size="small"
                                      variant="outlined"
                                      href={`/api/files/${att.local_path.replace(/^data[\\/]/, '')}`}
                                      target="_blank"
                                      startIcon={<Download />}
                                      sx={{ textTransform: 'none' }}
                                    >
                                      İndir
                                    </Button>
                                    {!att.downloaded && (
                                      <Tooltip title="Yeniden indir">
                                        <IconButton
                                          size="small"
                                          onClick={() => {
                                            // Re-download single attachment
                                            handleDownloadAttachments()
                                          }}
                                        >
                                          <Refresh fontSize="small" />
                                        </IconButton>
                                      </Tooltip>
                                    )}
                                  </>
                                ) : (
                                  <Tooltip title="Dosya henüz indirilmemiş">
                                    <span>
                                      <Button
                                        size="small"
                                        variant="outlined"
                                        disabled
                                        sx={{ textTransform: 'none' }}
                                      >
                                        İndirilemedi
                                      </Button>
                                    </span>
                                  </Tooltip>
                                )}
                              </Stack>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              )}
            </CardContent>
          </Card>

          {/* 3. Pipeline Kartları (Accordion) */}
          <Accordion
            expanded={expandedAccordions.has('pipeline')}
            onChange={() => handleAccordionChange('pipeline')}
            sx={{ mb: 2 }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Analiz Çalıştır ({analysisResults.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ mb: 2 }}>
                <Tabs value={logTab} onChange={(_, v) => setLogTab(v)} sx={{ mb: 2 }}>
                  <Tab label="Analiz Sonuçları" />
                  <Tab label="Loglar" />
                </Tabs>

                {logTab === 0 ? (
                  analysisResults.length === 0 ? (
                    <Alert severity="info">
                      Henüz analiz kaydı yok. "Yeni Pipeline Başlat" butonuna tıklayarak analiz başlatabilirsiniz.
                    </Alert>
                  ) : (
                    <Grid container spacing={2}>
                      {analysisResults.map((result) => (
                        <Grid item xs={12} sm={6} key={result.id}>
                          <Card
                            variant="outlined"
                            sx={{
                              cursor: 'pointer',
                              border: selectedResult?.id === result.id ? 2 : 1,
                              borderColor: selectedResult?.id === result.id ? 'primary.main' : 'divider',
                              '&:hover': {
                                boxShadow: 2,
                                borderColor: 'primary.main'
                              }
                            }}
                            onClick={() => setSelectedResult(result)}
                          >
                            <CardContent>
                              <Stack spacing={1}>
                                <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                                  <Chip
                                    size="small"
                                    label={result.analysis_type}
                                    color={result.status === 'completed' ? 'success' : result.status === 'failed' ? 'error' : 'warning'}
                                  />
                                  <Chip
                                    size="small"
                                    label={result.status}
                                    color={result.status === 'completed' ? 'success' : result.status === 'failed' ? 'error' : 'default'}
                                    variant="outlined"
                                  />
                                </Stack>
                                {result.completed_at && (
                                  <Typography variant="caption" color="text.secondary">
                                    <AccessTime fontSize="inherit" sx={{ fontSize: 12, mr: 0.5, verticalAlign: 'middle' }} />
                                    {formatDate(result.completed_at)}
                                  </Typography>
                                )}
                                <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                                  <Button
                                    size="small"
                                    variant="outlined"
                                    href={`/api/pipeline/results/${result.id}/download-pdf`}
                                    target="_blank"
                                    startIcon={<Description />}
                                    sx={{ textTransform: 'none', flex: 1 }}
                                  >
                                    PDF
                                  </Button>
                                  <Button
                                    size="small"
                                    variant="outlined"
                                    href={`/api/pipeline/results/${result.id}/download-json`}
                                    target="_blank"
                                    startIcon={<Description />}
                                    sx={{ textTransform: 'none', flex: 1 }}
                                  >
                                    JSON
                                  </Button>
                                </Stack>
                              </Stack>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  )
                ) : (
                  <Box sx={{ maxHeight: 500, overflow: 'auto' }}>
                    {selectedResult ? (
                      logs.length === 0 ? (
                        <Alert severity="info">
                          Log bekleniyor... Pipeline çalıştıkça loglar burada görünecek.
                        </Alert>
                      ) : (
                        <Box sx={{ position: 'relative', pl: 3 }}>
                          {/* Timeline */}
                          {logs.map((log, index) => {
                            const isLast = index === logs.length - 1
                            const logColor = log.level === 'ERROR' ? 'error.main' :
                              log.level === 'WARNING' ? 'warning.main' :
                                log.level === 'INFO' ? 'info.main' : 'success.main'

                            return (
                              <Box key={log.id} sx={{ position: 'relative', pb: isLast ? 0 : 3 }}>
                                {/* Timeline line */}
                                {!isLast && (
                                  <Box
                                    sx={{
                                      position: 'absolute',
                                      left: 7,
                                      top: 24,
                                      bottom: -16,
                                      width: 2,
                                      backgroundColor: 'divider',
                                    }}
                                  />
                                )}
                                {/* Timeline dot */}
                                <Box
                                  sx={{
                                    position: 'absolute',
                                    left: 0,
                                    top: 4,
                                    width: 16,
                                    height: 16,
                                    borderRadius: '50%',
                                    backgroundColor: logColor,
                                    border: '2px solid',
                                    borderColor: 'background.paper',
                                    zIndex: 1,
                                  }}
                                />
                                {/* Log content */}
                                <Card variant="outlined" sx={{ ml: 2, mb: 1 }}>
                                  <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                                    <Stack spacing={1}>
                                      <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                                        <Chip
                                          size="small"
                                          label={log.level}
                                          color={
                                            log.level === 'ERROR' ? 'error' :
                                              log.level === 'WARNING' ? 'warning' :
                                                log.level === 'INFO' ? 'info' :
                                                  'success'
                                          }
                                        />
                                        {log.step && (
                                          <Typography variant="caption" color="text.secondary">
                                            {log.step}
                                          </Typography>
                                        )}
                                        {log.timestamp && (
                                          <Typography variant="caption" color="text.secondary">
                                            {formatDate(log.timestamp)}
                                          </Typography>
                                        )}
                                      </Stack>
                                      <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                                        {log.message}
                                      </Typography>
                                    </Stack>
                                  </CardContent>
                                </Card>
                              </Box>
                            )
                          })}
                        </Box>
                      )
                    ) : (
                      <Alert severity="info">
                        Log görmek için bir analiz kaydı seçin.
                      </Alert>
                    )}
                  </Box>
                )}
              </Box>
            </AccordionDetails>
          </Accordion>
          {/* 4. Otel Önerisi Kartı */}
          <Card sx={{ mb: 3 }}>
            <CardHeader
              title="Otel Önerisi"
              action={
                <Button
                  size="small"
                  variant="outlined"
                  onClick={startHotelMatch}
                  disabled={hotelLoading}
                  startIcon={hotelLoading ? <CircularProgress size={16} /> : <Hotel />}
                >
                  {hotelLoading ? 'Aranıyor...' : 'Çalıştır'}
                </Button>
              }
            />
            <CardContent>
              {!latestHotelMatch ? (
                <Alert severity="info">
                  Henüz hotel matcher çalıştırılmadı. "Çalıştır" butonuna tıklayarak otel önerisi alabilirsiniz.
                </Alert>
              ) : latestHotelMatch.hotels.length === 0 ? (
                <Alert severity="warning">
                  Otel önerisi bulunamadı.
                </Alert>
              ) : (
                <Grid container spacing={2}>
                  {latestHotelMatch.hotels.map((hotel, idx) => {
                    const score = hotel.score || 0
                    const scorePercent = (score * 100).toFixed(0)

                    return (
                      <Grid item xs={12} sm={6} md={4} key={hotel.amadeus_hotel_id || idx}>
                        <Card
                          variant="outlined"
                          sx={{
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            '&:hover': {
                              boxShadow: 3,
                              borderColor: 'primary.main'
                            }
                          }}
                        >
                          <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                            <Stack spacing={2}>
                              {/* Header with name and score */}
                              <Box>
                                <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                                  <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>
                                    {hotel.name || 'Otel'}
                                  </Typography>
                                  {score > 0 && (
                                    <Chip
                                      size="small"
                                      icon={<Star />}
                                      label={`${scorePercent}%`}
                                      color={score > 0.7 ? 'success' : score > 0.4 ? 'warning' : 'default'}
                                      sx={{ fontWeight: 600 }}
                                    />
                                  )}
                                </Stack>
                                {score > 0 && (
                                  <LinearProgress
                                    variant="determinate"
                                    value={score * 100}
                                    color={score > 0.7 ? 'success' : score > 0.4 ? 'warning' : 'primary'}
                                    sx={{ height: 6, borderRadius: 1, mt: 0.5 }}
                                  />
                                )}
                              </Box>

                              <Divider />

                              {/* Details */}
                              <Stack spacing={1.5}>
                                {hotel.currency && hotel.total_price && (
                                  <Stack direction="row" spacing={1} alignItems="center">
                                    <AttachMoney fontSize="small" color="primary" />
                                    <Typography variant="body2">
                                      <strong>Fiyat:</strong> {hotel.total_price} {hotel.currency}
                                    </Typography>
                                  </Stack>
                                )}

                                {(hotel as any).distance_miles && (
                                  <Stack direction="row" spacing={1} alignItems="center">
                                    <LocationOn fontSize="small" color="action" />
                                    <Typography variant="body2" color="text.secondary">
                                      {(hotel as any).distance_miles.toFixed(1)} mil uzaklık
                                    </Typography>
                                  </Stack>
                                )}

                                {hotel.notes && (
                                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                    {hotel.notes}
                                  </Typography>
                                )}
                              </Stack>

                              {/* Actions */}
                              <Box sx={{ mt: 'auto', pt: 1 }}>
                                {hotel.amadeus_hotel_id && (
                                  <Button
                                    fullWidth
                                    size="small"
                                    variant="contained"
                                    href={`https://www.amadeus.com/hotel/${hotel.amadeus_hotel_id}`}
                                    target="_blank"
                                    startIcon={<OpenInNew />}
                                    sx={{ textTransform: 'none' }}
                                  >
                                    Amadeus'ta Aç
                                  </Button>
                                )}
                              </Box>
                            </Stack>
                          </CardContent>
                        </Card>
                      </Grid>
                    )
                  })}
                </Grid>
              )}
              {latestHotelMatch?.reasoning && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2"><strong>Gerekçe:</strong> {latestHotelMatch.reasoning}</Typography>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Additional Accordions */}
          <Accordion
            expanded={expandedAccordions.has('agents')}
            onChange={() => handleAccordionChange('agents')}
            sx={{ mb: 2 }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                AI Ajan Akışı ({agentRuns.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {agentRuns.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Henüz agent çalıştırması kaydı yok.
                </Typography>
              ) : (
                <List dense>
                  {agentRuns.map((run) => (
                    <ListItem key={run.id}>
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Chip size="small" label={run.run_type} />
                            <Chip
                              size="small"
                              label={run.status}
                              color={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'default'}
                            />
                          </Stack>
                        }
                        secondary={[
                          run.started_at ? `Başlangıç: ${formatTimestamp(run.started_at)}` : null,
                          run.finished_at ? `Bitiş: ${formatTimestamp(run.finished_at)}` : null,
                          run.error_message ? `Hata: ${run.error_message}` : null,
                        ].filter(Boolean).join(' · ')}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </AccordionDetails>
          </Accordion>

          <Accordion
            expanded={expandedAccordions.has('decision')}
            onChange={() => handleAccordionChange('decision')}
            sx={{ mb: 2 }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Karar Önerisi
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {decisionLookup?.pattern ? (
                <Stack spacing={2}>
                  <Typography variant="body2">
                    {decisionLookup.pattern.pattern_desc || 'Desen açıklaması yok.'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Anahtar:</strong> {decisionLookup.pattern.key_hash}
                  </Typography>
                  {decisionLookup.signature && (
                    <Typography variant="body2" color="text.secondary">
                      <strong>İmza:</strong> {Object.entries(decisionLookup.signature)
                        .map(([key, value]) => `${key}: ${value}`)
                        .join(' · ')}
                    </Typography>
                  )}
                  {Array.isArray(decisionLookup.pattern.recommended_hotels) &&
                    decisionLookup.pattern.recommended_hotels.length > 0 ? (
                    <List dense>
                      {decisionLookup.pattern.recommended_hotels.map((hotel: any, idx: number) => (
                        <ListItem key={hotel.id || hotel.name || idx}>
                          <ListItemText
                            primary={`${hotel.name || 'Otel'}${hotel.city ? ` · ${hotel.city}` : ''}`}
                            secondary={[
                              hotel.distance_miles ? `${hotel.distance_miles.toFixed(1)} mil` : null,
                              hotel.room_rate ? `Oda: ${hotel.room_rate}` : null,
                              hotel.total_rooms ? `Oda sayısı: ${hotel.total_rooms}` : null,
                            ].filter(Boolean).join(' · ')}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Bu desen için kayıtlı otel listesi bulunamadı.
                    </Typography>
                  )}
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  {decisionLookup
                    ? 'Bu fırsat için hazır bir karar paterni bulunamadı.'
                    : 'Karar paterni henüz hesaplanmadı.'}
                </Typography>
              )}
            </AccordionDetails>
          </Accordion>

          <Accordion
            expanded={expandedAccordions.has('emails')}
            onChange={() => handleAccordionChange('emails')}
            sx={{ mb: 2 }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                E-posta Kayıtları ({emailLogs.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {emailLogs.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Henüz e-posta logu kaydedilmedi.
                </Typography>
              ) : (
                <List dense>
                  {emailLogs.slice(0, 10).map((email) => (
                    <ListItem key={email.id}>
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Chip
                              size="small"
                              label={email.direction === 'outbound' ? 'Giden' : 'Gelen'}
                              color={email.direction === 'outbound' ? 'primary' : 'default'}
                            />
                            <Typography variant="body2">
                              {email.subject || 'Konu yok'}
                            </Typography>
                          </Stack>
                        }
                        secondary={`${new Date(email.created_at).toLocaleString()} · ${email.from_address || email.to_address || ''
                          }`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Right Column - Timeline Sidebar */}
        <Grid item xs={12} md={4}>
          <Stack spacing={2}>
            {/* Timeline */}
            <Card>
              <CardHeader
                title={
                  <Stack direction="row" spacing={1} alignItems="center">
                    <TimelineIcon />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Fırsat Zaman Çizelgesi
                    </Typography>
                  </Stack>
                }
              />
              <CardContent>
                {timelineEvents.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    Henüz kaydedilmiş olay yok.
                  </Typography>
                ) : (
                  <Stack spacing={2} sx={{ position: 'relative', pl: 2 }}>
                    {timelineEvents.slice(0, 10).map((event, index) => {
                      const typeMeta = timelineTypeMeta[event.type]
                      return (
                        <Box key={event.id} sx={{ display: 'flex' }}>
                          <Box sx={{ position: 'relative', width: 24, display: 'flex', justifyContent: 'center' }}>
                            <Box
                              sx={{
                                width: 10,
                                height: 10,
                                borderRadius: '50%',
                                backgroundColor: typeMeta.color,
                                mt: 0.5,
                              }}
                            />
                            {index < Math.min(timelineEvents.length, 10) - 1 && (
                              <Box
                                sx={{
                                  position: 'absolute',
                                  top: 14,
                                  bottom: -16,
                                  width: 2,
                                  backgroundColor: 'divider',
                                }}
                              />
                            )}
                          </Box>
                          <Box sx={{ flex: 1, pl: 1.5 }}>
                            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                              {event.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              {formatTimestamp(event.timestamp)}
                            </Typography>
                            {event.description && (
                              <Typography variant="caption" sx={{ display: 'block' }}>
                                {event.description}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      )
                    })}
                  </Stack>
                )}
              </CardContent>
            </Card>

            {/* Training Examples */}
            <Card>
              <CardHeader
                title={
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    Eğitim Örnekleri ({trainingExamples.length})
                  </Typography>
                }
              />
              <CardContent>
                {trainingExamples.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    Henüz kayıt yok.
                  </Typography>
                ) : (
                  <List dense>
                    {trainingExamples.slice(0, 5).map((example) => (
                      <ListItem key={example.id}>
                        <ListItemText
                          primary={
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Chip size="small" label={example.example_type} />
                              <Typography variant="body2">
                                {example.outcome || 'N/A'}
                              </Typography>
                            </Stack>
                          }
                          secondary={`${new Date(example.created_at).toLocaleDateString()} · Puan: ${example.rating ?? '-'
                            }`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>
    </Box>
  )
}
