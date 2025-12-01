import { useState } from "react";
import {
  Home, Search, Bot, FileText, MessageSquare,
  LogOut, Bell
} from "lucide-react";
import { Button } from "./components/ui/button";
import { ScrollArea } from "./components/ui/scroll-area";
import { Avatar, AvatarFallback } from "./components/ui/avatar";
import { Badge } from "./components/ui/badge";

// Page Components
import Dashboard from "./components/Dashboard";
import OpportunitySearch from "./components/OpportunitySearch";
import AIAnalysis from "./components/AIAnalysis";
import ResultsReports from "./components/ResultsReports";
import Communication from "./components/Communication";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");

  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: Home },
    { id: "search", label: "Opportunity Search", icon: Search },
    { id: "analysis", label: "AI Analysis", icon: Bot },
    { id: "results", label: "Results", icon: FileText },
    { id: "communication", label: "Communication", icon: MessageSquare, badge: 3 },
  ];

  return (
    // Root container must be h-screen and overflow-hidden to act as the app window
    <div
      className="flex h-screen w-full bg-slate-950 text-slate-200 font-sans overflow-hidden selection:bg-blue-500/30"
      style={{ backgroundColor: '#020617', color: '#e2e8f0' }}
    >
      {/* GLOBAL STYLE INJECTION 
         This fixes the "white screen" issue on overscroll or partial content rendering 
      */}
      <style>{`
        html, body, #root {
          height: 100%;
          margin: 0;
          padding: 0;
          background-color: #020617 !important;
          overflow: hidden; /* Prevent body scroll, let React handle it */
        }
        ::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        ::-webkit-scrollbar-track {
          background: transparent;
        }
        ::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: #475569;
        }
      `}</style>

      {/* --- LEFT SIDEBAR --- */}
      <aside
        className="w-64 flex-shrink-0 flex flex-col bg-slate-950 border-r border-slate-800/60 z-20"
        style={{ backgroundColor: '#020617' }}
      >
        {/* Logo */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-800/60">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-900/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight text-white">MergenLite</span>
        </div>

        {/* Menu */}
        <ScrollArea className="flex-1 px-4 py-4">
          <div className="space-y-1">
            {menuItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive
                    ? "bg-blue-600/10 text-blue-400 border border-blue-600/20 shadow-sm"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-transparent"
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <item.icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-500 group-hover:text-slate-300"}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <Badge className="bg-blue-600 text-white border-0 text-[10px] h-5 px-1.5 shadow-md shadow-blue-900/30">{item.badge}</Badge>
                  )}
                </button>
              );
            })}
          </div>
        </ScrollArea>

        {/* Profile */}
        <div className="p-4 border-t border-slate-800/60 bg-slate-950/50">
          <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-900 cursor-pointer transition-colors border border-transparent hover:border-slate-800">
            <Avatar className="w-8 h-8 border border-slate-700 bg-slate-800">
              <AvatarFallback className="text-xs bg-slate-800 text-slate-300">OS</AvatarFallback>
            </Avatar>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium truncate text-slate-200">Ozgur Sarli</p>
              <p className="text-xs text-slate-500 truncate">Admin</p>
            </div>
            <LogOut className="w-4 h-4 text-slate-500 hover:text-slate-300 transition-colors" />
          </div>
        </div>
      </aside>

      {/* --- MAIN CONTENT AREA --- */}
      <main
        className="flex-1 flex flex-col min-w-0 bg-slate-950 relative"
        style={{ backgroundColor: '#020617' }}
      >
        {/* Header */}
        <header className="h-16 flex-shrink-0 border-b border-slate-800/60 flex items-center justify-between px-6 bg-slate-950/80 backdrop-blur-md z-10 sticky top-0">
          <div>
            <h2 className="text-lg font-semibold text-white tracking-tight">{menuItems.find(i => i.id === activeTab)?.label}</h2>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="text-slate-400 hover:text-white hover:bg-slate-800/50">
              <Bell className="w-5 h-5" />
            </Button>
          </div>
        </header>

        {/* Content Container 
            - 'overflow-y-auto' handles the vertical scrolling of the content
            - 'bg-slate-950' ensures background is dark even if content is short
        */}
        <div
          className={`flex-1 overflow-y-auto overflow-x-hidden relative scroll-smooth ${activeTab === 'communication' ? 'p-0' : 'p-6'}`}
          style={{ backgroundColor: '#020617' }}
        >
          {/* Inner Content Wrapper - Ensures min-height is satisfied */}
          <div
            className="min-h-full w-full animate-in fade-in zoom-in-[0.99] duration-300"
            style={{ backgroundColor: '#020617' }}
          >
            {activeTab === "dashboard" && <Dashboard />}
            {activeTab === "search" && <OpportunitySearch />}
            {activeTab === "analysis" && <AIAnalysis opportunity={null} />}
            {activeTab === "results" && <ResultsReports />}
            {activeTab === "communication" && <Communication />}
          </div>
        </div>
      </main>
    </div>
  );
}
