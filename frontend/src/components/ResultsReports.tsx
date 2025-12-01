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
  Loader2,
  Search,
  Filter
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
    return <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20">Excellent</Badge>;
  } else if (score >= 80) {
    return <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20">Good</Badge>;
  } else if (score >= 70) {
    return <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20">Average</Badge>;
  }
  return <Badge className="bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20">Weak</Badge>;
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
      <div className="flex flex-col items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-4" />
        <p className="text-slate-400 animate-pulse">Loading reports...</p>
      </div>
    );
  }

  const resultData = selectedAnalysis?.result_json || {};
  const requirements = resultData.requirements || [];
  const complianceMatrix = resultData.compliance_matrix || [];
  const proposalText = resultData.proposal_text || "";

  return (
    <div className="space-y-6 pb-12">
      {/* Analysis History */}
      <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-sm shadow-lg overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Analysis History</h3>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="h-8 text-xs border-slate-700 text-slate-400 hover:text-slate-200 hover:bg-slate-800">
              <Filter className="w-3.5 h-3.5 mr-1.5" /> Filter
            </Button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-slate-800 bg-slate-950/20 hover:bg-slate-950/30">
                <TableHead className="text-slate-400 font-medium pl-6">Analysis ID</TableHead>
                <TableHead className="text-slate-400 font-medium">Notice ID</TableHead>
                <TableHead className="text-slate-400 font-medium">Title</TableHead>
                <TableHead className="text-slate-400 font-medium">Date</TableHead>
                <TableHead className="text-slate-400 font-medium">Score</TableHead>
                <TableHead className="text-slate-400 font-medium">Status</TableHead>
                <TableHead className="text-slate-400 font-medium text-right pr-6">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analysisHistory.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                    No analysis results found.
                  </TableCell>
                </TableRow>
              ) : (
                analysisHistory.map((analysis) => (
                  <TableRow
                    key={analysis.id}
                    className={`border-slate-800 hover:bg-slate-800/30 cursor-pointer transition-colors ${selectedAnalysis?.id === analysis.id ? "bg-blue-500/5 border-l-2 border-l-blue-500" : "border-l-2 border-l-transparent"}`}
                    onClick={() => setSelectedAnalysis(analysis)}
                  >
                    <TableCell className="text-blue-400 font-mono text-xs pl-6">#{analysis.id}</TableCell>
                    <TableCell className="text-slate-300 font-medium text-xs">{analysis.opportunity?.notice_id || "-"}</TableCell>
                    <TableCell className="text-slate-400 max-w-xs truncate text-xs">{analysis.opportunity?.title || "-"}</TableCell>
                    <TableCell className="text-slate-500 text-xs">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3 h-3" />
                        {analysis.created_at ? new Date(analysis.created_at).toLocaleDateString() : "-"}
                      </div>
                    </TableCell>
                    <TableCell>
                      {getScoreBadge(analysis.confidence ? analysis.confidence * 100 : 0)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-emerald-500/5 text-emerald-400 border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3 mr-1.5" />
                        {analysis.status || "Completed"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right pr-6">
                      <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-full">
                        <FileText className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Card>

      {/* Selected Analysis Detail */}
      {selectedAnalysis && (
        <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-sm shadow-lg overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="p-6 border-b border-slate-800 bg-slate-950/30">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className="bg-slate-900 text-slate-500 border-slate-700 text-[10px]">DETAIL</Badge>
                  <span className="text-slate-500 text-xs">#{selectedAnalysis.id}</span>
                </div>
                <h3 className="text-xl font-semibold text-white">{selectedAnalysis.opportunity?.title}</h3>
                <p className="text-slate-400 text-sm mt-1 font-mono">{selectedAnalysis.opportunity?.notice_id}</p>
              </div>
              <div className="flex gap-3">
                <Button className="bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white shadow-lg shadow-red-500/20 border-0">
                  <Download className="w-4 h-4 mr-2" />
                  Download PDF
                </Button>
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white">
                  <FileJson className="w-4 h-4 mr-2" />
                  JSON Export
                </Button>
              </div>
            </div>
          </div>

          <Tabs defaultValue="requirements" className="w-full">
            <div className="border-b border-slate-800 px-2 bg-slate-950/20">
              <TabsList className="w-full justify-start bg-transparent p-0 h-12 gap-6">
                <TabsTrigger
                  value="requirements"
                  className="rounded-none border-b-2 border-transparent px-4 h-12 data-[state=active]:border-blue-500 data-[state=active]:text-blue-400 data-[state=active]:bg-transparent text-slate-400 hover:text-slate-200 transition-colors"
                >
                  Requirements Summary
                </TabsTrigger>
                <TabsTrigger
                  value="compliance"
                  className="rounded-none border-b-2 border-transparent px-4 h-12 data-[state=active]:border-blue-500 data-[state=active]:text-blue-400 data-[state=active]:bg-transparent text-slate-400 hover:text-slate-200 transition-colors"
                >
                  Compliance Matrix
                </TabsTrigger>
                <TabsTrigger
                  value="proposal"
                  className="rounded-none border-b-2 border-transparent px-4 h-12 data-[state=active]:border-blue-500 data-[state=active]:text-blue-400 data-[state=active]:bg-transparent text-slate-400 hover:text-slate-200 transition-colors"
                >
                  Draft Proposal
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="requirements" className="p-0">
              {requirements.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-800 bg-slate-950/20 hover:bg-slate-950/30">
                      <TableHead className="text-slate-400 font-medium pl-6">Category</TableHead>
                      <TableHead className="text-slate-400 font-medium">Requirement</TableHead>
                      <TableHead className="text-slate-400 font-medium">Priority</TableHead>
                      <TableHead className="text-slate-400 font-medium">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {requirements.map((req: any, index: number) => (
                      <TableRow key={index} className="border-slate-800 hover:bg-slate-800/30 transition-colors">
                        <TableCell className="text-blue-400 font-medium pl-6">{req.category}</TableCell>
                        <TableCell className="text-slate-300">{req.requirement || req.text}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={
                            req.priority === "Yüksek" || req.priority === "High" ? "bg-red-500/10 border-red-500/20 text-red-400" :
                              req.priority === "Orta" || req.priority === "Medium" ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                                "bg-slate-500/10 border-slate-500/20 text-slate-400"
                          }>
                            {req.priority}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={
                            req.status === "Karşılanıyor" ? "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20" :
                              "bg-amber-500/10 text-amber-400 hover:bg-amber-500/20"
                          }>
                            {req.status || "Analyzing"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  No data found.
                </div>
              )}
            </TabsContent>

            <TabsContent value="compliance" className="p-6">
              {complianceMatrix.length > 0 ? (
                <div className="space-y-4">
                  {complianceMatrix.map((item: any, index: number) => (
                    <Card key={index} className="bg-slate-950/30 border-slate-800 p-4 hover:border-slate-700 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-slate-200 font-medium">{item.area}</h4>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-400 font-mono text-sm">{item.score}/100</span>
                          <Badge className={
                            item.status === "Düşük Risk" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                              "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          }>
                            {item.status}
                          </Badge>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  No data found.
                </div>
              )}
            </TabsContent>

            <TabsContent value="proposal" className="p-8">
              <div className="prose prose-invert max-w-none prose-headings:text-slate-200 prose-p:text-slate-400 prose-a:text-blue-400 prose-strong:text-slate-200">
                <div className="whitespace-pre-wrap font-serif leading-relaxed text-slate-300 bg-slate-950/30 p-8 rounded-xl border border-slate-800/50 shadow-inner">
                  {proposalText || "Draft proposal not found."}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </Card>
      )}
    </div>
  );
}
