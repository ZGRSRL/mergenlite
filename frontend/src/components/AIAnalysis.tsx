import { useEffect, useState } from "react";
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
  Clock,
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
import { Opportunity } from "../api/opportunities";
import api from "../api/client";
import EmailHistory from "./EmailHistory";

interface AIAnalysisProps {
  opportunity: Opportunity | null;
}

interface AnalysisResult {
  id: number;
  status: string;
  result_json: any;
  created_at: string;
  completed_at: string;
}

const processSteps = [
  {
    name: "Document Processor",
    key: "doc_processor",
    icon: FileText,
    description: "Doküman işleme"
  },
  {
    name: "Requirements Extractor",
    key: "req_extractor",
    icon: FileSearch,
    description: "Gereksinim analizi"
  },
  {
    name: "Compliance Analyst",
    key: "compliance",
    icon: Shield,
    description: "Uyumluluk kontrolü"
  },
  {
    name: "Proposal Writer",
    key: "proposal",
    icon: PenTool,
    description: "Teklif yazımı"
  }
];

export default function AIAnalysis({ opportunity }: AIAnalysisProps) {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!opportunity) return;

      try {
        setLoading(true);
        // Fetch the latest analysis result for this opportunity
        const response = await api.get(`/pipeline/opportunity/${opportunity.id}/results?limit=1`);
        if (response.data && response.data.length > 0) {
          setAnalysisResult(response.data[0]);
        } else {
          setAnalysisResult(null);
        }
        setError(null);
      } catch (err) {
        console.error("Error fetching analysis:", err);
        setError("Analiz verileri alınamadı.");
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [opportunity]);

  if (!opportunity) {
    return (
      <Card className="bg-slate-900/50 border-slate-800 p-8 text-center backdrop-blur-sm">
        <div className="flex flex-col items-center gap-4">
          <div className="p-4 rounded-full bg-slate-800">
            <FileSearch className="w-8 h-8 text-slate-400" />
          </div>
          <div>
            <h3 className="text-white text-lg font-medium mb-2">Analiz İçin Fırsat Seçin</h3>
            <p className="text-slate-400 max-w-md mx-auto">
              Detaylı AI analizi başlatmak için lütfen "Fırsat Arama" sekmesinden bir fırsat seçin ve "Analizi Başlat" butonuna tıklayın.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <p className="text-slate-400">Analiz verileri yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg">
        {error}
      </div>
    );
  }

  // If no analysis exists yet, show a "Start Analysis" prompt or empty state
  // But usually we come here after clicking "Start Analysis" which triggers a backend job.
  // For now, if no result, we can show a message or just the header.

  const resultData = analysisResult?.result_json || {};
  const requirements = resultData.requirements || [];
  const complianceMatrix = resultData.compliance_matrix || [];
  const proposalText = resultData.proposal_text || "";

  // Determine step status based on analysis status/progress
  // This is a simplification. Ideally backend provides step-by-step progress.
  const isCompleted = analysisResult?.status === "completed";
  const currentStepIndex = isCompleted ? 4 : 1; // Mock progress if not completed

  const progress = (currentStepIndex / processSteps.length) * 100;

  return (
    <div className="space-y-6">
      {/* Analysis Header */}
      <Card className="bg-gradient-to-br from-slate-900/50 to-slate-800/50 border-slate-800 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-white mb-1">Aktif Analiz</h3>
            <p className="text-slate-400">{opportunity.noticeId} - {opportunity.title}</p>
          </div>
          <Badge className={`${isCompleted ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/50" : "bg-blue-500/20 text-blue-400 border-blue-500/50"
            }`}>
            {isCompleted ? <CheckCircle2 className="w-3 h-3 mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
            {isCompleted ? "Tamamlandı" : "Analiz Ediliyor..."}
          </Badge>
        </div>
        <Progress value={progress} className="h-2" />
        <p className="text-slate-400 text-sm mt-2">
          {isCompleted ? "Tüm aşamalar tamamlandı" : "Analiz devam ediyor..."}
        </p>
      </Card>

      {/* Process Flow */}
      <Card className="bg-slate-900/50 border-slate-800 p-6 backdrop-blur-sm">
        <h3 className="text-white mb-4">Analiz Akışı</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {processSteps.map((step, index) => {
            const Icon = step.icon;
            // Simplified logic for step status
            let status = "pending";
            if (index < currentStepIndex) status = "completed";
            else if (index === currentStepIndex && !isCompleted) status = "in-progress";

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
                <Card className={`${statusColors[status as keyof typeof statusColors]} border-2 p-4 transition-all`}>
                  <div className="flex flex-col items-center text-center">
                    <div className="mb-3">
                      <Icon className={`w-8 h-8 ${iconColors[status as keyof typeof iconColors]}`} />
                    </div>
                    <p className="text-white text-sm mb-2">{step.name}</p>
                    <p className="text-slate-400 text-xs">{step.description}</p>
                    {status === "completed" && (
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
          <TabsList className="w-full justify-start rounded-none border-b border-slate-800 bg-transparent p-0 overflow-x-auto">
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
            <TabsTrigger
              value="emails"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:bg-transparent"
            >
              İletişim Geçmişi
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
                Henüz gereksinim analizi tamamlanmadı veya veri bulunamadı.
              </div>
            )}
          </TabsContent>

          <TabsContent value="compliance" className="p-6">
            {complianceMatrix.length > 0 ? (
              <div className="space-y-4">
                {complianceMatrix.map((item: any, index: number) => (
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
            ) : (
              <div className="text-center py-8 text-slate-400">
                Uyumluluk matrisi henüz oluşturulmadı.
              </div>
            )}
          </TabsContent>

          <TabsContent value="proposal" className="p-6">
            <div className="prose prose-invert max-w-none">
              {proposalText ? (
                <div className="text-slate-300 whitespace-pre-wrap">
                  {proposalText}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  Teklif taslağı henüz oluşturulmadı.
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="emails" className="p-6">
            <EmailHistory opportunityId={opportunity.id} />
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}

