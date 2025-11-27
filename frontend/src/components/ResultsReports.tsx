import { useEffect, useState } from "react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  FileText,
  Download,
  FileJson,
  Calendar,
  CheckCircle2,
  Loader2
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import api from "../api/client";

interface AnalysisResult {
  id: number;
  status: string;
  result_json: any;
  created_at: string;
  completed_at: string;
  opportunity: {
    notice_id: string;
    title: string;
  };
  confidence?: number;
}

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
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResult[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await api.get("/pipeline/results?limit=50");
        setAnalysisHistory(response.data);
        if (response.data.length > 0) {
          setSelectedAnalysis(response.data[0]);
        }
      } catch (err) {
        console.error("Error fetching analysis history:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  const resultData = selectedAnalysis?.result_json || {};
  const requirements = resultData.requirements || [];
  const complianceMatrix = resultData.compliance_matrix || [];
  const proposalText = resultData.proposal_text || "";

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
                <TableHead className="text-slate-400">Skor</TableHead>
                <TableHead className="text-slate-400">Durum</TableHead>
                <TableHead className="text-slate-400">Aksiyonlar</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analysisHistory.map((analysis) => (
                <TableRow
                  key={analysis.id}
                  className={`border-slate-800 hover:bg-slate-800/50 cursor-pointer ${selectedAnalysis?.id === analysis.id ? "bg-slate-800/50" : ""}`}
                  onClick={() => setSelectedAnalysis(analysis)}
                >
                  <TableCell className="text-blue-400">#{analysis.id}</TableCell>
                  <TableCell className="text-slate-300">{analysis.opportunity?.notice_id || "-"}</TableCell>
                  <TableCell className="text-slate-300 max-w-xs truncate">{analysis.opportunity?.title || "-"}</TableCell>
                  <TableCell className="text-slate-400">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(analysis.created_at).toLocaleDateString()}
                    </div>
                  </TableCell>
                  <TableCell>
                    {getScoreBadge(analysis.confidence ? analysis.confidence * 100 : 0)}
                  </TableCell>
                  <TableCell>
                    <Badge className="bg-emerald-500/20 text-emerald-400">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      {analysis.status}
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
                <p className="text-slate-400">{selectedAnalysis.opportunity?.notice_id} - {selectedAnalysis.opportunity?.title}</p>
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
              {requirements.length > 0 ? (
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
                    {requirements.map((req: any, index: number) => (
                      <TableRow key={index} className="border-slate-800 hover:bg-slate-800/50">
                        <TableCell className="text-blue-400">{req.category}</TableCell>
                        <TableCell className="text-slate-300">{req.requirement || req.text}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={
                            req.priority === "Yüksek" || req.priority === "High" ? "border-red-500/50 text-red-400" :
                              req.priority === "Orta" || req.priority === "Medium" ? "border-yellow-500/50 text-yellow-400" :
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
                            {req.status || "Analiz Ediliyor"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  Veri bulunamadı.
                </div>
              )}
            </TabsContent>

            <TabsContent value="compliance" className="p-6">
              {complianceMatrix.length > 0 ? (
                <div className="space-y-4">
                  {complianceMatrix.map((item: any, index: number) => (
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
              ) : (
                <div className="text-center py-8 text-slate-400">
                  Veri bulunamadı.
                </div>
              )}
            </TabsContent>

            <TabsContent value="proposal" className="p-6">
              <div className="prose prose-invert max-w-none">
                <div className="text-slate-300 whitespace-pre-wrap">
                  {proposalText || "Teklif taslağı bulunamadı."}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </Card>
      )}
    </div>
  );
}
