'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, AlertTriangle, CheckCircle, XCircle, Filter } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface ComplianceTableProps {
  matrix: {
    rfq_id: number
    items: Array<{
      requirement: {
        id: number
        code: string
        text: string
        category: string
        priority: string
      }
      evidence: Array<{
        id: number
        snippet: string
        score: number
        evidence_type: string
        source_doc_title?: string
      }>
      risk_level: string
      gap_analysis: string
      mitigation: string
    }>
    overall_risk: string
    total_requirements: number
    met_requirements: number
    gap_requirements: number
  }
}

export function ComplianceTable({ matrix }: ComplianceTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())
  const [filterCategory, setFilterCategory] = useState<string>('all')

  const toggleRow = (requirementId: number) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(requirementId)) {
      newExpanded.delete(requirementId)
    } else {
      newExpanded.add(requirementId)
    }
    setExpandedRows(newExpanded)
  }

  const filteredItems = filterCategory === 'all' 
    ? matrix.items 
    : matrix.items.filter(item => item.requirement.category === filterCategory)

  const categories = ['all', ...Array.from(new Set(matrix.items.map(item => item.requirement.category)))]

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'medium':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />
      case 'critical':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusIcon = (riskLevel: string) => {
    if (riskLevel === 'low' || riskLevel === 'medium') {
      return <CheckCircle className="h-4 w-4 text-green-500" />
    }
    return <XCircle className="h-4 w-4 text-red-500" />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Compliance Matrix</h2>
          <p className="text-muted-foreground">
            {matrix.met_requirements} of {matrix.total_requirements} requirements met
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            {categories.map(category => (
              <option key={category} value={category}>
                {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Requirement</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Category</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Risk</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Evidence</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredItems.map((item) => (
                  <tr key={item.requirement.id} className="hover:bg-muted/50">
                    <td className="px-4 py-3">
                      <div className="flex items-center">
                        {getStatusIcon(item.risk_level)}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{item.requirement.code}</div>
                      <div className="text-sm text-muted-foreground max-w-md">
                        {item.requirement.text}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="secondary">
                        {item.requirement.category}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        {getRiskIcon(item.risk_level)}
                        <Badge 
                          variant={
                            item.risk_level === 'low' ? 'success' :
                            item.risk_level === 'medium' ? 'warning' :
                            item.risk_level === 'high' ? 'danger' : 'danger'
                          }
                        >
                          {item.risk_level.toUpperCase()}
                        </Badge>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm">
                        {item.evidence.length} evidence
                        {item.evidence.length > 0 && (
                          <div className="text-xs text-muted-foreground">
                            Avg score: {(item.evidence.reduce((sum, e) => sum + e.score, 0) / item.evidence.length).toFixed(2)}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleRow(item.requirement.id)}
                        className="p-1 hover:bg-muted rounded"
                      >
                        {expandedRows.has(item.requirement.id) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Expanded details */}
      {Array.from(expandedRows).map(requirementId => {
        const item = matrix.items.find(i => i.requirement.id === requirementId)
        if (!item) return null

        return (
          <Card key={requirementId} className="mt-4">
            <CardHeader>
              <CardTitle className="text-lg">
                {item.requirement.code} - {item.requirement.text}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {item.evidence.length > 0 ? (
                  <div>
                    <h4 className="font-semibold mb-3">Evidence ({item.evidence.length}):</h4>
                    <div className="space-y-3">
                      {item.evidence.map((evidence, idx) => (
                        <div key={idx} className="p-4 bg-muted rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-sm">
                              {evidence.source_doc_title || `Evidence ${idx + 1}`}
                            </span>
                            <Badge variant="outline">
                              Score: {evidence.score.toFixed(2)}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {evidence.snippet}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
                    <p>No evidence found for this requirement</p>
                  </div>
                )}

                {item.gap_analysis && (
                  <div>
                    <h4 className="font-semibold mb-2">Gap Analysis:</h4>
                    <p className="text-sm text-muted-foreground">
                      {item.gap_analysis}
                    </p>
                  </div>
                )}

                {item.mitigation && (
                  <div>
                    <h4 className="font-semibold mb-2">Mitigation Strategy:</h4>
                    <p className="text-sm text-muted-foreground">
                      {item.mitigation}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}