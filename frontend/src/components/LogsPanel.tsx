import { Card, CardContent, Typography, Box, Paper } from '@mui/material'
import { Terminal } from '@mui/icons-material'

interface LogsPanelProps {
  logs: string[]
}

export function LogsPanel({ logs }: LogsPanelProps) {
  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <Terminal />
          <Typography variant="h6">Pipeline Logs</Typography>
        </Box>
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            maxHeight: 400,
            overflow: 'auto',
            bgcolor: '#1e1e1e',
            color: '#d4d4d4',
            fontFamily: 'monospace',
            fontSize: '0.875rem',
          }}
        >
          {logs.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No logs yet. Run a pipeline to see activity.
            </Typography>
          ) : (
            logs.map((log, index) => (
              <Box key={index} sx={{ mb: 0.5 }}>
                {log}
              </Box>
            ))
          )}
        </Paper>
      </CardContent>
    </Card>
  )
}

