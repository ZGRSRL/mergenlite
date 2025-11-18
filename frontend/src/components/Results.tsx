import { useEffect, useState } from 'react'
import { Download, PictureAsPdf, Code, ExpandMore, ExpandLess } from '@mui/icons-material'
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
} from '@mui/material'
import { listGeneratedFiles, getArtifactUrl, listAllAnalysisResults, AnalysisResult } from '../api/pipeline'
import { getOpportunity, Opportunity } from '../api/opportunities'
import { Link } from '@mui/material'

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
    }
    setExpandedResults(newExpanded)
  }

  const getSamGovUrl = (noticeId?: string) => {
    if (!noticeId) return null
    return `https://sam.gov/opp/${noticeId}/view`
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
                                <Link
                                  href={samUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  sx={{ fontSize: '0.875rem', display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
                                >
                                  SAM.gov'da Görüntüle →
                                </Link>
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

                      {isExpanded && (
                        <Box sx={{ mt: 2 }}>
                          <Divider sx={{ mb: 2 }} />
                          <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                Analiz Detayları
                              </Typography>
                              <Stack spacing={0.5}>
                                <Typography variant="body2">
                                  <strong>Fırsat ID:</strong> {result.opportunity_id}
                                </Typography>
                                <Typography variant="body2">
                                  <strong>Agent:</strong> {result.agent_name || 'N/A'}
                                </Typography>
                                {result.confidence && (
                                  <Typography variant="body2">
                                    <strong>Güven:</strong> {(result.confidence * 100).toFixed(1)}%
                                  </Typography>
                                )}
                              </Stack>
                            </Grid>
                            <Grid item xs={12} md={6}>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                Dosya Yolları
                              </Typography>
                              <Stack spacing={0.5}>
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
                          </Grid>
                          {result.result_json && (
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                Analiz Özeti (JSON Önizleme)
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
                        </Box>
                      )}
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
