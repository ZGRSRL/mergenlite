import { useState } from 'react'
import { Container, Box, CssBaseline } from '@mui/material'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { Navigation, type PageType } from './components/Navigation'
import { Dashboard } from './components/Dashboard'
import { OpportunityCenter } from './components/OpportunityCenter'
import { GuidedAnalysis } from './components/GuidedAnalysis'
import { Results } from './components/Results'
import type { Opportunity } from './api/opportunities'

// GitHub tasarımına göre theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#2563eb', // Blue
    },
    secondary: {
      main: '#9333ea', // Purple
    },
    background: {
      default: '#f0f9ff', // Blue-50
    },
  },
  typography: {
    fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
  },
})

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard')
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null)

  const handleAnalyzeOpportunity = (opportunity: Opportunity) => {
    setSelectedOpportunity(opportunity)
    setCurrentPage('analysis')
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard onNavigate={setCurrentPage} />
      case 'opportunities':
        return <OpportunityCenter onAnalyze={handleAnalyzeOpportunity} />
      case 'analysis':
        return (
          <GuidedAnalysis
            opportunity={selectedOpportunity}
            onBack={() => setCurrentPage('opportunities')}
          />
        )
      case 'results':
        return <Results />
      default:
        return <Dashboard onNavigate={setCurrentPage} />
    }
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(to bottom right, #eff6ff, #ffffff, #faf5ff)',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'fixed',
            top: 0,
            right: 0,
            width: '50%',
            height: '50%',
            background: 'radial-gradient(ellipse at top right, rgba(59, 130, 246, 0.4), transparent)',
            pointerEvents: 'none',
            zIndex: 0,
          },
          '&::after': {
            content: '""',
            position: 'fixed',
            bottom: 0,
            left: 0,
            width: '50%',
            height: '50%',
            background: 'radial-gradient(ellipse at bottom left, rgba(16, 185, 129, 0.3), transparent)',
            pointerEvents: 'none',
            zIndex: 0,
          },
        }}
      >
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Container maxWidth="xl" sx={{ py: 3, px: { xs: 2, sm: 3, lg: 4 } }}>
            <Navigation currentPage={currentPage} onNavigate={setCurrentPage} />
            <Box sx={{ mt: 4 }}>{renderPage()}</Box>
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App

