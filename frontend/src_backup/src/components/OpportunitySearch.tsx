import { useState } from "react";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import { Search, Calendar, FileText, Play, Eye, AlertCircle } from "lucide-react";

const opportunities = [
  {
    noticeId: "SAM-721110-2025-001",
    title: "Hotel Accommodation Services - Washington DC",
    publishedDate: "2025-11-01",
    responseDeadline: "2025-11-15",
    daysLeft: 8,
    risk: "low",
    analyzed: true
  },
  {
    noticeId: "SAM-721110-2025-002",
    title: "Extended Stay Housing for Military Personnel",
    publishedDate: "2025-11-03",
    responseDeadline: "2025-11-20",
    daysLeft: 13,
    risk: "medium",
    analyzed: true
  },
  {
    noticeId: "SAM-721110-2025-003",
    title: "Emergency Housing Services - Natural Disaster Response",
    publishedDate: "2025-11-05",
    responseDeadline: "2025-11-12",
    daysLeft: 5,
    risk: "high",
    analyzed: false
  },
  {
    noticeId: "SAM-721110-2025-004",
    title: "Conference Center & Lodging - Federal Training Programs",
    publishedDate: "2025-11-06",
    responseDeadline: "2025-11-25",
    daysLeft: 18,
    risk: "low",
    analyzed: true
  },
  {
    noticeId: "SAM-721110-2025-005",
    title: "Temporary Housing for Federal Employees - Remote Locations",
    publishedDate: "2025-11-07",
    responseDeadline: "2025-11-18",
    daysLeft: 11,
    risk: "medium",
    analyzed: false
  }
];

const getRiskBadge = (risk: string) => {
  const variants = {
    low: { label: "Düşük Risk", className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50" },
    medium: { label: "Orta Risk", className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50" },
    high: { label: "Yüksek Risk", className: "bg-red-500/20 text-red-400 border-red-500/50" }
  };
  const variant = variants[risk as keyof typeof variants];
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

export default function OpportunitySearch() {
  const [searchTerm, setSearchTerm] = useState("");
  const [naicsCode, setNaicsCode] = useState("721110");

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
            />
          </div>
          <div>
            <label className="text-slate-400 text-sm mb-2 block">NAICS Kodu</label>
            <Input 
              value={naicsCode}
              onChange={(e) => setNaicsCode(e.target.value)}
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
          <div>
            <label className="text-slate-400 text-sm mb-2 block">Anahtar Kelime</label>
            <Input 
              placeholder="Örn: hotel, lodging..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
          <div className="flex items-end">
            <Button className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white">
              <Search className="w-4 h-4 mr-2" />
              Ara
            </Button>
          </div>
        </div>
      </Card>

      {/* API Status Alert */}
      <Alert className="bg-blue-500/10 border-blue-500/50 backdrop-blur-sm">
        <AlertCircle className="h-4 w-4 text-blue-400" />
        <AlertDescription className="text-blue-300">
          SAM.gov API bağlantısı aktif. Günlük kota: 450/500 sorgu kaldı.
        </AlertDescription>
      </Alert>

      {/* Results */}
      <div className="grid grid-cols-1 gap-4">
        {opportunities.map((opp, index) => (
          <Card 
            key={index}
            className="bg-slate-900/50 border-slate-800 p-6 hover:bg-slate-900/70 transition-all hover:border-blue-500/50 backdrop-blur-sm"
          >
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <FileText className="w-5 h-5 text-blue-400" />
                  <p className="text-blue-400">{opp.noticeId}</p>
                  {getDeadlineBadge(opp.daysLeft)}
                </div>
                <h4 className="text-white mb-2">{opp.title}</h4>
                <div className="flex items-center gap-4 text-sm text-slate-400">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    <span>Yayın: {opp.publishedDate}</span>
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
                <Button variant="outline" className="border-slate-600 text-white hover:bg-slate-800 hover:border-slate-500">
                  <Eye className="w-4 h-4 mr-2" />
                  Detayları Gör
                </Button>
                <Button className="bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-700 hover:to-orange-600 text-white">
                  <Play className="w-4 h-4 mr-2" />
                  Analizi Başlat
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
