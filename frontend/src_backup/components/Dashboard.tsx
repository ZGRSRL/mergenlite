import { useState, useEffect } from 'react'
import { TrendingUp, CheckCircle, Schedule } from '@mui/icons-material'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  CircularProgress,
} from '@mui/material'
import type { PageType } from './Navigation'
import { getDashboardStats, getRecentActivities, type RecentActivity } from '../api/dashboard'

interface DashboardProps {
  onNavigate: (page: PageType) => void
}

const aiAgents = [
  { name: 'Document Processor', icon: '📄', status: 'active' },
  { name: 'Requirements Extractor', icon: '🔍', status: 'active' },
  { name: 'Compliance Analyst', icon: '🛡️', status: 'active' },
  { name: 'Proposal Writer', icon: '✍️', status: 'active' },
]

export function Dashboard({ onNavigate }: DashboardProps) {
  const [stats, setStats] = useState({
    total_opportunities: 0,
    today_new: 0,
    analyzed_count: 0,
    avg_analysis_time: '0sn',
  })
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      const [statsData, activitiesData] = await Promise.all([
        getDashboardStats(),
        getRecentActivities(5),
      ])
      setStats(statsData)
      setRecentActivities(activitiesData)
    } catch (error) {
      console.error('Error loading dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (risk: 'low' | 'medium' | 'high') => {
    switch (risk) {
      case 'low':
        return { bg: '#d1fae5', text: '#047857', border: '#10b981' }
      case 'medium':
        return { bg: '#fef3c7', text: '#92400e', border: '#fbbf24' }
      case 'high':
        return { bg: '#fee2e2', text: '#991b1b', border: '#ef4444' }
    }
  }

  const getRiskLabel = (risk: 'low' | 'medium' | 'high') => {
    switch (risk) {
      case 'low':
        return 'Düşük Risk'
      case 'medium':
        return 'Orta Risk'
      case 'high':
        return 'Yüksek Risk'
    }
  }

  const formatNumber = (num: number | undefined | null) => {
    if (num === undefined || num === null || isNaN(num)) {
      return '0'
    }
    return num.toLocaleString('tr-TR')
  }

  const kpiCards = [
    {
      title: 'Toplam Fırsat Sayısı',
      value: formatNumber(stats.total_opportunities),
      icon: TrendingUp,
      gradient: 'linear-gradient(to bottom right, #2563eb, #3b82f6)',
    },
    {
      title: 'Bugün Yeni Eklenenler',
      value: formatNumber(stats.today_new),
      icon: CheckCircle,
      gradient: 'linear-gradient(to bottom right, #059669, #10b981)',
    },
    {
      title: 'Tamamlanan Analiz',
      value: formatNumber(stats.analyzed_count),
      icon: CheckCircle,
      gradient: 'linear-gradient(to bottom right, #9333ea, #a855f7)',
    },
    {
      title: 'Ortalama Analiz Süresi',
      value: stats.avg_analysis_time,
      icon: Schedule,
      gradient: 'linear-gradient(to bottom right, #ea580c, #f97316)',
    },
  ]

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {/* KPI Cards */}
      <Box>
        <Typography variant="h6" sx={{ mb: 3, color: '#1e293b', fontWeight: 600 }}>
          📊 Sistem Durumu
        </Typography>
        <Grid container spacing={2.5}>
          {kpiCards.map((card) => {
            const Icon = card.icon
            return (
              <Grid item xs={12} sm={6} lg={3} key={card.title}>
                <Card
                  sx={{
                    background: card.gradient,
                    color: 'white',
                    border: 'none',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    transition: 'all 0.3s',
                    '&:hover': {
                      transform: 'scale(1.05)',
                      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                    },
                    cursor: 'pointer',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.9)', mb: 1, display: 'block' }}>
                          {card.title}
                        </Typography>
                        <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>
                          {card.value}
                        </Typography>
                      </Box>
                      <Icon sx={{ color: 'rgba(255, 255, 255, 0.9)', fontSize: 28 }} />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )
          })}
        </Grid>
      </Box>

      {/* AI Agents & Recent Activities */}
      <Grid container spacing={3}>
        {/* AI Agents */}
        <Grid item xs={12} lg={4}>
          <Typography variant="h6" sx={{ mb: 3, color: '#1e293b', fontWeight: 600 }}>
            🤖 AI Ajanlar
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {aiAgents.map((agent) => (
              <Card
                key={agent.name}
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.8)',
                  backdropFilter: 'blur(12px)',
                  border: '1px solid rgba(226, 232, 240, 1)',
                  transition: 'all 0.3s',
                  '&:hover': {
                    borderColor: 'rgba(59, 130, 246, 0.4)',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="h5">{agent.icon}</Typography>
                    <Typography variant="body1" sx={{ flex: 1, color: '#334155', fontWeight: 500 }}>
                      {agent.name}
                    </Typography>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        bgcolor: '#10b981',
                        borderRadius: '50%',
                        boxShadow: '0 0 8px rgba(16, 185, 129, 0.5)',
                        animation: 'pulse 2s infinite',
                        '@keyframes pulse': {
                          '0%, 100%': { opacity: 1 },
                          '50%': { opacity: 0.5 },
                        },
                      }}
                    />
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Box>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12} lg={8}>
          <Typography variant="h6" sx={{ mb: 3, color: '#1e293b', fontWeight: 600 }}>
            📋 Son Aktiviteler
          </Typography>
          {recentActivities.length === 0 ? (
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  Henüz aktivite bulunamadı
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {recentActivities.map((activity) => {
                const riskColor = getRiskColor(activity.risk)
                return (
                  <Card
                    key={activity.id}
                    sx={{
                      bgcolor: 'rgba(255, 255, 255, 0.8)',
                      backdropFilter: 'blur(12px)',
                      border: '1px solid rgba(226, 232, 240, 1)',
                      transition: 'all 0.3s',
                      '&:hover': {
                        borderColor: 'rgba(59, 130, 246, 0.4)',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                      },
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 500 }}>
                          {activity.noticeId}
                        </Typography>
                        <Chip
                          label={getRiskLabel(activity.risk)}
                          size="small"
                          sx={{
                            bgcolor: riskColor.bg,
                            color: riskColor.text,
                            border: `1px solid ${riskColor.border}`,
                            fontWeight: 500,
                          }}
                        />
                      </Box>
                      <Typography variant="body1" sx={{ mb: 2, color: '#1e293b', fontWeight: 500 }}>
                        {activity.title}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Schedule sx={{ fontSize: 16, color: '#2563eb' }} />
                        <Typography variant="body2" sx={{ color: '#2563eb', fontWeight: 500 }}>
                          {activity.daysLeft} gün kaldı
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                )
              })}
            </Box>
          )}
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          onClick={() => onNavigate('opportunities')}
          sx={{
            flex: 1,
            background: 'linear-gradient(to right, #2563eb, #3b82f6)',
            boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.3)',
            '&:hover': {
              background: 'linear-gradient(to right, #1d4ed8, #2563eb)',
              boxShadow: '0 6px 8px -1px rgba(37, 99, 235, 0.4)',
            },
          }}
        >
          🔍 Fırsat Ara
        </Button>
        <Button
          variant="outlined"
          onClick={() => onNavigate('results')}
          sx={{
            flex: 1,
            borderColor: '#cbd5e1',
            color: '#334155',
            '&:hover': {
              bgcolor: '#f1f5f9',
              borderColor: '#94a3b8',
            },
            fontWeight: 500,
          }}
        >
          📊 Sonuçları Görüntüle
        </Button>
      </Box>
    </Box>
  )
}

