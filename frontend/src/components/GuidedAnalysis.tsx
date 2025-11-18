import { useEffect, useMemo, useState } from 'react'
import { ArrowBack } from '@mui/icons-material'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
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
  OpportunityHistoryEntry,
  AgentRunSummary,
  TrainingExampleSummary,
  DecisionCacheLookupResponse,
  EmailLogEntry,
  HotelMatchResult,
} from '../api/opportunities'
import {
  runPipelineJob,
  listAnalysisResults,
  getAnalysisResult,
  getAnalysisLogs,
  AnalysisResult,
  AnalysisLog,
} from '../api/pipeline'

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
  const latestHotelMatch = hotelMatches[0] ?? null

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
    if (!opportunity) return
    setRunning(true)
    setError(null)
    try {
      // Fetch attachments first
      const attachments = await getAttachments(opportunity.id)
      const attachmentIds = attachments.map(att => att.id)
      
      const response = await runPipelineJob({
        opportunityId: opportunity.id,
        analysisType: 'sow_draft',
        pipelineVersion: 'v1',
        attachmentIds: attachmentIds.length > 0 ? attachmentIds : undefined,
      })
      await pollAnalysis(response.analysis_result_id)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Pipeline başlatılamadı')
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

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Button onClick={onBack} startIcon={<ArrowBack />}>
          Geri
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            onClick={startAnalysis}
            disabled={running}
            startIcon={running ? <CircularProgress size={16} /> : undefined}
          >
            {running ? 'Pipeline ??al??Y??yor...' : 'Yeni Pipeline Ba?Ylat'}
          </Button>
          <Button
            variant="outlined"
            onClick={startHotelMatch}
            disabled={hotelLoading}
            startIcon={hotelLoading ? <CircularProgress size={16} /> : undefined}
          >
            {hotelLoading ? 'Otel aran??yor...' : 'Otel ??nerisi'}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Attachments Section */}
      {attachments.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
              Fırsat Dökümanları ({attachments.length})
            </Typography>
            <List dense>
              {attachments.map((att) => (
                <ListItem key={att.id}>
                  <ListItemText
                    primary={att.name}
                    secondary={
                      <Box>
                        {att.downloaded ? (
                          <Chip size="small" label="İndirildi" color="success" sx={{ mr: 1 }} />
                        ) : (
                          <Chip size="small" label="İndirilmedi" color="warning" sx={{ mr: 1 }} />
                        )}
                        {att.source_url && (
                          <Button
                            size="small"
                            href={att.source_url}
                            target="_blank"
                            sx={{ textTransform: 'none' }}
                          >
                            Kaynak Link
                          </Button>
                        )}
                        {att.local_path && (
                          <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                            {att.local_path}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Analiz Kayıtları
              </Typography>
              {analysisResults.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Henüz analiz kaydı yok.
                </Typography>
              ) : (
                <List dense>
                  {analysisResults.map((result) => (
                    <ListItem
                      key={result.id}
                      button
                      selected={selectedResult?.id === result.id}
                      onClick={() => setSelectedResult(result)}
                    >
                      <ListItemText
                        primary={`${result.analysis_type} · ${result.status}`}
                        secondary={
                          result.completed_at
                            ? new Date(result.completed_at).toLocaleString()
                            : 'Devam ediyor...'
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Pipeline Logları
              </Typography>
              {selectedResult ? (
                logs.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    Log bekleniyor...
                  </Typography>
                ) : (
                  <List dense>
                    {logs.map((log) => (
                      <ListItem key={log.id}>
                        <ListItemText
                          primary={`${log.level} · ${log.step || 'pipeline'}`}
                          secondary={log.message}
                        />
                      </ListItem>
                    ))}
                  </List>
                )
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Log görmek için bir analiz kaydı seçin.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>



      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Fırsat Zaman Çizelgesi
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Seçili fırsatın durum değişiklikleri kronolojik olarak listelenir.
              </Typography>
              {timelineEvents.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Henüz kaydedilmiş olay yok.
                </Typography>
              ) : (
                <Stack spacing={3} sx={{ position: 'relative', pl: 2 }}>
                  {timelineEvents.map((event, index) => {
                    const typeMeta = timelineTypeMeta[event.type]
                    return (
                      <Box key={event.id} sx={{ display: 'flex' }}>
                        <Box sx={{ position: 'relative', width: 24, display: 'flex', justifyContent: 'center' }}>
                          <Box
                            sx={{
                              width: 12,
                              height: 12,
                              borderRadius: '50%',
                              backgroundColor: typeMeta.color,
                              mt: 0.5,
                            }}
                          />
                          {index < timelineEvents.length - 1 && (
                            <Box
                              sx={{
                                position: 'absolute',
                                top: 16,
                                bottom: -24,
                                width: 2,
                                backgroundColor: 'divider',
                              }}
                            />
                          )}
                        </Box>
                        <Box sx={{ flex: 1, pl: 2 }}>
                          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5, flexWrap: 'wrap' }}>
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              {event.title}
                            </Typography>
                            <Chip
                              size="small"
                              label={typeMeta.label}
                              sx={{
                                bgcolor: `${typeMeta.color}22`,
                                color: typeMeta.color,
                                textTransform: 'capitalize',
                              }}
                            />
                          </Stack>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                            {formatTimestamp(event.timestamp)}
                          </Typography>
                          {event.description && (
                            <Typography variant="body2" sx={{ mb: event.context ? 0.5 : 0 }}>
                              {event.description}
                            </Typography>
                          )}
                          {event.context && (
                            <Typography variant="body2" color="text.secondary">
                              {event.context}
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
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                AI Ajan Akışı
              </Typography>
              {agentRuns.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Henüz agent çalıştırması kaydı yok.
                </Typography>
              ) : (
                <List dense>
                  {agentRuns.map((run) => (
                    <ListItem key={run.id} alignItems="flex-start">
                      <ListItemText
                        primary={`${run.run_type} · ${run.status}`}
                        secondary={[
                          run.started_at ? `Başlangıç: ${formatTimestamp(run.started_at)}` : null,
                          run.finished_at ? `Bitiş: ${formatTimestamp(run.finished_at)}` : null,
                          run.error_message ? `Hata: ${run.error_message}` : null,
                        ]
                          .filter(Boolean)
                          .join(' · ')}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Eğitim örnekleri
              </Typography>
              {trainingExamples.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Henüz kayıt yok.
                </Typography>
              ) : (
                <List dense>
                  {trainingExamples.map((example) => (
                    <ListItem key={example.id}>
                      <ListItemText
                        primary={`${example.example_type} · ${example.outcome || 'N/A'}`}
                        secondary={`${new Date(example.created_at).toLocaleString()} · Puan: ${
                          example.rating ?? '-'
                        }`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Stack spacing={2}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                  Karar önerisi
                </Typography>
                {decisionLookup?.pattern ? (
                  <>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      {decisionLookup.pattern.pattern_desc || 'Desen açıklaması yok.'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Anahtar: {decisionLookup.pattern.key_hash}
                    </Typography>
                    {decisionLookup.signature && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {Object.entries(decisionLookup.signature)
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
                              ]
                                .filter(Boolean)
                                .join(' · ')}
                            />
                          </ListItem>
                        ))}
                      </List>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Bu desen için kayıtlı otel listesi bulunamadı.
                      </Typography>
                    )}
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {decisionLookup
                      ? 'Bu fırsat için hazır bir karar paterni bulunamadı.'
                      : 'Karar paterni henüz hesaplanmadı.'}
                  </Typography>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                  E-posta kayıtları
                </Typography>
                {emailLogs.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    Henüz e-posta logu kaydedilmedi.
                  </Typography>
                ) : (
                  <List dense>
                    {emailLogs.slice(0, 5).map((email) => (
                      <ListItem key={email.id}>
                        <ListItemText
                          primary={`${email.direction === 'outbound' ? 'Giden' : 'Gelen'} · ${
                            email.subject || 'Konu yok'
                          }`}
                          secondary={`${new Date(email.created_at).toLocaleString()} · ${
                            email.from_address || email.to_address || ''
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
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Önerilen Oteller
              </Typography>
              {!latestHotelMatch ? (
                <Typography variant="body2" color="text.secondary">
                  Henüz hotel matcher çalıştırılmadı.
                </Typography>
              ) : latestHotelMatch.hotels.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Otel önerisi bulunamadı.
                </Typography>
              ) : (
                <List dense>
                  {latestHotelMatch.hotels.map((hotel, idx) => (
                    <ListItem key={`${hotel.amadeus_hotel_id || idx}`}>
                      <ListItemText
                        primary={`${hotel.name || 'Otel'}${
                          hotel.currency && hotel.total_price ? ` · ${hotel.total_price} ${hotel.currency}` : ''
                        }`}
                        secondary={(
                          [
                            hotel.score ? `Skor: ${(hotel.score * 100).toFixed(0)}%` : null,
                            hotel.notes,
                          ]
                            .filter(Boolean)
                            .join(' · ')
                        )}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
              {latestHotelMatch?.reasoning && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {latestHotelMatch.reasoning}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
