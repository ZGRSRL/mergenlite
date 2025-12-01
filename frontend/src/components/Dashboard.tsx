import { useEffect, useState } from "react";
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
  Search,
  Activity,
  ArrowUpRight
} from "lucide-react";
import axios from "axios";

interface DashboardStats {
  total_opportunities: number;
  today_new: number;
  analyzed_count: number;
  avg_analysis_time: string;
}

interface RecentActivity {
  id: string;
  noticeId: string;
  title: string;
  risk: 'low' | 'medium' | 'high';
}

const agents = [
  { name: "Document Processor", status: "Active", icon: FileText, color: "text-blue-400", bg: "bg-blue-500/10" },
  { name: "Requirement Extractor", status: "Active", icon: FileSearch, color: "text-purple-400", bg: "bg-purple-500/10" },
  { name: "Compliance Analyst", status: "Active", icon: Shield, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  { name: "Proposal Writer", status: "Active", icon: PenTool, color: "text-orange-400", bg: "bg-orange-500/10" }
];

const getRiskBadge = (risk: string) => {
  const variants = {
    low: { label: "Low Risk", className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    medium: { label: "Medium Risk", className: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
    high: { label: "High Risk", className: "bg-red-500/10 text-red-400 border-red-500/20" }
  };
  const variant = variants[risk as keyof typeof variants] || variants.low;
  return <Badge variant="outline" className={variant.className}>{variant.label}</Badge>;
};

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    total_opportunities: 0,
    today_new: 0,
    analyzed_count: 0,
    avg_analysis_time: "0s"
  });
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, activitiesRes] = await Promise.all([
          axios.get('/api/dashboard/stats'),
          axios.get('/api/dashboard/recent-activities')
        ]);

        setStats(statsRes.data);
        setRecentActivities(activitiesRes.data.activities);
      } catch (error) {
        console.error("Dashboard data fetch error:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const kpiData = [
    {
      title: "Total Opportunities",
      value: stats.total_opportunities.toLocaleString('en-US'),
      icon: Database,
      gradient: "from-blue-600/20 to-blue-500/10",
      border: "border-blue-500/20",
      text: "text-blue-400"
    },
    {
      title: "New Today",
      value: stats.today_new.toLocaleString('en-US'),
      subtitle: "NAICS 721110",
      icon: TrendingUp,
      gradient: "from-emerald-600/20 to-emerald-500/10",
      border: "border-emerald-500/20",
      text: "text-emerald-400"
    },
    {
      title: "Completed Analysis",
      value: stats.analyzed_count.toLocaleString('en-US'),
      icon: CheckCircle2,
      gradient: "from-purple-600/20 to-purple-500/10",
      border: "border-purple-500/20",
      text: "text-purple-400"
    },
    {
      title: "Avg. Analysis Time",
      value: stats.avg_analysis_time,
      icon: Clock,
      gradient: "from-orange-600/20 to-orange-500/10",
      border: "border-orange-500/20",
      text: "text-orange-400"
    }
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, index) => {
          const Icon = kpi.icon;
          return (
            <Card
              key={index}
              className={`bg-gradient-to-br ${kpi.gradient} border ${kpi.border} p-6 hover:scale-[1.02] transition-transform cursor-pointer backdrop-blur-sm relative overflow-hidden group`}
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-white/5 rounded-full blur-2xl -mr-8 -mt-8 pointer-events-none group-hover:bg-white/10 transition-colors"></div>
              <div className="flex items-start justify-between relative">
                <div className="flex-1">
                  <p className="text-slate-400 text-xs font-medium mb-2 uppercase tracking-wider">{kpi.title}</p>
                  <h3 className="text-2xl font-bold text-white mb-1 tracking-tight">
                    {loading ? <span className="animate-pulse">...</span> : kpi.value}
                  </h3>
                  {kpi.subtitle && (
                    <p className="text-slate-500 text-xs flex items-center gap-1">
                      <ArrowUpRight className="w-3 h-3" /> {kpi.subtitle}
                    </p>
                  )}
                </div>
                <div className={`p-3 rounded-xl bg-slate-950/30 ${kpi.text}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Ana Bölüm: Grid Yapısı */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
        {/* AI Agent Status */}
        <Card className="bg-slate-900/40 border-slate-800 p-6 backdrop-blur-sm shadow-lg lg:col-span-1 h-full flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-white font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              AI Agent Status
            </h3>
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">System Normal</Badge>
          </div>
          <div className="space-y-3 flex-1">
            {agents.map((agent, index) => {
              const Icon = agent.icon;
              return (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-950/30 border border-slate-800/50 hover:border-slate-700 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${agent.bg} ${agent.color} group-hover:scale-110 transition-transform`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-slate-200 text-sm font-medium">{agent.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                    <span className="text-xs text-slate-400">{agent.status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Recent Activities */}
        <Card className="bg-slate-900/40 border-slate-800 p-6 lg:col-span-2 backdrop-blur-sm shadow-lg h-full flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-white font-semibold">Recent Activities</h3>
            <Button variant="ghost" size="sm" className="text-xs text-slate-400 hover:text-white hover:bg-slate-800">
              View All
            </Button>
          </div>
          <div className="space-y-3 flex-1 overflow-y-auto custom-scrollbar max-h-[300px]">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-8 text-slate-500">
                <div className="w-6 h-6 border-2 border-slate-600 border-t-transparent rounded-full animate-spin mb-2"></div>
                <span className="text-xs">Loading...</span>
              </div>
            ) : recentActivities.length === 0 ? (
              <div className="text-center py-12 bg-slate-950/30 rounded-xl border border-slate-800/50 border-dashed">
                <p className="text-slate-500 text-sm">No activity records found.</p>
              </div>
            ) : (
              recentActivities.map((activity, index) => (
                <div
                  key={index}
                  className="p-4 rounded-xl bg-slate-950/30 border border-slate-800/50 hover:bg-slate-900/50 hover:border-slate-700 transition-all cursor-pointer group"
                >
                  <div className="flex items-start justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="bg-slate-900 text-slate-400 border-slate-700 text-[10px] font-mono">
                        {activity.noticeId}
                      </Badge>
                      <span className="text-xs text-slate-500">•</span>
                      <span className="text-xs text-slate-400">New Analysis</span>
                    </div>
                    {getRiskBadge(activity.risk)}
                  </div>
                  <p className="text-slate-300 text-sm font-medium group-hover:text-white transition-colors pl-1">{activity.title}</p>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Quick Start Actions */}
      <Card className="bg-gradient-to-r from-slate-900/60 to-slate-800/60 border-slate-800 p-6 backdrop-blur-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-white font-semibold mb-1">Quick Start</h3>
            <p className="text-slate-400 text-sm">Common actions to get started with the system.</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
            <Button
              className="bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 border-0 transition-all flex-1 md:flex-none"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Sync New Opportunities
            </Button>
            <Button
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-800 hover:text-white hover:border-slate-500 transition-all flex-1 md:flex-none"
            >
              <Search className="w-4 h-4 mr-2" />
              Search Opportunities
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
