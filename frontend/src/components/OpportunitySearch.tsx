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
    low: { label: "Low Risk", className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    medium: { label: "Medium Risk", className: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
    high: { label: "High Risk", className: "bg-red-500/10 text-red-400 border-red-500/20" }
  };
  const variant = variants[risk as keyof typeof variants] || variants.low;
  return <Badge variant="outline" className={variant.className}>{variant.label}</Badge>;
};

const getDeadlineBadge = (daysLeft: number) => {
  if (daysLeft <= 5) {
    return <Badge className="bg-red-500/10 text-red-400 border-red-500/20">{daysLeft} days left</Badge>;
  } else if (daysLeft <= 10) {
    return <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20">{daysLeft} days left</Badge>;
  }
  return <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20">{daysLeft} days left</Badge>;
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
      alert("Document download started. Continuing in background.");
    } catch (error) {
      console.error("Download error:", error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Filter Section */}
      <Card className="bg-slate-900/50 border-slate-800 p-6 backdrop-blur-sm shadow-xl">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-slate-400 text-xs font-medium mb-2 block ml-1">Notice ID</label>
            <Input
              placeholder="SAM-721110-..."
              className="bg-slate-950/50 border-slate-800 text-slate-200 placeholder:text-slate-600 focus:border-blue-500/50 focus:ring-blue-500/20 transition-all"
              value={filters.noticeId}
              onChange={(e) => setFilters(prev => ({ ...prev, noticeId: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-slate-400 text-xs font-medium mb-2 block ml-1">NAICS Code</label>
            <Input
              value={filters.naicsCode}
              onChange={(e) => setFilters(prev => ({ ...prev, naicsCode: e.target.value }))}
              className="bg-slate-950/50 border-slate-800 text-slate-200 placeholder:text-slate-600 focus:border-blue-500/50 focus:ring-blue-500/20 transition-all"
            />
          </div>
          <div>
            <label className="text-slate-400 text-xs font-medium mb-2 block ml-1">Keyword</label>
            <Input
              placeholder="e.g., hotel, lodging..."
              value={filters.keyword}
              onChange={(e) => setFilters(prev => ({ ...prev, keyword: e.target.value }))}
              className="bg-slate-950/50 border-slate-800 text-slate-200 placeholder:text-slate-600 focus:border-blue-500/50 focus:ring-blue-500/20 transition-all"
            />
          </div>
          <div className="flex items-end gap-2">
            <Button
              onClick={handleSearch}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white shadow-lg shadow-blue-500/20 border-0 transition-all"
            >
              <Search className="w-4 h-4 mr-2" />
              {loading ? "Searching..." : "Search"}
            </Button>
            <Button
              onClick={handleSync}
              disabled={syncing}
              variant="outline"
              className="border-slate-700 text-slate-400 hover:text-slate-200 hover:bg-slate-800 hover:border-slate-600 transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </Card>

      {/* API Status Alert */}
      <Alert className="bg-blue-500/5 border-blue-500/20 backdrop-blur-sm">
        <AlertCircle className="h-4 w-4 text-blue-400" />
        <AlertDescription className="text-blue-300 text-xs">
          SAM.gov API connection active. {opportunities.length} opportunities listed.
        </AlertDescription>
      </Alert>

      {/* Results */}
      <div className="grid grid-cols-1 gap-4">
        {loading ? (
          <div className="text-center text-slate-500 py-12 flex flex-col items-center">
            <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mb-4"></div>
            <p>Loading opportunities...</p>
          </div>
        ) : opportunities.length === 0 ? (
          <div className="text-center text-slate-500 py-12 bg-slate-900/30 rounded-xl border border-slate-800/50 border-dashed">
            <Search className="w-8 h-8 mx-auto mb-3 opacity-50" />
            <p>No opportunities found matching criteria.</p>
          </div>
        ) : (
          opportunities.map((opp) => (
            <Card
              key={opp.id}
              className="group bg-slate-900/40 border-slate-800 p-6 hover:bg-slate-900/60 transition-all hover:border-blue-500/30 backdrop-blur-sm relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-[2px] h-full bg-blue-500/0 group-hover:bg-blue-500 transition-all"></div>

              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pl-2">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-1.5 rounded bg-blue-500/10 text-blue-400">
                      <FileText className="w-4 h-4" />
                    </div>
                    <p className="text-blue-400 font-mono text-xs tracking-wide">{opp.noticeId}</p>
                    {getDeadlineBadge(opp.daysLeft)}
                  </div>
                  <h4 className="text-slate-200 font-medium mb-2 group-hover:text-white transition-colors">{opp.title}</h4>
                  <div className="flex items-center gap-6 text-xs text-slate-500">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Posted: <span className="text-slate-400">{opp.postedDate}</span></span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Response: <span className="text-slate-400">{opp.responseDeadline}</span></span>
                    </div>
                  </div>
                  {opp.analyzed && (
                    <div className="mt-3">
                      {getRiskBadge(opp.risk)}
                    </div>
                  )}
                </div>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={() => handleDownload(opp.id)}
                    className="border-slate-700 text-slate-400 hover:text-white hover:bg-slate-800 hover:border-slate-600 transition-all text-xs h-9"
                  >
                    <Download className="w-3.5 h-3.5 mr-2" />
                    Document
                  </Button>
                  <Button
                    onClick={() => onAnalyze?.(opp)}
                    className="bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-500 hover:to-orange-400 text-white shadow-lg shadow-orange-500/20 border-0 transition-all text-xs h-9"
                  >
                    <Play className="w-3.5 h-3.5 mr-2" />
                    Start Analysis
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
