# 🖥️ ZgrBid Frontend - Modern UI Implementation

## 🎨 Frontend Yapısı

### 📁 Bileşen Mimarisi

```
web/src/
├── app/
│   ├── layout.tsx          # Ana layout + NavigationBar
│   ├── page.tsx            # Dashboard (3 sekme: Upload, Compliance, Proposal)
│   ├── globals.css         # Tailwind + shadcn/ui tema
│   └── api.ts              # Backend API client
├── components/
│   ├── ui/                 # shadcn/ui bileşenleri
│   │   ├── card.tsx        # Card, CardHeader, CardContent
│   │   ├── tabs.tsx        # Tabs, TabsList, TabsTrigger, TabsContent
│   │   └── badge.tsx       # Badge (success, warning, danger variants)
│   ├── UploadPanel.tsx     # Drag & drop dosya yükleme
│   ├── ComplianceTable.tsx # Uyumluluk matrisi tablosu
│   ├── DraftViewer.tsx     # Teklif taslağı görüntüleyici
│   └── RiskBadges.tsx      # Risk göstergeleri
└── lib/
    └── utils.ts            # cn() utility (clsx + tailwind-merge)
```

## 🚀 Özellikler

### 1. 📁 Upload Panel
- **Drag & Drop**: Dosyaları sürükleyip bırakma
- **Dosya Türü Algılama**: RFQ, SOW, Facility, Past Performance, Pricing
- **Görsel İkonlar**: PDF, Excel, resim dosyaları için özel ikonlar
- **Dosya Listesi**: Yüklenen dosyaların detaylı görünümü
- **Card Tasarım**: Modern shadcn/ui Card bileşeni

### 2. 📊 Compliance Table
- **Filtreleme**: Kategoriye göre gereksinim filtreleme
- **Risk Badges**: LOW/MEDIUM/HIGH/CRITICAL risk seviyeleri
- **Genişletilebilir Satırlar**: Detaylı kanıt görüntüleme
- **Responsive Tasarım**: Mobil uyumlu tablo
- **Status İkonları**: CheckCircle, AlertTriangle, XCircle

### 3. 📝 Draft Viewer
- **Sekmeli Görünüm**: Executive, Technical, Performance, Pricing
- **Preview/Edit Modu**: Markdown render + düzenleme
- **Download Butonları**: DOCX/PDF indirme
- **Compliance Matrix**: Ayrı kart olarak görüntüleme

### 4. 🎯 Risk Badges
- **4 Kart Layout**: Total, Met, Gap, Overall Risk
- **Yüzde Gösterimi**: Compliance oranları
- **Renk Kodlaması**: Yeşil (başarı), sarı (uyarı), kırmızı (risk)
- **İkonlar**: TrendingUp/Down, CheckCircle, XCircle

## 🎨 Tasarım Sistemi

### Renk Paleti
```css
--primary: 221.2 83.2% 53.3%     # Mavi
--success: green-100/green-800    # Yeşil
--warning: yellow-100/yellow-800  # Sarı
--danger: red-100/red-800         # Kırmızı
--muted: 210 40% 96%              # Gri
```

### Bileşen Varyantları
- **Badge**: default, secondary, success, warning, danger, outline
- **Card**: Temiz, gölgeli kartlar
- **Tabs**: Responsive sekme sistemi

## 🔧 Teknoloji Stack

### Core
- **Next.js 14**: App Router, Server Components
- **React 18**: Hooks, State Management
- **TypeScript**: Type Safety

### UI Framework
- **Tailwind CSS**: Utility-first CSS
- **shadcn/ui**: Radix UI + Tailwind bileşenleri
- **Lucide React**: Modern ikonlar
- **Framer Motion**: Animasyonlar (gelecekte)

### Styling
- **CSS Variables**: Tema sistemi
- **Dark Mode**: Otomatik tema desteği
- **Responsive**: Mobile-first tasarım

## 📱 Responsive Tasarım

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Grid Layout
- **Risk Badges**: 1 col (mobile) → 2 col (tablet) → 4 col (desktop)
- **Compliance Table**: Horizontal scroll (mobile)
- **Tabs**: Responsive tab listesi

## 🚀 Kullanım

### Geliştirme
```bash
cd web
npm install
npm run dev
```

### Build
```bash
npm run build
npm start
```

### Linting
```bash
npm run lint
```

## 🔗 API Entegrasyonu

### Endpoints
- `GET /health` - Sistem durumu
- `POST /ingest/process-local` - Dosya işleme
- `GET /compliance/matrix/{rfq_id}` - Uyumluluk matrisi
- `POST /proposal/generate/{rfq_id}` - Teklif oluşturma
- `GET /proposal/download/{rfq_id}` - Dosya indirme

### Error Handling
- Try-catch blokları
- Loading states
- Error messages
- Graceful fallbacks

## 🎯 Gelecek Özellikler

### Phase 2
- [ ] Framer Motion animasyonları
- [ ] Dark mode toggle
- [ ] Real-time updates
- [ ] Advanced filtering

### Phase 3
- [ ] Drag & drop reordering
- [ ] Bulk operations
- [ ] Export options
- [ ] User preferences

## 📊 Performans

### Optimizasyonlar
- **Code Splitting**: Next.js otomatik
- **Image Optimization**: Next.js Image
- **Bundle Analysis**: Webpack Bundle Analyzer
- **Lazy Loading**: React.lazy()

### Metrikler
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **Time to Interactive**: < 3.5s

## 🧪 Test Stratejisi

### Unit Tests
- Component testing (Jest + React Testing Library)
- Utility function testing
- API client testing

### Integration Tests
- User flow testing
- API integration testing
- Error scenario testing

### E2E Tests
- Playwright/Cypress
- Critical user journeys
- Cross-browser testing

## 📝 Notlar

- Tüm bileşenler TypeScript ile yazıldı
- shadcn/ui best practices takip edildi
- Accessibility (a11y) standartları uygulandı
- Mobile-first responsive tasarım
- Modern React patterns (hooks, context)

---

**Frontend hazır! 🎉** Backend ile entegrasyon için API endpoints'lerin çalışır durumda olması gerekiyor.



