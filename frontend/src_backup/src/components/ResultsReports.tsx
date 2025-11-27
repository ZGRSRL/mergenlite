import { useState } from "react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { 
  FileText, 
  Download, 
  FileJson,
  Calendar,
  Clock,
  CheckCircle2
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

const analysisHistory = [
  {
    id: "AN-2025-001",
    noticeId: "SAM-721110-2025-001",
    title: "Hotel Accommodation Services - Washington DC",
    date: "2025-11-07 14:30",
    duration: "25sn",
    status: "completed",
    overallScore: 92
  },
  {
    id: "AN-2025-002",
    noticeId: "SAM-721110-2025-002",
    title: "Extended Stay Housing for Military Personnel",
    date: "2025-11-06 16:45",
    duration: "28sn",
    status: "completed",
    overallScore: 85
  },
  {
    id: "AN-2025-003",
    noticeId: "SAM-721110-2025-003",
    title: "Emergency Housing Services - Natural Disaster Response",
    date: "2025-11-06 11:20",
    duration: "31sn",
    status: "completed",
    overallScore: 78
  },
  {
    id: "AN-2025-004",
    noticeId: "SAM-721110-2025-004",
    title: "Conference Center & Lodging - Federal Training",
    date: "2025-11-05 09:15",
    duration: "24sn",
    status: "completed",
    overallScore: 94
  },
  {
    id: "AN-2025-005",
    noticeId: "SAM-721110-2025-005",
    title: "Temporary Housing for Federal Employees",
    date: "2025-11-04 13:50",
    duration: "27sn",
    status: "completed",
    overallScore: 88
  }
];

const requirements = [
  { category: "Teknik", requirement: "NAICS 721110 sertifikasyonu", priority: "Yüksek", status: "Karşılanıyor" },
  { category: "Mali", requirement: "Son 3 yıl gelir beyanı", priority: "Yüksek", status: "Karşılanıyor" },
  { category: "Deneyim", requirement: "Benzer projelerde 5 yıl deneyim", priority: "Orta", status: "Karşılanıyor" }
];

const complianceMatrix = [
  { area: "Teknik Uyumluluk", score: 95, status: "Düşük Risk" },
  { area: "Mali Uyumluluk", score: 88, status: "Düşük Risk" },
  { area: "Yasal Uyumluluk", score: 72, status: "Orta Risk" }
];

const getScoreBadge = (score: number) => {
  if (score >= 90) {
    return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50">Mükemmel</Badge>;
  } else if (score >= 80) {
    return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">İyi</Badge>;
  } else if (score >= 70) {
    return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/50">Orta</Badge>;
  }
  return <Badge className="bg-red-500/20 text-red-400 border-red-500/50">Zayıf</Badge>;
};

export default function ResultsReports() {
  const [selectedAnalysis, setSelectedAnalysis] = useState(analysisHistory[0]);

  return (
    <div className="space-y-6">
      {/* Analysis History */}
      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
        <div className="p-6 border-b border-slate-800">
          <h3 className="text-white">Analiz Geçmişi</h3>
        </div>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-slate-800 hover:bg-slate-800/50">
                <TableHead className="text-slate-400">Analiz ID</TableHead>
                <TableHead className="text-slate-400">Notice ID</TableHead>
                <TableHead className="text-slate-400">Başlık</TableHead>
                <TableHead className="text-slate-400">Tarih</TableHead>
                <TableHead className="text-slate-400">Süre</TableHead>
                <TableHead className="text-slate-400">Skor</TableHead>
                <TableHead className="text-slate-400">Durum</TableHead>
                <TableHead className="text-slate-400">Aksiyonlar</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analysisHistory.map((analysis, index) => (
                <TableRow 
                  key={index} 
                  className="border-slate-800 hover:bg-slate-800/50 cursor-pointer"
                  onClick={() => setSelectedAnalysis(analysis)}
                >
                  <TableCell className="text-blue-400">{analysis.id}</TableCell>
                  <TableCell className="text-slate-300">{analysis.noticeId}</TableCell>
                  <TableCell className="text-slate-300 max-w-xs truncate">{analysis.title}</TableCell>
                  <TableCell className="text-slate-400">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {analysis.date}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-400">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {analysis.duration}
                    </div>
                  </TableCell>
                  <TableCell>
                    {getScoreBadge(analysis.overallScore)}
                  </TableCell>
                  <TableCell>
                    <Badge className="bg-emerald-500/20 text-emerald-400">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      Tamamlandı
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
                        <FileText className="w-3 h-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </Card>

      {/* Selected Analysis Detail */}
      {selectedAnalysis && (
        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
          <div className="p-6 border-b border-slate-800">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-white mb-1">Detaylı Görünüm</h3>
                <p className="text-slate-400">{selectedAnalysis.noticeId} - {selectedAnalysis.title}</p>
              </div>
              <div className="flex gap-2">
                <Button className="bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 text-white">
                  <Download className="w-4 h-4 mr-2" />
                  PDF İndir
                </Button>
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
                  <FileJson className="w-4 h-4 mr-2" />
                  JSON Export
                </Button>
              </div>
            </div>
          </div>

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
                        <Badge className="bg-emerald-500/20 text-emerald-400">
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
                    <div className="flex items-center justify-between mb-2">
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
                      Bu teklif, SAM.gov ihalesi {selectedAnalysis.noticeId} kapsamında hazırlanmıştır. 
                      Firmamız, deneyimimiz ve sertifikalı personelimizle bu projeyi başarıyla yürütmeye hazırız.
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="text-white mb-2">Teknik Yaklaşım</h4>
                    <p className="text-sm">
                      Projede, NAICS 721110 standartlarına tam uyumlu çözümler sunacağız. 
                      24/7 operasyonel destek ve Washington DC merkezli koordinasyon ofisimiz ile kesintisiz hizmet sağlayacağız.
                    </p>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </Card>
      )}
    </div>
  );
}
