const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Health check
  async healthCheck() {
    return this.request('/api/health')
  }

  // Document ingestion
  async processLocalFiles() {
    return this.request('/api/ingest/local', {
      method: 'POST',
    })
  }

  async uploadDocument(file: File, kind: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('kind', kind)

    return this.request('/api/ingest/upload', {
      method: 'POST',
      body: formData,
      headers: {}, // Let fetch set Content-Type for FormData
    })
  }

  // Compliance
  async getComplianceMatrix(rfqId: number) {
    return this.request(`/api/compliance/matrix?rfq_id=${rfqId}`)
  }

  async getRequirements(rfqId: number) {
    return this.request(`/api/compliance/requirements/${rfqId}`)
  }

  // Pricing
  async loadPricingData(rfqId: number) {
    return this.request(`/api/pricing/load?rfq_id=${rfqId}`, {
      method: 'POST',
    })
  }

  async getPricingQuote(rfqId: number) {
    return this.request(`/api/pricing/quote?rfq_id=${rfqId}`)
  }

  // Proposal
  async generateProposalDraft(rfqId: number, format: string = 'json') {
    return this.request(`/api/proposal/draft?rfq_id=${rfqId}&format=${format}`, {
      method: 'POST',
    })
  }

  async downloadProposal(rfqId: number, format: string = 'docx') {
    const response = await fetch(`${this.baseUrl}/api/proposal/draft/${rfqId}/download?format=${format}`)
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status} ${response.statusText}`)
    }

    return response.blob()
  }

  // Search
  async searchDocuments(query: string, documentType?: string, limit: number = 10) {
    const params = new URLSearchParams({
      query,
      limit: limit.toString(),
    })
    
    if (documentType) {
      params.append('document_type', documentType)
    }

    return this.request(`/api/search?${params.toString()}`)
  }
}

export const apiClient = new ApiClient()



