import api from './client'

const API_BASE = '/api'

export interface DashboardStats {
  total_opportunities: number
  today_new: number
  analyzed_count: number
  avg_analysis_time: string
}

export interface RecentActivity {
  id: string
  noticeId: string
  title: string
  risk: 'low' | 'medium' | 'high'
  daysLeft: number
  publishedDate?: string
  responseDeadline?: string
  samGovLink?: string
}

export async function getDashboardStats(): Promise<DashboardStats> {
  try {
    const { data } = await api.get(`${API_BASE}/dashboard/stats`)
    return data
  } catch (error) {
    console.error('Error fetching dashboard stats:', error)
    // Return default values on error
    return {
      total_opportunities: 0,
      today_new: 0,
      analyzed_count: 0,
      avg_analysis_time: '0sn',
    }
  }
}

export async function getRecentActivities(limit: number = 5): Promise<RecentActivity[]> {
  try {
    const { data } = await api.get(`${API_BASE}/dashboard/recent-activities`, {
      params: { limit },
    })
    return data.activities || []
  } catch (error) {
    console.error('Error fetching recent activities:', error)
    return []
  }
}

