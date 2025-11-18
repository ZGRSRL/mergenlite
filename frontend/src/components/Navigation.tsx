import { Home, Search, AutoAwesome, Description } from '@mui/icons-material'
import { Box, Button, Typography } from '@mui/material'

export type PageType = 'dashboard' | 'opportunities' | 'analysis' | 'results'

interface NavigationProps {
  currentPage: PageType
  onNavigate: (page: PageType) => void
}

const navItems: Array<{ id: PageType; icon: any; label: string }> = [
  { id: 'dashboard', icon: Home, label: 'Dashboard' },
  { id: 'opportunities', icon: Search, label: 'Fırsat Arama' },
  { id: 'analysis', icon: AutoAwesome, label: 'AI Analiz' },
  { id: 'results', icon: Description, label: 'Sonuçlar' },
]

export function Navigation({ currentPage, onNavigate }: NavigationProps) {
  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          sx={{
            background: 'linear-gradient(to right, #2563eb, #9333ea)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            mb: 1,
            fontWeight: 600,
          }}
        >
          MergenLite
        </Typography>
        <Typography variant="body2" color="text.secondary">
          SAM.gov Otomatik Teklif Analiz Platformu
        </Typography>
      </Box>

      {/* Navigation Tabs */}
      <Box
        sx={{
          bgcolor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(226, 232, 240, 1)',
          borderRadius: '16px',
          p: 1.5,
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}
      >
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1.5 }}>
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentPage === item.id

            return (
              <Button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                startIcon={<Icon />}
                sx={{
                  borderRadius: '12px',
                  px: 3,
                  py: 1.5,
                  fontWeight: 500,
                  transition: 'all 0.3s',
                  ...(isActive
                    ? {
                        background: 'linear-gradient(to right, #2563eb, #3b82f6)',
                        color: 'white',
                        boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.3)',
                        transform: 'scale(1.05)',
                        '&:hover': {
                          background: 'linear-gradient(to right, #1d4ed8, #2563eb)',
                        },
                      }
                    : {
                        color: '#475569',
                        '&:hover': {
                          color: '#2563eb',
                          bgcolor: 'rgba(239, 246, 255, 1)',
                        },
                      }),
                }}
              >
                {item.label}
              </Button>
            )
          })}
        </Box>
      </Box>
    </Box>
  )
}

