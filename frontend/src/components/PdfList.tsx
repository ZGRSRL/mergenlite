import { useState, useEffect } from 'react'
import { Card, CardContent, Typography, Box, List, ListItem, ListItemText, Button } from '@mui/material'
import { Description, Download } from '@mui/icons-material'
import { listGeneratedFiles, getArtifactUrl } from '../api/pipeline'

interface PdfFile {
  filename?: string
  path: string
  size?: number
  created?: number
  modified?: number
}

export function PdfList() {
  const [files, setFiles] = useState<PdfFile[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadFiles()
    const interval = setInterval(loadFiles, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadFiles = async () => {
    try {
      const fileList = await listGeneratedFiles()
      setFiles(fileList)
    } catch (error) {
      console.error('Error loading files:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (timestamp?: number) => {
    if (!timestamp) return new Date().toLocaleString()
    return new Date(timestamp * 1000).toLocaleString()
  }

  const formatSize = (bytes?: number) => {
    if (!bytes) return '0 B'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <Description />
          <Typography variant="h6">Latest SOW PDFs</Typography>
        </Box>
        {loading ? (
          <Typography variant="body2" color="text.secondary">
            Loading...
          </Typography>
        ) : files.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No PDFs generated yet.
          </Typography>
        ) : (
          <List dense>
            {files.slice(0, 5).map((file) => (
              <ListItem
                key={file.path}
                secondaryAction={
                  <Button size="small" href={getArtifactUrl(file.path)} target="_blank" startIcon={<Download />}>
                    Open
                  </Button>
                }
              >
                <ListItemText
                  primary={file.filename || file.path.split('/').pop() || 'Generated PDF'}
                  secondary={`${formatSize(file.size)} · ${formatDate(file.modified)}`}
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  )
}
