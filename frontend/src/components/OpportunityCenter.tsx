import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  Grid,
  IconButton,
  Snackbar,
  TextField,
  Typography,
} from '@mui/material'
import {
  Download,
  ExpandLess,
  ExpandMore,
  OpenInNew,
  PlayArrow,
  Refresh,
  Search,
  Upload,
} from '@mui/icons-material'
import {
  Opportunity,
  loadOpportunities,
  OpportunityFilters,
  startSamSync,
  getSyncJob,
  getSyncLogs,
  startAttachmentDownload,
  getDownloadJob,
} from '../api/opportunities'

interface OpportunityCenterProps {
  onAnalyze: (opportunity: Opportunity) => void
}

interface JobInfo {
  jobId: string
  status: string
  logs?: string[]
  message?: string
}

export function OpportunityCenter({ onAnalyze }: OpportunityCenterProps) {
  const [searchParams, setSearchParams] = useState<OpportunityFilters>({
    noticeId: '',
    naicsCode: '721110',
    keyword: '',
  })
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(false)
  const [syncJob, setSyncJob] = useState<JobInfo | null>(null)
  const [downloadJob, setDownloadJob] = useState<JobInfo | null>(null)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' | 'warning' }>({
    open: false,
    message: '',
    severity: 'info',
  })
  const pendingOpportunities = useMemo(
    () => opportunities.filter((opp) => !opp.analyzed),
    [opportunities],
  )
  const analyzedOpportunities = useMemo(
    () => opportunities.filter((opp) => opp.analyzed),
    [opportunities],
  )

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (!syncJob?.jobId || ['completed', 'failed'].includes(syncJob.status)) return
    const interval = setInterval(async () => {
      try {
        const job = await getSyncJob(syncJob.jobId)
        const logs = await getSyncLogs(syncJob.jobId, 10)
        setSyncJob({
          jobId: job.job_id,
          status: job.status,
          logs: logs.map((log: any) => `${log.step || 'step'}: ${log.message}`),
          message: job.error_message,
        })
        if (job.status === 'completed' || job.status === 'failed') {
          clearInterval(interval)
          loadData()
        }
      } catch (error) {
        console.error('Error polling sync job', error)
        clearInterval(interval)
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [syncJob?.jobId, syncJob?.status])

  useEffect(() => {
    if (!downloadJob?.jobId || ['completed', 'failed'].includes(downloadJob.status)) return
    const interval = setInterval(async () => {
      try {
        const job = await getDownloadJob(downloadJob.jobId)
        setDownloadJob({
          jobId: job.job_id,
          status: job.status,
          message: job.error_message,
        })
        if (job.status === 'completed' || job.status === 'failed') {
          clearInterval(interval)
          loadData()
        }
      } catch (error) {
        console.error('Error polling download job', error)
        clearInterval(interval)
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [downloadJob?.jobId, downloadJob?.status])

  const loadData = async () => {
    setLoading(true)
    try {
      const data = await loadOpportunities(searchParams)
      setOpportunities(data)
    } catch (error) {
      console.error('Error loading opportunities', error)
      setSnackbar({
        open: true,
        message: 'Fırsatlar yüklenemedi',
        severity: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    await loadData()
    if (!loading && opportunities.length === 0) {
      setSnackbar({
        open: true,
        message: 'Sonuç bulunamadı. SAM sync yapmayı deneyin.',
        severity: 'info',
      })
    }
  }

  const handleSyncFromSam = async () => {
    setSnackbar({
      open: true,
      message: 'SAM.gov sync başlatıldı...',
      severity: 'info',
    })
    try {
      const response = await startSamSync({
        naics: searchParams.naicsCode || '721110',
        keyword: searchParams.keyword || undefined,
      })
      if (response?.job_id) {
        setSyncJob({
          jobId: response.job_id,
          status: 'running',
          logs: ['Sync job created...'],
        })
      } else {
        setSnackbar({
          open: true,
          message: 'Sync başlatılamadı.',
          severity: 'error',
        })
      }
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || 'Bilinmeyen hata'
      setSnackbar({
        open: true,
        message: `Sync hatası: ${message}`,
        severity: 'error',
      })
    }
  }

  const handleDownloadAttachments = async (opportunityId: number) => {
    try {
      const response = await startAttachmentDownload(opportunityId)
      if (response?.job_id) {
        setDownloadJob({
          jobId: response.job_id,
          status: 'running',
        })
        setSnackbar({
          open: true,
          message: 'Attachment indirme başlatıldı',
          severity: 'info',
        })
      } else {
        setSnackbar({
          open: true,
          message: 'İndirme başlatılamadı',
          severity: 'error',
        })
      }
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || 'Bilinmeyen hata'
      setSnackbar({
        open: true,
        message: `İndirme hatası: ${message}`,
        severity: 'error',
      })
    }
  }

  const getRiskLabel = (risk?: Opportunity['risk']) => {
    if (!risk) return null
    switch (risk) {
      case 'low':
        return 'Düşük Risk'
      case 'medium':
        return 'Orta Risk'
      case 'high':
        return 'Yüksek Risk'
      default:
        return risk
    }
  }

  const syncLogs = useMemo(() => syncJob?.logs ?? [], [syncJob])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Card sx={{ p: 2 }}>
        <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Typography variant="h6" sx={{ color: '#1e293b', fontWeight: 600 }}>
            Fırsat Filtreleri
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Notice ID"
                value={searchParams.noticeId}
                onChange={(e) => setSearchParams((prev) => ({ ...prev, noticeId: e.target.value }))}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="NAICS"
                value={searchParams.naicsCode}
                onChange={(e) => setSearchParams((prev) => ({ ...prev, naicsCode: e.target.value }))}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Anahtar Kelime"
                value={searchParams.keyword}
                onChange={(e) => setSearchParams((prev) => ({ ...prev, keyword: e.target.value }))}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleSearch}
                startIcon={<Search />}
                disabled={loading}
              >
                Ara
              </Button>
            </Grid>
            <Grid item xs={12} md={1}>
              <Button
                fullWidth
                variant="outlined"
                onClick={handleSyncFromSam}
                startIcon={syncJob?.status === 'running' ? <CircularProgress size={16} /> : <Refresh />}
                disabled={loading}
              >
                Sync
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {syncJob && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              Sync Job: {syncJob.jobId} ({syncJob.status})
            </Typography>
            {syncLogs.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                Log kaydı bekleniyor...
              </Typography>
            ) : (
              <Box component="ul" sx={{ pl: 3, m: 0 }}>
                {syncLogs.map((log, idx) => (
                  <li key={idx}>
                    <Typography variant="body2">{log}</Typography>
                  </li>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {downloadJob && (
        <Alert severity={downloadJob.status === 'failed' ? 'error' : 'info'}>
          Attachment indirme durumu: {downloadJob.status}
        </Alert>
      )}

      <Box>
        <Typography variant="h6" sx={{ mb: 1, color: '#1e293b', fontWeight: 600 }}>
          Analiz Bekleyen {pendingOpportunities.length} Fırsat
        </Typography>
        {analyzedOpportunities.length > 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {analyzedOpportunities.length} fırsat analiz edildi ve Sonuçlar sekmesinde listeleniyor.
          </Alert>
        )}

        {loading ? (
          <Typography>Yükleniyor...</Typography>
        ) : pendingOpportunities.length === 0 ? (
          <Typography color="text.secondary">
            Henüz analiz bekleyen fırsat yok. Tamamlanan fırsatların çıktıları Sonuçlar sayfasında.
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {pendingOpportunities.map((opp) => {
              const riskLabel = getRiskLabel(opp.risk)
              return (
                <Card key={opp.id}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Box>
                        <Typography variant="body2" sx={{ color: '#2563eb', fontWeight: 600 }}>
                          {opp.noticeId}
                        </Typography>
                        <Typography variant="h6" sx={{ color: '#1e293b', fontWeight: 600 }}>
                          {opp.title}
                        </Typography>
                      </Box>
                      {opp.samGovLink && (
                        <Button
                          size="small"
                          href={opp.samGovLink}
                          target="_blank"
                          startIcon={<OpenInNew />}
                        >
                          SAM.gov
                        </Button>
                      )}
                    </Box>

                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 1 }}>
                      {opp.postedDate && (
                        <Typography variant="caption" color="text.secondary">
                          Yayın: {opp.postedDate}
                        </Typography>
                      )}
                      {opp.responseDeadline && (
                        <Typography variant="caption" color="text.secondary">
                          Yanıt: {opp.responseDeadline}
                        </Typography>
                      )}
                      <Chip label={`${opp.daysLeft} gün`} size="small" />
                      {riskLabel && <Chip label={riskLabel} size="small" color="warning" />}
                    </Box>

                    {opp.description && (
                      <Box sx={{ mt: 1 }}>
                        <IconButton
                          size="small"
                          onClick={() => setExpandedId(expandedId === opp.id ? null : opp.id)}
                        >
                          {expandedId === opp.id ? <ExpandLess /> : <ExpandMore />}
                        </IconButton>
                        <Collapse in={expandedId === opp.id}>
                          <Typography variant="body2" color="text.secondary">
                            {opp.description}
                          </Typography>
                        </Collapse>
                      </Box>
                    )}

                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
                        gap: 1.5,
                        mt: 2,
                      }}
                    >
                      <Button
                        variant="contained"
                        startIcon={<PlayArrow />}
                        onClick={() => onAnalyze(opp)}
                      >
                        Analizi Başlat
                      </Button>
                      <Button variant="outlined" startIcon={<Upload />} disabled>
                        Doküman Yükle
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<Download />}
                        onClick={() => handleDownloadAttachments(opp.id)}
                      >
                        Dokümanları İndir
                      </Button>
                      <Button variant="outlined" startIcon={<Download />} disabled>
                        Klasörü Aç
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              )
            })}
          </Box>
        )}
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={snackbar.severity === 'error' ? 10000 : 4000}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
