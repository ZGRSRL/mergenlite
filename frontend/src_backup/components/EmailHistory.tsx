import { useEffect, useState } from 'react'
import {
    Email as EmailIcon,
    Refresh,
    ExpandMore,
} from '@mui/icons-material'
import {
    Card,
    CardHeader,
    CardContent,
    Typography,
    List,
    ListItem,
    ListItemText,
    Box,
    Chip,
    IconButton,
    CircularProgress,
    Alert,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Stack,
    Divider,
} from '@mui/material'
import { getEmailLogs, EmailLogEntry } from '../api/opportunities'

interface EmailHistoryProps {
    opportunityId: number
}

export function EmailHistory({ opportunityId }: EmailHistoryProps) {
    const [emails, setEmails] = useState<EmailLogEntry[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const loadEmails = async () => {
        try {
            setLoading(true)
            setError(null)
            const data = await getEmailLogs(opportunityId)
            setEmails(data)
        } catch (err) {
            console.error('Failed to load emails:', err)
            setError('Email geçmişi yüklenemedi')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadEmails()
    }, [opportunityId])

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return new Intl.DateTimeFormat('tr-TR', {
            dateStyle: 'medium',
            timeStyle: 'short',
        }).format(date)
    }

    return (
        <Card>
            <CardHeader
                avatar={<EmailIcon color="primary" />}
                title="Gönderilen Mailler"
                subheader={`${emails.length} mail kaydı`}
                action={
                    <IconButton onClick={loadEmails} disabled={loading}>
                        <Refresh />
                    </IconButton>
                }
            />
            <CardContent>
                {loading && (
                    <Box display="flex" justifyContent="center" p={3}>
                        <CircularProgress />
                    </Box>
                )}

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {!loading && emails.length === 0 && (
                    <Alert severity="info">
                        Henüz bu fırsat için gönderilmiş mail bulunmuyor.
                    </Alert>
                )}

                {!loading && emails.length > 0 && (
                    <Stack spacing={2}>
                        {emails.map((email) => (
                            <Accordion key={email.id}>
                                <AccordionSummary expandIcon={<ExpandMore />}>
                                    <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <Chip
                                            label={email.direction === 'outgoing' ? 'Giden' : 'Gelen'}
                                            color={email.direction === 'outgoing' ? 'primary' : 'secondary'}
                                            size="small"
                                        />
                                        <Typography variant="subtitle1" sx={{ flex: 1 }}>
                                            {email.subject || '(Konu yok)'}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            {formatDate(email.created_at)}
                                        </Typography>
                                    </Box>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <Stack spacing={2}>
                                        <Box>
                                            <Typography variant="caption" color="text.secondary">
                                                Gönderen
                                            </Typography>
                                            <Typography variant="body2">{email.from_address}</Typography>
                                        </Box>

                                        <Box>
                                            <Typography variant="caption" color="text.secondary">
                                                Alıcı
                                            </Typography>
                                            <Typography variant="body2">{email.to_address}</Typography>
                                        </Box>

                                        {email.message_id && (
                                            <Box>
                                                <Typography variant="caption" color="text.secondary">
                                                    Message ID
                                                </Typography>
                                                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                                    {email.message_id}
                                                </Typography>
                                            </Box>
                                        )}

                                        <Divider />

                                        {email.parsed_summary && (
                                            <Box>
                                                <Typography variant="caption" color="text.secondary" gutterBottom>
                                                    Özet
                                                </Typography>
                                                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                                    {email.parsed_summary}
                                                </Typography>
                                            </Box>
                                        )}

                                        {email.raw_body && email.raw_body !== email.parsed_summary && (
                                            <Box>
                                                <Typography variant="caption" color="text.secondary" gutterBottom>
                                                    Tam İçerik
                                                </Typography>
                                                <Box
                                                    sx={{
                                                        maxHeight: 300,
                                                        overflow: 'auto',
                                                        bgcolor: 'grey.100',
                                                        p: 2,
                                                        borderRadius: 1,
                                                        fontFamily: 'monospace',
                                                        fontSize: '0.875rem',
                                                        whiteSpace: 'pre-wrap',
                                                    }}
                                                >
                                                    {email.raw_body}
                                                </Box>
                                            </Box>
                                        )}

                                        {email.related_agent_run_id && (
                                            <Chip
                                                label={`Agent Run ID: ${email.related_agent_run_id}`}
                                                size="small"
                                                variant="outlined"
                                            />
                                        )}
                                    </Stack>
                                </AccordionDetails>
                            </Accordion>
                        ))}
                    </Stack>
                )}
            </CardContent>
        </Card>
    )
}
