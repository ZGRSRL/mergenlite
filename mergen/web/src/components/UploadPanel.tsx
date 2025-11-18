'use client'

import { useState, useRef } from 'react'
import { Upload, FileText, X, File, FileSpreadsheet, Image } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

interface UploadPanelProps {
  onFileUpload: (files: FileList) => void
  loading: boolean
}

export function UploadPanel({ onFileUpload, loading }: UploadPanelProps) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFiles(Array.from(e.dataTransfer.files))
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  const handleUpload = () => {
    if (selectedFiles.length > 0) {
      const fileList = new DataTransfer()
      selectedFiles.forEach(file => fileList.items.add(file))
      onFileUpload(fileList.files)
      setSelectedFiles([])
    }
  }

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') return <FileText className="h-6 w-6 text-red-500" />
    if (file.type.includes('spreadsheet') || file.name.endsWith('.xlsx')) return <FileSpreadsheet className="h-6 w-6 text-green-500" />
    if (file.type.startsWith('image/')) return <Image className="h-6 w-6 text-blue-500" />
    return <File className="h-6 w-6 text-gray-500" />
  }

  const getFileType = (file: File) => {
    if (file.type === 'application/pdf') {
      if (file.name.toLowerCase().includes('rfq')) return 'RFQ'
      if (file.name.toLowerCase().includes('sow')) return 'SOW'
      if (file.name.toLowerCase().includes('facility') || file.name.toLowerCase().includes('technical')) return 'Facility'
      if (file.name.toLowerCase().includes('performance')) return 'Past Performance'
      return 'PDF Document'
    }
    if (file.type.includes('spreadsheet') || file.name.endsWith('.xlsx')) return 'Pricing Spreadsheet'
    return 'Document'
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Document Upload</h2>
        <p className="text-muted-foreground">
          Upload your RFQ, SOW, facility specifications, past performance, and pricing documents
        </p>
      </div>
      
      <Card>
        <CardContent className="p-8">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-muted-foreground/50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
            <p className="text-xl font-medium mb-2">
              Drag and drop files here, or click to select
            </p>
            <p className="text-sm text-muted-foreground mb-6">
              Supports PDF, Excel, and other document formats
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 font-medium"
            >
              Select Files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.xlsx,.xls,.docx,.doc"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        </CardContent>
      </Card>

      {selectedFiles.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold mb-4">Selected Files</h3>
            <div className="space-y-3">
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-muted rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    {getFileIcon(file)}
                    <div>
                      <p className="font-medium">{file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {getFileType(file)} • {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-destructive hover:text-destructive/80 p-1"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <button
                onClick={handleUpload}
                disabled={loading}
                className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 font-medium"
              >
                {loading ? 'Processing...' : 'Upload Files'}
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="text-sm text-muted-foreground">
        <p className="font-medium mb-2">Supported file types:</p>
        <ul className="space-y-1">
          <li>• RFQ/SOW documents (PDF)</li>
          <li>• Facility specifications (PDF)</li>
          <li>• Past performance records (PDF)</li>
          <li>• Pricing spreadsheets (Excel)</li>
        </ul>
      </div>
    </div>
  )
}
