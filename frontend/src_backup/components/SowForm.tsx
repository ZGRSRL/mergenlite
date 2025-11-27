import { Card, CardContent, Typography, Alert } from '@mui/material'

export function SowForm() {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          SOW Generator (Coming Soon)
        </Typography>
        <Alert severity="info">
          Manuel PDF yükleyerek SOW pipeline’ýný çalýþtýrma özelliði henüz tamamlanmadý. Guided Analysis üzerinden
          pipeline tetiklendiðinde sonuçlar otomatik olarak burada listelenecek.
        </Alert>
      </CardContent>
    </Card>
  )
}
