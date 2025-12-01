import { useEffect, useState } from "react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Button } from "./ui/button";
import {
  FileText,
  FileSearch,
  Shield,
  PenTool,
  CheckCircle2,
  Clock,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Hotel,
  Utensils,
  Mic2,
  Truck,
  CalendarDays,
  FileCheck,
  Download
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
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./ui/collapsible";

interface AIAnalysisProps {
  opportunity: Opportunity | null;
}

interface AnalysisResult {
  id: number;
  status: string;
  result_json: any;
  created_at: string;
  updated_at?: string;
  completed_at: string;
}

const processSteps = [
  {
    name: "Document Processor",
    key: "doc_processor",
    icon: FileText,
    description: "Document processing"
  },
  {
    name: "Requirement Extractor",
    key: "req_extractor",
    icon: FileSearch,
    description: "Requirement analysis"
  },
  {
    name: "Compliance Analyst",
    key: "compliance",
    icon: Shield,
    description: "Compliance check"
  },
  {
    name: "Proposal Writer",
    key: "proposal",
    icon: PenTool,
    description: "Proposal writing"
  }
];

// Helper component for Requirement Sections
const RequirementSection = ({ title, icon: Icon, data, isOpen = false }: { title: string, icon: any, data: any, isOpen?: boolean }) => {
  const [open, setOpen] = useState(isOpen);

  if (!data || (Array.isArray(data) && data.length === 0) || (typeof data === 'object' && Object.keys(data).length === 0)) {
    return null;
  }

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="border border-slate-800 rounded-lg bg-slate-950/30 mb-4 overflow-hidden">
      <CollapsibleTrigger className="flex items-center justify-between w-full p-4 hover:bg-slate-900/50 transition-colors">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-blue-500/10 text-blue-400">
            <Icon className="w-5 h-5" />
          </div>
          <h3 className="text-slate-200 font-medium text-left">{title}</h3>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
      </CollapsibleTrigger>
      <CollapsibleContent className="border-t border-slate-800/50 bg-slate-900/20 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          {Object.entries(data).map(([key, value]) => {
            if (value === null || value === undefined || value === "" || (Array.isArray(value) && value.length === 0)) return null;

            // Format key for display
            const label = key.replace(/_/g, " ").replace(/([A-Z])/g, " $1").trim();
            const displayLabel = label.charAt(0).toUpperCase() + label.slice(1);

            return (
              <div key={key} className="flex flex-col gap-1">
                <span className="text-slate-500 text-xs font-mono uppercase tracking-wider">{displayLabel}</span>
                <span className="text-slate-300">
                  {Array.isArray(value) ? (
                    <ul className="list-disc list-inside">
                      {value.map((item: any, i: number) => (
                        <li key={i} className="truncate">
                          {typeof item === 'object' ? JSON.stringify(item).substring(0, 50) + "..." : String(item)}
                        </li>
                      ))}
                    </ul>
                  ) : typeof value === 'object' ? (
                    <pre className="text-xs bg-slate-950 p-2 rounded border border-slate-800 overflow-x-auto">
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  ) : (
                    String(value)
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

export default function AIAnalysis({ opportunity }: AIAnalysisProps) {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!opportunity) return;

      try {
        setLoading(true);
        setError(null);
        // Fetch the latest analysis result for this opportunity
        const response = await api.get(`/pipeline/opportunity/${opportunity.id}/results?limit=1`);
        if (response.data && response.data.length > 0) {
          setAnalysisResult(response.data[0]);
        } else {
          setAnalysisResult(null);
        }
      } catch (err) {
        console.error("Error fetching analysis:", err);
        setError("Failed to load analysis results.");
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [opportunity]);

  if (!opportunity) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-slate-500">
        <FileSearch className="w-16 h-16 mb-4 opacity-20" />
        <p className="text-lg">Please select an opportunity from the "Opportunity Search" tab to view analysis.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-4" />
        <p className="text-slate-400 animate-pulse">Loading analysis data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-red-400">
        <AlertCircle className="w-12 h-12 mb-4 opacity-50" />
        <p className="text-lg">{error}</p>
        <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  // Determine current step based on status
  let currentStepIndex = 0;
  if (analysisResult) {
    if (analysisResult.status === 'completed') currentStepIndex = 4;
    else if (analysisResult.status === 'running') currentStepIndex = 2; // Assume in middle
    else if (analysisResult.status === 'failed') currentStepIndex = 0;
  }

  const sowData = analysisResult?.result_json?.sow_analysis || {};
  const complianceData = sowData.ComplianceRequirements || {};
  const farClauses = complianceData.far_clauses || [];

  // Generate Draft Proposal Text (Client-side generation)
  const generateProposalText = () => {
    if (!sowData.EventDetails) return "No analysis data available to generate proposal.";

    const event = sowData.EventDetails;
    const lodging = sowData.LodgingRequirements || {};

    return `# Technical Proposal for ${event.event_name || "Event"}
**Solicitation Number:** ${event.solicitation_number || "N/A"}
**Agency:** ${event.agency || "N/A"}

## 1. Executive Summary
We are pleased to submit this proposal to support the ${event.event_name}. Our solution ensures full compliance with all requirements outlined in the Statement of Work, providing high-quality lodging, meeting spaces, and logistical support.

## 2. Event Details
- **Dates:** ${event.start_date || "TBD"} to ${event.end_date || "TBD"}
- **Duration:** ${event.duration_days || 0} days
- **Location:** ${event.locations ? event.locations.map((l: any) => l.city).join(", ") : "TBD"}

## 3. Technical Approach

### 3.1 Lodging Strategy
We have secured room blocks that meet the minimum requirement of ${lodging.rooms_per_city_min || 0} rooms per night.
- **Cancellation Policy:** Compliant with ${lodging.cancellation_policy?.free_cancellation_hours_before_checkin || "standard"} hours notice.
- **Amenities:** ${lodging.amenities_required?.join(", ") || "Standard amenities included"}

### 3.2 Meeting Space & AV
All function spaces will be set up according to the specific layout requirements (U-Shape, Classroom, Theater) as detailed in the SOW. AV equipment including microphones, screens, and projectors will be provided and tested prior to the event start.

### 3.3 Transportation
Transportation services will be arranged to ensure attendees can travel between lodging and the venue within the required timeframe.

## 4. Past Performance
(Placeholder for relevant past performance examples matching this agency and scope)

## 5. Pricing
See attached pricing schedule for detailed cost breakdown.
`;
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header Info */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20 font-mono">
              {opportunity.noticeId}
            </Badge>
            <span className="text-slate-500 text-sm flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              Last Update: {analysisResult?.updated_at ? new Date(analysisResult.updated_at).toLocaleString() : "Just now"}
            </span>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">{opportunity.title}</h2>
          <p className="text-slate-400 max-w-3xl">{opportunity.description?.substring(0, 200)}...</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-slate-400 mb-1">Status</div>
          <Badge className={`px-3 py-1 ${analysisResult?.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'}`}>
            {analysisResult?.status === 'completed' ? 'Analysis Completed' : 'Processing...'}
          </Badge>
        </div>
      </div>

      {/* Process Flow */}
      <Card className="bg-slate-900/40 border-slate-800 p-8 backdrop-blur-sm shadow-lg relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-slate-800">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-1000"
            style={{ width: `${(currentStepIndex / processSteps.length) * 100}%` }}
          ></div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative z-10">
          {processSteps.map((step, index) => {
            const isActive = index === currentStepIndex;
            const isCompleted = index < currentStepIndex;
            const Icon = step.icon;

            return (
              <div key={step.key} className={`relative ${index !== processSteps.length - 1 ? "after:content-[''] after:absolute after:top-6 after:-right-4 after:w-8 after:h-[2px] after:bg-slate-800 md:after:block after:hidden" : ""}`}>
                <div className={`flex flex-col items-center text-center group transition-all duration-300 ${isActive ? "scale-105" : "opacity-70"}`}>
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-all duration-300 shadow-lg ${isActive ? "bg-blue-600 text-white shadow-blue-500/30 ring-2 ring-blue-500/20" :
                    isCompleted ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                      "bg-slate-800 text-slate-500 border border-slate-700"
                    }`}>
                    {isCompleted ? <CheckCircle2 className="w-6 h-6" /> : <Icon className="w-6 h-6" />}
                  </div>
                  <h4 className={`font-medium mb-1 ${isActive ? "text-white" : "text-slate-400"}`}>{step.name}</h4>
                  <p className="text-xs text-slate-500">{step.description}</p>

                  {isActive && (
                    <div className="mt-3 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] animate-pulse">
                      Processing...
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Detailed Results Tabs */}
      <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-sm shadow-lg overflow-hidden">
        <Tabs defaultValue="requirements" className="w-full">
          <div className="border-b border-slate-800 px-6 bg-slate-950/20">
            <TabsList className="w-full justify-start bg-transparent p-0 h-14 gap-8">
              <TabsTrigger
                value="requirements"
                className="rounded-none border-b-2 border-transparent px-0 h-14 data-[state=active]:border-blue-500 data-[state=active]:text-blue-400 data-[state=active]:bg-transparent text-slate-400 hover:text-slate-200 transition-colors text-sm font-medium"
              >
                Requirements
              </TabsTrigger>
              <TabsTrigger
                value="compliance"
                className="rounded-none border-b-2 border-transparent px-0 h-14 data-[state=active]:border-blue-500 data-[state=active]:text-blue-400 data-[state=active]:bg-transparent text-slate-400 hover:text-slate-200 transition-colors text-sm font-medium"
              >
                Compliance Matrix
              </TabsTrigger>
              <TabsTrigger
                value="proposal"
                className="rounded-none border-b-2 border-transparent px-0 h-14 data-[state=active]:border-blue-500 data-[state=active]:text-blue-400 data-[state=active]:bg-transparent text-slate-400 hover:text-slate-200 transition-colors text-sm font-medium"
              >
                Draft Proposal
              </TabsTrigger>
              <TabsTrigger
                value="emails"
                className="rounded-none border-b-2 border-transparent px-0 h-14 data-[state=active]:border-blue-500 data-[state=active]:text-blue-400 data-[state=active]:bg-transparent text-slate-400 hover:text-slate-200 transition-colors text-sm font-medium"
              >
                Email History
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="p-6 min-h-[400px]">
            <TabsContent value="requirements" className="mt-0 animate-in fade-in slide-in-from-bottom-2 duration-500">
              {!analysisResult ? (
                <div className="text-center py-12 text-slate-500">No analysis data available yet.</div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 mb-4 p-3 bg-blue-500/5 border border-blue-500/10 rounded-lg text-sm text-blue-300">
                    <AlertCircle className="w-4 h-4" />
                    AI extracted key requirements from the document. Please verify against original PDF.
                  </div>

                  <RequirementSection title="Event Details" icon={CalendarDays} data={sowData.EventDetails} isOpen={true} />
                  <RequirementSection title="Lodging Requirements" icon={Hotel} data={sowData.LodgingRequirements} />
                  <RequirementSection title="Food & Beverage" icon={Utensils} data={sowData.FoodAndBeverageRequirements} />
                  <RequirementSection title="AV Requirements" icon={Mic2} data={sowData.AVRequirements} />
                  <RequirementSection title="Transportation" icon={Truck} data={sowData.TransportationRequirements} />
                  <RequirementSection title="Deliverables" icon={FileCheck} data={sowData.Deliverables} />
                </div>
              )}
            </TabsContent>

            <TabsContent value="compliance" className="mt-0 animate-in fade-in slide-in-from-bottom-2 duration-500">
              {!analysisResult ? (
                <div className="text-center py-12 text-slate-500">No analysis data available yet.</div>
              ) : (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-white">FAR/EDAR Clauses</h3>
                    <Badge variant="outline" className="text-slate-400">{farClauses.length} Clauses Found</Badge>
                  </div>

                  <div className="rounded-md border border-slate-800 overflow-hidden">
                    <Table>
                      <TableHeader className="bg-slate-950/50">
                        <TableRow className="border-slate-800 hover:bg-transparent">
                          <TableHead className="text-slate-400 w-[150px]">Clause ID</TableHead>
                          <TableHead className="text-slate-400">Description</TableHead>
                          <TableHead className="text-slate-400 w-[100px]">Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {farClauses.length > 0 ? (
                          farClauses.map((clause: any, idx: number) => (
                            <TableRow key={idx} className="border-slate-800 hover:bg-slate-900/50">
                              <TableCell className="font-mono text-blue-400">{typeof clause === 'string' ? clause : clause.id || "N/A"}</TableCell>
                              <TableCell className="text-slate-300">{typeof clause === 'string' ? "Standard Clause" : clause.title || "No description available"}</TableCell>
                              <TableCell>
                                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">Active</Badge>
                              </TableCell>
                            </TableRow>
                          ))
                        ) : (
                          <TableRow>
                            <TableCell colSpan={3} className="text-center py-8 text-slate-500">
                              No compliance clauses found in the analysis.
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="proposal" className="mt-0 animate-in fade-in slide-in-from-bottom-2 duration-500">
              {!analysisResult ? (
                <div className="text-center py-12 text-slate-500">No analysis data available yet.</div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-medium text-white">Draft Technical Proposal</h3>
                    <Button variant="outline" size="sm" className="h-8 border-slate-700 text-slate-400">
                      <Download className="w-3.5 h-3.5 mr-2" />
                      Export PDF
                    </Button>
                  </div>

                  <div className="bg-slate-950 p-8 rounded-lg border border-slate-800 font-mono text-sm text-slate-300 whitespace-pre-wrap leading-relaxed shadow-inner h-[600px] overflow-y-auto custom-scrollbar">
                    {generateProposalText()}
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="emails" className="mt-0 animate-in fade-in slide-in-from-bottom-2 duration-500">
              <EmailHistory opportunityId={opportunity.id} />
            </TabsContent>
          </div>
        </Tabs>
      </Card>
    </div>
  );
}
