import { useState, useEffect } from "react";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import { Search, Calendar, FileText, Play, Eye, AlertCircle, RefreshCw, Download } from "lucide-react";
import {
  loadOpportunities,
  startSamSync,
  startAttachmentDownload,
  type Opportunity,
  type OpportunityFilters
} from "../api/opportunities";

interface OpportunitySearchProps {
  onAnalyze?: (opportunity: Opportunity) => void;
}

const getRiskBadge = (risk: string | undefined) => {
  if (!risk) return null;
  const variants = {
    low: { label: "Düşük Risk", className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50" },
    medium: { label: "Orta Risk", className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50" },
    high: { label: "Yüksek Risk", className: "bg-red-500/20 text-red-400 border-red-500/50" }
  };
  const variant = variants[risk as keyof typeof variants] || variants.low;
  return <Badge variant="outline" className={variant.className}>{variant.label}</Badge>;
};

const getDeadlineBadge = (daysLeft: number) => {
  if (daysLeft <= 5) {
    return <Badge className="bg-red-500/20 text-red-400 border-red-500/50">{daysLeft} gün kaldı</Badge>;
  } else if (daysLeft <= 10) {
    return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/50">{daysLeft} gün kaldı</Badge>;
  }
  return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">{daysLeft} gün kaldı</Badge>;
};

export default function OpportunitySearch({ onAnalyze }: OpportunitySearchProps) {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<OpportunityFilters>({
    noticeId: "",
    naicsCode: "721110",
    keyword: ""
  });
  const [syncing, setSyncing] = useState(false);

  const fetchOpportunities = async () => {
    setLoading(true);
    try {
      const data = await loadOpportunities(filters);
      setOpportunities(data);
    } catch (error) {
      console.error("Error loading opportunities:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunities();
  }, []);

  const handleSearch = () => {
    fetchOpportunities();
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await startSamSync({
        naics: filters.naicsCode,
        keyword: filters.keyword
      });
      // Poll for completion or just wait a bit and reload
      setTimeout(() => {
        fetchOpportunities();
        setSyncing(false);
      }, 5000);
    } catch (error) {
      console.error("Sync error:", error);
      setSyncing(false);
    }
  };

  const handleDownload = async (id: number) => {
    try {
      await startAttachmentDownload(id);
      alert("Doküman indirme başlatıldı. Arka planda devam ediyor.");
    } catch (error) {
      console.error("Download error:", error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Filter Section */}
      <Card className="bg-slate-900/50 border-slate-800 p-6 backdrop-blur-sm">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-slate-400 text-sm mb-2 block">Notice ID</label>
            <Input
              placeholder="SAM-721110-..."
              className="bg-slate-800 border-slate-700 text-white"
              value={filters.noticeId}
              onChange={(e) => setFilters(prev => ({ ...prev, noticeId: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-slate-400 text-sm mb-2 block">NAICS Kodu</label>
            <Input
              value={filters.naicsCode}
              onChange={(e) => setFilters(prev => ({ ...prev, naicsCode: e.target.value }))}
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
          <div>
            <label className="text-slate-400 text-sm mb-2 block">Anahtar Kelime</label>
            <Input
              placeholder="Örn: hotel, lodging..."
              value={filters.keyword}
              onChange={(e) => setFilters(prev => ({ ...prev, keyword: e.target.value }))}
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
          <div className="flex items-end gap-2">
            <Button
              onClick={handleSearch}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white"
            >
              <Search className="w-4 h-4 mr-2" />
              {loading ? "Aranıyor..." : "Ara"}
            </Button>
            <Button
              onClick={handleSync}
              disabled={syncing}
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-800"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </Card>

      {/* API Status Alert */}
      <Alert className="bg-blue-500/10 border-blue-500/50 backdrop-blur-sm">
        <AlertCircle className="h-4 w-4 text-blue-400" />
        <AlertDescription className="text-blue-300">
          SAM.gov API bağlantısı aktif. {opportunities.length} fırsat listeleniyor.
        </AlertDescription>
      </Alert>

      {/* Results */}
      <div className="grid grid-cols-1 gap-4">
        {loading ? (
          <div className="text-center text-slate-400 py-8">Yükleniyor...</div>
        ) : opportunities.length === 0 ? (
          <div className="text-center text-slate-400 py-8">Fırsat bulunamadı.</div>
        ) : (
          opportunities.map((opp) => (
            <Card
              key={opp.id}
              className="bg-slate-900/50 border-slate-800 p-6 hover:bg-slate-900/70 transition-all hover:border-blue-500/50 backdrop-blur-sm"
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <FileText className="w-5 h-5 text-blue-400" />
                    <p className="text-blue-400 font-mono">{opp.noticeId}</p>
                    {getDeadlineBadge(opp.daysLeft)}
                  </div>
                  <h4 className="text-white mb-2">{opp.title}</h4>
                  <div className="flex items-center gap-4 text-sm text-slate-400">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>Yayın: {opp.postedDate}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>Yanıt: {opp.responseDeadline}</span>
                    </div>
                  </div>
                  {opp.analyzed && (
                    <div className="mt-2">
                      {getRiskBadge(opp.risk)}
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => handleDownload(opp.id)}
                    className="border-slate-600 text-white hover:bg-slate-800 hover:border-slate-500"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Doküman
                  </Button>
                  <Button
                    onClick={() => onAnalyze?.(opp)}
                    className="bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-700 hover:to-orange-600 text-white"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Analizi Başlat
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
