'use client'

import { useState } from 'react'
import { Download, Eye, FileText, CheckCircle, AlertTriangle, Clock, DollarSign } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'

interface DraftViewerProps {
  draft: {
    rfq_id: number
    executive_summary: string
    technical_approach: string
    past_performance: string
    pricing_summary: string
    compliance_matrix: string
    generated_at: string
    status: string
  }
}

export function DraftViewer({ draft }: DraftViewerProps) {
  const [activeSection, setActiveSection] = useState('executive')
  const [isPreviewMode, setIsPreviewMode] = useState(false)

  const sections = [
    { id: 'executive', title: 'Executive Summary', icon: FileText },
    { id: 'technical', title: 'Technical Approach', icon: CheckCircle },
    { id: 'performance', title: 'Past Performance', icon: Clock },
    { id: 'pricing', title: 'Pricing Summary', icon: DollarSign },
  ]

  const getSectionContent = (sectionId: string) => {
    switch (sectionId) {
      case 'executive':
        return draft.executive_summary
      case 'technical':
        return draft.technical_approach
      case 'performance':
        return draft.past_performance
      case 'pricing':
        return draft.pricing_summary
      default:
        return ''
    }
  }

  const handleDownload = async (format: 'docx' | 'pdf') => {
    try {
      const response = await fetch(`/api/proposal/download/${draft.rfq_id}?format=${format}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `proposal_${draft.rfq_id}.${format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Proposal Draft</h2>
          <p className="text-muted-foreground">
            Generated on {new Date(draft.generated_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={draft.status === 'complete' ? 'success' : 'warning'}>
            {draft.status}
          </Badge>
          <button
            onClick={() => setIsPreviewMode(!isPreviewMode)}
            className="flex items-center space-x-2 px-3 py-2 border rounded-md hover:bg-muted"
          >
            <Eye className="h-4 w-4" />
            <span>{isPreviewMode ? 'Edit' : 'Preview'}</span>
          </button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <Tabs value={activeSection} onValueChange={setActiveSection}>
            <TabsList className="grid w-full grid-cols-4">
              {sections.map((section) => (
                <TabsTrigger key={section.id} value={section.id} className="flex items-center space-x-2">
                  <section.icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{section.title}</span>
                </TabsTrigger>
              ))}
            </TabsList>

            {sections.map((section) => (
              <TabsContent key={section.id} value={section.id} className="p-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">{section.title}</h3>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleDownload('docx')}
                        className="flex items-center space-x-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                      >
                        <Download className="h-4 w-4" />
                        <span>Download DOCX</span>
                      </button>
                    </div>
                  </div>
                  
                  <div className="prose max-w-none">
                    {isPreviewMode ? (
                      <div 
                        className="whitespace-pre-wrap text-sm leading-relaxed"
                        dangerouslySetInnerHTML={{ 
                          __html: getSectionContent(section.id).replace(/\n/g, '<br/>') 
                        }}
                      />
                    ) : (
                      <textarea
                        value={getSectionContent(section.id)}
                        onChange={() => {}} // Read-only for now
                        className="w-full h-96 p-4 border rounded-md font-mono text-sm"
                        readOnly
                      />
                    )}
                  </div>
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Compliance Matrix</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Download the complete compliance matrix
              </p>
              <button
                onClick={() => handleDownload('docx')}
                className="flex items-center space-x-2 px-3 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90"
              >
                <Download className="h-4 w-4" />
                <span>Download Matrix</span>
              </button>
            </div>
            <div className="bg-muted p-4 rounded-md">
              <pre className="text-xs text-muted-foreground whitespace-pre-wrap">
                {draft.compliance_matrix}
              </pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}