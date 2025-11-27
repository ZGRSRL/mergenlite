import { useState } from "react";

import { Home, Search, Bot, FileText, MessageSquare } from "lucide-react";
import Dashboard from "./components/Dashboard";
import OpportunitySearch from "./components/OpportunitySearch";
import AIAnalysis from "./components/AIAnalysis";
import ResultsReports from "./components/ResultsReports";
import Communication from "./components/Communication";
import { Opportunity } from "./api/opportunities";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);

  const handleAnalyze = (opp: Opportunity) => {
    console.log("handleAnalyze called with:", opp);
    setSelectedOpportunity(opp);
    setActiveTab("analysis");
  };

  console.log("App render, activeTab:", activeTab);


  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto p-4 md:p-6 lg:p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-white mb-2">
            MergenLite
          </h1>
          <p className="text-slate-400">
            SAM.gov Otomatik Teklif Analiz Platformu
          </p>
        </div>

        {/* Main Navigation Tabs */}
        {/* Main Navigation Tabs */}
        <div className="w-full space-y-6">
          <div className="grid w-full grid-cols-5 bg-slate-900/50 border border-slate-800 rounded-xl p-1">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`flex items-center justify-center px-3 py-2 text-sm font-medium rounded-lg transition-all ${activeTab === "dashboard"
                ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
            >
              <Home className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Dashboard</span>
            </button>
            <button
              onClick={() => setActiveTab("search")}
              className={`flex items-center justify-center px-3 py-2 text-sm font-medium rounded-lg transition-all ${activeTab === "search"
                ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
            >
              <Search className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Fırsat Arama</span>
            </button>
            <button
              onClick={() => setActiveTab("analysis")}
              className={`flex items-center justify-center px-3 py-2 text-sm font-medium rounded-lg transition-all ${activeTab === "analysis"
                ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
            >
              <Bot className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">AI Analiz</span>
            </button>
            <button
              onClick={() => setActiveTab("results")}
              className={`flex items-center justify-center px-3 py-2 text-sm font-medium rounded-lg transition-all ${activeTab === "results"
                ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
            >
              <FileText className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Sonuçlar</span>
            </button>
            <button
              onClick={() => setActiveTab("communication")}
              className={`flex items-center justify-center px-3 py-2 text-sm font-medium rounded-lg transition-all ${activeTab === "communication"
                ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">İletişim</span>
            </button>
          </div>

          <div className="mt-6">
            {activeTab === "dashboard" && <Dashboard />}
            {activeTab === "search" && <OpportunitySearch onAnalyze={handleAnalyze} />}
            {activeTab === "analysis" && <AIAnalysis opportunity={selectedOpportunity} />}
            {activeTab === "results" && <ResultsReports />}
            {activeTab === "communication" && <Communication />}
          </div>
        </div>
      </div >
    </div >
  );
}
