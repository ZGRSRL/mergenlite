import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Home, Search, Bot, FileText } from "lucide-react";
import Dashboard from "./components/Dashboard";
import OpportunitySearch from "./components/OpportunitySearch";
import AIAnalysis from "./components/AIAnalysis";
import ResultsReports from "./components/ResultsReports";

export default function App() {
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
        <Tabs defaultValue="dashboard" className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-8 bg-slate-900/50 border border-slate-800">
            <TabsTrigger 
              value="dashboard"
              className="text-slate-300 data-[state=active]:text-white data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-500"
            >
              <Home className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger 
              value="search"
              className="text-slate-300 data-[state=active]:text-white data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-500"
            >
              <Search className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Fırsat Arama</span>
            </TabsTrigger>
            <TabsTrigger 
              value="analysis"
              className="text-slate-300 data-[state=active]:text-white data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-500"
            >
              <Bot className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">AI Analiz</span>
            </TabsTrigger>
            <TabsTrigger 
              value="results"
              className="text-slate-300 data-[state=active]:text-white data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-500"
            >
              <FileText className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Sonuçlar</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            <Dashboard />
          </TabsContent>

          <TabsContent value="search">
            <OpportunitySearch />
          </TabsContent>

          <TabsContent value="analysis">
            <AIAnalysis />
          </TabsContent>

          <TabsContent value="results">
            <ResultsReports />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
