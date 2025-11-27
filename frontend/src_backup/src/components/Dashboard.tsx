import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { 
  Database, 
  TrendingUp, 
  CheckCircle2, 
  Clock,
  FileText,
  FileSearch,
  Shield,
  PenTool,
  RefreshCw,
  Search
} from "lucide-react";

const kpiData = [
  {
    title: "Toplam Fırsat Sayısı",
    value: "1,247",
    icon: Database,
    gradient: "from-blue-600 to-blue-500"
  },
  {
    title: "Bugün Yeni Eklenenler",
    value: "23",
    subtitle: "NAICS 721110",
    icon: TrendingUp,
    gradient: "from-emerald-600 to-emerald-500"
  },
  {
    title: "Tamamlanan Analiz",
    value: "342",
    icon: CheckCircle2,
    gradient: "from-purple-600 to-purple-500"
  },
  {
    title: "Ortalama Analiz Süresi",
    value: "28sn",
    icon: Clock,
    gradient: "from-orange-600 to-orange-500"
  }
];

const agents = [
  { name: "Document Processor", status: "Aktif", icon: FileText },
  { name: "Requirements Extractor", status: "Aktif", icon: FileSearch },
  { name: "Compliance Analyst", status: "Aktif", icon: Shield },
  { name: "Proposal Writer", status: "Aktif", icon: PenTool }
];

const recentActivities = [
  { 
    noticeId: "SAM-721110-2025-001", 
    title: "Hotel Accommodation Services - Washington DC",
    risk: "low"
  },
  { 
    noticeId: "SAM-721110-2025-002", 
    title: "Extended Stay Housing for Military Personnel",
    risk: "medium"
  },
  { 
    noticeId: "SAM-721110-2025-003", 
    title: "Emergency Housing Services - Natural Disaster Response",
    risk: "high"
  },
  { 
    noticeId: "SAM-721110-2025-004", 
    title: "Conference Center & Lodging - Federal Training",
    risk: "low"
  },
  { 
    noticeId: "SAM-721110-2025-005", 
    title: "Temporary Housing for Federal Employees",
    risk: "medium"
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

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, index) => {
          const Icon = kpi.icon;
          return (
            <Card 
              key={index}
              className={`bg-gradient-to-br ${kpi.gradient} border-0 p-6 hover:scale-105 transition-transform cursor-pointer`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-white/80 text-sm mb-2">{kpi.title}</p>
                  <h3 className="text-white mb-1">
                    {kpi.value}
                  </h3>
                  {kpi.subtitle && (
                    <p className="text-white/70 text-sm">{kpi.subtitle}</p>
                  )}
                </div>
                <Icon className="w-8 h-8 text-white/80" />
              </div>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Agent Status */}
        <Card className="bg-slate-900/50 border-slate-800 p-6 backdrop-blur-sm">
          <h3 className="text-white mb-4">AI Ajan Durumu</h3>
          <div className="space-y-3">
            {agents.map((agent, index) => {
              const Icon = agent.icon;
              return (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-blue-600/20">
                      <Icon className="w-4 h-4 text-blue-400" />
                    </div>
                    <span className="text-slate-200 text-sm">{agent.name}</span>
                  </div>
                  <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50">
                    {agent.status}
                  </Badge>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Recent Activities */}
        <Card className="bg-slate-900/50 border-slate-800 p-6 lg:col-span-2 backdrop-blur-sm">
          <h3 className="text-white mb-4">Son Aktiviteler</h3>
          <div className="space-y-3">
            {recentActivities.map((activity, index) => (
              <div 
                key={index}
                className="p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <p className="text-blue-400 text-sm">{activity.noticeId}</p>
                  {getRiskBadge(activity.risk)}
                </div>
                <p className="text-slate-300 text-sm">{activity.title}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Quick Start Actions */}
      <Card className="bg-gradient-to-br from-slate-900/50 to-slate-800/50 border-slate-800 p-6 backdrop-blur-sm">
        <h3 className="text-white mb-4">Hızlı Başlangıç</h3>
        <div className="flex flex-col sm:flex-row gap-4">
          <Button 
            className="bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white flex-1"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Yeni İlanları Senkronize Et (721110)
          </Button>
          <Button 
            className="bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-700 hover:to-orange-600 text-white flex-1"
          >
            <Search className="w-4 h-4 mr-2" />
            Fırsat Aramaya Başla
          </Button>
        </div>
      </Card>
    </div>
  );
}
