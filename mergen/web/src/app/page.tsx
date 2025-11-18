'use client'

import { useState, useEffect } from 'react'
import { UploadPanel } from '@/components/UploadPanel'
import { ComplianceTable } from '@/components/ComplianceTable'
import { DraftViewer } from '@/components/DraftViewer'
import { RiskBadges } from '@/components/RiskBadges'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/app/api'

export default function Home() {
  const [rfqId, setRfqId] = useState<number | null>(null)
  const [complianceMatrix, setComplianceMatrix] = useState<any>(null)
  const [proposalDraft, setProposalDraft] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('upload')

  const handleFileUpload = async (files: FileList) => {
    setLoading(true)
    setError(null)
    
    try {
      // Process local files first
      const response = await apiClient.processLocalFiles()
      
      if (response.files && response.files.length > 0) {
        const rfqFile = response.files.find((f: any) => f.kind === 'rfq')
        if (rfqFile) {
          setRfqId(rfqFile.id)
          setActiveTab('compliance')
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const loadComplianceMatrix = async () => {
    if (!rfqId) return
    
    setLoading(true)
    setError(null)
    
    try {
      const matrix = await apiClient.getComplianceMatrix(rfqId)
      setComplianceMatrix(matrix)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const generateProposal = async () => {
    if (!rfqId) return
    
    setLoading(true)
    setError(null)
    
    try {
      const draft = await apiClient.generateProposalDraft(rfqId)
      setProposalDraft(draft)
      setActiveTab('proposal')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (rfqId) {
      loadComplianceMatrix()
    }
  }, [rfqId])

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">
          ZgrBid Dashboard
        </h1>
        <p className="text-xl text-muted-foreground">
          RFQ Analysis & Proposal Generation Platform
        </p>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upload">📁 Upload Documents</TabsTrigger>
          <TabsTrigger value="compliance" disabled={!rfqId}>
            📊 Compliance Matrix
          </TabsTrigger>
          <TabsTrigger value="proposal" disabled={!proposalDraft}>
            📝 Proposal Draft
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Document Upload</CardTitle>
              <CardDescription>
                Upload RFQ, SOW, facility specifications, past performance, and pricing documents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <UploadPanel onFileUpload={handleFileUpload} loading={loading} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="compliance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Compliance Analysis</CardTitle>
              <CardDescription>
                Review requirement compliance and risk assessment
              </CardDescription>
            </CardHeader>
            <CardContent>
              {complianceMatrix && (
                <div className="space-y-6">
                  <RiskBadges 
                    total={complianceMatrix.total_requirements}
                    met={complianceMatrix.met_requirements}
                    gap={complianceMatrix.gap_requirements}
                    risk={complianceMatrix.overall_risk}
                  />
                  <ComplianceTable matrix={complianceMatrix} />
                </div>
              )}
              {!complianceMatrix && rfqId && (
                <div className="text-center py-8">
                  <button
                    onClick={loadComplianceMatrix}
                    disabled={loading}
                    className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
                  >
                    {loading ? 'Loading...' : 'Load Compliance Matrix'}
                  </button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="proposal" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Proposal Draft</CardTitle>
              <CardDescription>
                Generated proposal sections and compliance documentation
              </CardDescription>
            </CardHeader>
            <CardContent>
              {proposalDraft ? (
                <DraftViewer draft={proposalDraft} />
              ) : (
                <div className="text-center py-8">
                  <button
                    onClick={generateProposal}
                    disabled={loading || !rfqId}
                    className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
                  >
                    {loading ? 'Generating...' : 'Generate Proposal Draft'}
                  </button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}