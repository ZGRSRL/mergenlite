import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { 
  FileText, 
  FileSearch, 
  Shield, 
  PenTool,
  CheckCircle2,
  Clock
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

const processSteps = [
  { 
    name: "Document Processor", 
    status: "completed", 
    icon: FileText,
    description: "Doküman işleme tamamlandı"
  },
  { 
    name: "Requirements Extractor", 
    status: "completed", 
    icon: FileSearch,
    description: "Gereksinimler çıkarıldı"
  },
  { 
    name: "Compliance Analyst", 
    status: "in-progress", 
    icon: Shield,
    description: "Uyumluluk analizi devam ediyor"
  },
  { 
    name: "Proposal Writer", 
    status: "pending", 
    icon: PenTool,
    description: "Teklif taslağı bekleniyor"
  }
];

const requirements = [
  { category: "Teknik", requirement: "NAICS 721110 sertifikasyonu", priority: "Yüksek", status: "Karşılanıyor" },
  { category: "Mali", requirement: "Son 3 yıl gelir beyanı", priority: "Yüksek", status: "Karşılanıyor" },
  { category: "Deneyim", requirement: "Benzer projelerde 5 yıl deneyim", priority: "Orta", status: "Karşılanıyor" },
  { category: "Personel", requirement: "Minimum 20 sertifikalı personel", priority: "Orta", status: "İnceleniyor" },
  { category: "Lokasyon", requirement: "Washington DC bölgesinde ofis", priority: "Düşük", status: "Karşılanıyor" }
];

const complianceMatrix = [
  { area: "Teknik Uyumluluk", score: 95, status: "Düşük Risk", actions: "Tüm teknik gereksinimler karşılanıyor" },
  { area: "Mali Uyumluluk", score: 88, status: "Düşük Risk", actions: "Mali belgeler hazır" },
  { area: "Yasal Uyumluluk", score: 72, status: "Orta Risk", actions: "İki ek belge gerekli" },
  { area: "Personel Yeterliliği", score: 65, status: "Orta Risk", actions: "3 ek sertifikalı personel alınmalı" },
  { area: "Lojistik Kapasite", score: 90, status: "Düşük Risk", actions: "Kapasite yeterli" }
];

export default function AIAnalysis() {
  const completedSteps = processSteps.filter(s => s.status === "completed").length;
  const progress = (completedSteps / processSteps.length) * 100;

  return (
    <div className="space-y-6">
      {/* Analysis Header */}
      <Card className="bg-gradient-to-br from-slate-900/50 to-slate-800/50 border-slate-800 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-white mb-1">Aktif Analiz</h3>
            <p className="text-slate-400">SAM-721110-2025-003 - Emergency Housing Services</p>
          </div>
          <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">
            <Clock className="w-3 h-3 mr-1" />
            18 saniye
          </Badge>
        </div>
        <Progress value={progress} className="h-2" />
        <p className="text-slate-400 text-sm mt-2">
          {completedSteps} / {processSteps.length} aşama tamamlandı
        </p>
      </Card>

      {/* Process Flow */}
      <Card className="bg-slate-900/50 border-slate-800 p-6 backdrop-blur-sm">
        <h3 className="text-white mb-4">Analiz Akışı</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {processSteps.map((step, index) => {
            const Icon = step.icon;
            const statusColors = {
              completed: "bg-emerald-500/20 border-emerald-500",
              "in-progress": "bg-blue-500/20 border-blue-500 animate-pulse",
              pending: "bg-slate-500/20 border-slate-600"
            };
            const iconColors = {
              completed: "text-emerald-400",
              "in-progress": "text-blue-400",
              pending: "text-slate-400"
            };
            
            return (
              <div key={index} className="relative">
                <Card className={`${statusColors[step.status as keyof typeof statusColors]} border-2 p-4 transition-all`}>
                  <div className="flex flex-col items-center text-center">
                    <div className="mb-3">
                      <Icon className={`w-8 h-8 ${iconColors[step.status as keyof typeof iconColors]}`} />
                    </div>
                    <p className="text-white text-sm mb-2">{step.name}</p>
                    <p className="text-slate-400 text-xs">{step.description}</p>
                    {step.status === "completed" && (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 mt-2" />
                    )}
                  </div>
                </Card>
                {index < processSteps.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-2 w-4 h-0.5 bg-slate-700" />
                )}
              </div>
            );
          })}
        </div>
      </Card>

      {/* Analysis Results Tabs */}
      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
        <Tabs defaultValue="requirements" className="w-full">
          <TabsList className="w-full justify-start rounded-none border-b border-slate-800 bg-transparent p-0">
            <TabsTrigger 
              value="requirements"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:bg-transparent"
            >
              Gereksinimler Özeti
            </TabsTrigger>
            <TabsTrigger 
              value="compliance"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:bg-transparent"
            >
              Compliance Matrisi
            </TabsTrigger>
            <TabsTrigger 
              value="proposal"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:bg-transparent"
            >
              Teklif Taslağı
            </TabsTrigger>
          </TabsList>

          <TabsContent value="requirements" className="p-6">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-800 hover:bg-slate-800/50">
                  <TableHead className="text-slate-400">Kategori</TableHead>
                  <TableHead className="text-slate-400">Gereksinim</TableHead>
                  <TableHead className="text-slate-400">Öncelik</TableHead>
                  <TableHead className="text-slate-400">Durum</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requirements.map((req, index) => (
                  <TableRow key={index} className="border-slate-800 hover:bg-slate-800/50">
                    <TableCell className="text-blue-400">{req.category}</TableCell>
                    <TableCell className="text-slate-300">{req.requirement}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={
                        req.priority === "Yüksek" ? "border-red-500/50 text-red-400" :
                        req.priority === "Orta" ? "border-yellow-500/50 text-yellow-400" :
                        "border-slate-500/50 text-slate-400"
                      }>
                        {req.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={
                        req.status === "Karşılanıyor" ? "bg-emerald-500/20 text-emerald-400" :
                        "bg-yellow-500/20 text-yellow-400"
                      }>
                        {req.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>

          <TabsContent value="compliance" className="p-6">
            <div className="space-y-4">
              {complianceMatrix.map((item, index) => (
                <Card key={index} className="bg-slate-800/50 border-slate-700 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white">{item.area}</h4>
                    <div className="flex items-center gap-3">
                      <span className="text-white">{item.score}/100</span>
                      <Badge className={
                        item.status === "Düşük Risk" ? "bg-emerald-500/20 text-emerald-400" :
                        "bg-yellow-500/20 text-yellow-400"
                      }>
                        {item.status}
                      </Badge>
                    </div>
                  </div>
                  <Progress value={item.score} className="h-2 mb-2" />
                  <p className="text-slate-400 text-sm">{item.actions}</p>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="proposal" className="p-6">
            <div className="prose prose-invert max-w-none">
              <div className="text-slate-300 space-y-4">
                <div>
                  <h4 className="text-white mb-2">Yönetici Özeti</h4>
                  <p className="text-sm">
                    Bu teklif, SAM.gov ihalesi SAM-721110-2025-003 kapsamında Emergency Housing Services projesi için hazırlanmıştır. 
                    Firmamız, 8 yıllık deneyimimiz ve 25 sertifikalı personelimizle bu projeyi başarıyla yürütmeye hazırız.
                  </p>
                </div>
                
                <div>
                  <h4 className="text-white mb-2">Teknik Yaklaşım</h4>
                  <p className="text-sm">
                    Projede, NAICS 721110 standartlarına tam uyumlu, afet bölgelerinde hızlı konaklama çözümleri sunacağız. 
                    24/7 operasyonel destek ve Washington DC merkezli koordinasyon ofisimiz ile kesintisiz hizmet sağlayacağız.
                  </p>
                </div>
                
                <div>
                  <h4 className="text-white mb-2">Personel ve Kaynaklar</h4>
                  <p className="text-sm">
                    20 sertifikalı personelimiz ve 5 yıllık benzer proje deneyimimiz ile tüm gereksinimleri karşılıyoruz. 
                    Ek 3 personel alımı planlanmaktadır.
                  </p>
                </div>
                
                <div>
                  <h4 className="text-white mb-2">Maliyet Analizi</h4>
                  <p className="text-sm">
                    Toplam proje maliyeti: $2,450,000 (üç yıllık süre için). 
                    Mali belgelerimiz ve son 3 yıllık gelir beyanlarımız eklenmiştir.
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
