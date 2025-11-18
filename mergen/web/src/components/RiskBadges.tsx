'use client'

import { AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface RiskBadgesProps {
  total: number
  met: number
  gap: number
  risk: string
}

export function RiskBadges({ total, met, gap, risk }: RiskBadgesProps) {
  const metPercentage = total > 0 ? Math.round((met / total) * 100) : 0
  const gapPercentage = total > 0 ? Math.round((gap / total) * 100) : 0

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return 'success'
      case 'medium':
        return 'warning'
      case 'high':
        return 'danger'
      case 'critical':
        return 'danger'
      default:
        return 'secondary'
    }
  }

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'medium':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'high':
      case 'critical':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Info className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Requirements</p>
              <p className="text-2xl font-bold">{total}</p>
            </div>
            <Info className="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Met Requirements</p>
              <p className="text-2xl font-bold text-green-600">{met}</p>
              <p className="text-xs text-muted-foreground">{metPercentage}% compliance</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Gap Requirements</p>
              <p className="text-2xl font-bold text-red-600">{gap}</p>
              <p className="text-xs text-muted-foreground">{gapPercentage}% need attention</p>
            </div>
            <XCircle className="h-8 w-8 text-red-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Overall Risk</p>
              <div className="flex items-center space-x-2 mt-1">
                {getRiskIcon(risk)}
                <Badge variant={getRiskColor(risk) as any}>
                  {risk.toUpperCase()}
                </Badge>
              </div>
            </div>
            {risk.toLowerCase() === 'low' ? (
              <TrendingDown className="h-8 w-8 text-green-500" />
            ) : (
              <TrendingUp className="h-8 w-8 text-red-500" />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}