import React, { useState, useEffect, useRef } from "react";
import {
    Search, Filter, Building2, MoreVertical, Phone, Video,
    Clock, ArrowUpRight, ArrowDownLeft, Paperclip, Send,
    LayoutGrid, Star, Loader2
} from "lucide-react";
import api from "../api/client";

// --- TYPES ---
type HotelStatus = 'queued' | 'sent' | 'replied' | 'negotiating' | 'rejected' | 'booked';

interface OpportunityDashboardResponse {
    id: number;
    noticeId: string | null;
    title: string;
    agency: string | null;
    location: string | null;
    deadline: string | null;
    totalHotels: number;
    contacted: number;
    replies: number;
    negotiating: number;
    status: string;
    hotels: HotelResponse[];
}

interface HotelResponse {
    id: number;
    name: string;
    manager: string | null;
    status: string;
    rating: number | null;
    price: string | null;
    lastUpdate: string | null;
    unread: number;
}

interface Hotel {
    id: number;
    name: string;
    manager: string;
    status: HotelStatus;
    rating: number | string;
    price: string | null;
    lastUpdate: string;
    unread: number;
    avatar?: string;
}

interface Opportunity {
    id: number;
    noticeId: string;
    title: string;
    agency: string;
    location: string;
    deadline: string | null;
    stats: { total: number; contacted: number; replied: number; negotiating: number };
    hotels: Hotel[];
}

interface Message {
    id: number;
    type: 'in' | 'out' | 'system';
    text: string;
    time: string;
}

// --- UI COMPONENTS ---

const Badge = ({ children, variant = 'default', className = "" }: any) => {
    const variants: any = {
        default: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        outline: "border-slate-700 text-slate-400",
        negotiating: "bg-amber-500/20 text-amber-400 border-amber-500/30",
        replied: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
        sent: "bg-blue-500/20 text-blue-400 border-blue-500/30",
        queued: "bg-slate-800 text-slate-500 border-slate-700",
    };
    return (
        <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${variants[variant] || variants.default} ${className}`}>
            {children}
        </span>
    );
};

const Avatar = ({ children, className }: any) => (
    <div className={`rounded-full flex items-center justify-center overflow-hidden ${className}`}>{children}</div>
);

// --- MAIN APP COMPONENT ---

export default function Communication() {
    const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
    const [filteredOpportunities, setFilteredOpportunities] = useState<Opportunity[]>([]);
    const [selectedOppId, setSelectedOppId] = useState<number | null>(null);
    const [selectedHotelId, setSelectedHotelId] = useState<number | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [msgInput, setMsgInput] = useState("");
    const [searchTerm, setSearchTerm] = useState("");
    const [hotelFilter, setHotelFilter] = useState<HotelStatus | 'all'>('all');
    const [loading, setLoading] = useState(true);
    const [loadingMessages, setLoadingMessages] = useState(false);
    const [sendingMessage, setSendingMessage] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Fetch Dashboard Data
    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                setLoading(true);
                // Use /api prefix to ensure proxy works
                const response = await api.get("/api/communications/dashboard");
                const data: Opportunity[] = response.data.map((opp: OpportunityDashboardResponse) => ({
                    id: opp.id,
                    noticeId: opp.noticeId || '',
                    title: opp.title,
                    agency: opp.agency || '',
                    location: opp.location || '',
                    deadline: opp.deadline || null,
                    stats: {
                        total: opp.totalHotels,
                        contacted: opp.contacted,
                        replied: opp.replies,
                        negotiating: opp.negotiating
                    },
                    hotels: opp.hotels.map((h: HotelResponse) => ({
                        id: h.id,
                        name: h.name,
                        manager: h.manager || '',
                        status: h.status as HotelStatus,
                        rating: h.rating || 'N/A',
                        price: h.price || null,
                        lastUpdate: h.lastUpdate || '',
                        unread: h.unread || 0
                    }))
                }));
                setOpportunities(data);
                setFilteredOpportunities(data);

                if (data.length > 0) {
                    setSelectedOppId(data[0].id);
                    if (data[0].hotels && data[0].hotels.length > 0) {
                        setSelectedHotelId(data[0].hotels[0].id);
                    }
                }
            } catch (error: any) {
                console.error("Error fetching communication dashboard:", error);
                setError("İletişim verileri yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin.");
            } finally {
                setLoading(false);
            }
        };

        fetchDashboard();
    }, []);

    // Fetch Messages when Hotel Changes
    useEffect(() => {
        const fetchMessages = async () => {
            if (!selectedHotelId) return;

            try {
                setLoadingMessages(true);
                // Use /api prefix
                const response = await api.get(`/api/communications/messages/${selectedHotelId}`);
                setMessages(response.data);
            } catch (error: any) {
                console.error("Error fetching messages:", error);
                setError("Mesajlar yüklenirken bir hata oluştu.");
            } finally {
                setLoadingMessages(false);
            }
        };

        fetchMessages();
    }, [selectedHotelId]);

    // Scroll to bottom on new message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!msgInput.trim() || !selectedHotelId || sendingMessage) return;

        const messageText = msgInput.trim();
        setMsgInput("");
        setSendingMessage(true);
        setError(null);

        const tempId = Date.now();
        const tempMsg: Message = { id: tempId, type: 'out', text: messageText, time: 'Gönderiliyor...' };
        setMessages(prev => [...prev, tempMsg]);

        try {
            const response = await api.post("/api/communications/messages", {
                hotel_id: selectedHotelId,
                text: messageText,
                direction: 'out'
            });

            // Replace temp message with real one
            setMessages(prev => prev.map(m => m.id === tempId ? {
                ...response.data,
                time: response.data.time || 'Şimdi'
            } : m));
        } catch (error: any) {
            console.error("Error sending message:", error);
            // Remove temp message on error
            setMessages(prev => prev.filter(m => m.id !== tempId));
            setError("Mesaj gönderilirken bir hata oluştu. Lütfen tekrar deneyin.");
            setMsgInput(messageText); // Restore message text
        } finally {
            setSendingMessage(false);
        }
    };

    // Filter opportunities based on search
    useEffect(() => {
        if (!searchTerm.trim()) {
            setFilteredOpportunities(opportunities);
        } else {
            const filtered = opportunities.filter(opp => 
                opp.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                opp.noticeId?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                opp.agency?.toLowerCase().includes(searchTerm.toLowerCase())
            );
            setFilteredOpportunities(filtered);
        }
    }, [searchTerm, opportunities]);

    const handleOppChange = (oppId: number) => {
        setSelectedOppId(oppId);
        const newOpp = opportunities.find(o => o.id === oppId);
        if (newOpp && newOpp.hotels.length > 0) {
            setSelectedHotelId(newOpp.hotels[0].id);
        } else {
            setSelectedHotelId(null);
            setMessages([]);
        }
    };

    const selectedOpp = opportunities.find(o => o.id === selectedOppId);
    const currentHotelList = (selectedOpp?.hotels || []).filter(hotel => 
        hotelFilter === 'all' || hotel.status === hotelFilter
    );
    const selectedHotel = currentHotelList.find(h => h.id === selectedHotelId);

    // Calculate days until deadline
    const getDaysUntilDeadline = (deadline: string | null): number | null => {
        if (!deadline) return null;
        try {
            const deadlineDate = new Date(deadline);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            deadlineDate.setHours(0, 0, 0, 0);
            const diffTime = deadlineDate.getTime() - today.getTime();
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            return diffDays;
        } catch {
            return null;
        }
    };

    const handleAISuggestion = (suggestion: string) => {
        setMsgInput(suggestion);
    };

    const getStatusBadgeVariant = (status: HotelStatus) => {
        switch (status) {
            case 'negotiating': return 'negotiating';
            case 'replied': return 'replied';
            case 'sent': return 'sent';
            case 'queued': return 'queued';
            default: return 'outline';
        }
    };

    const getStatusLabel = (status: HotelStatus) => {
        switch (status) {
            case 'negotiating': return 'Pazarlık';
            case 'replied': return 'Yanıtladı';
            case 'sent': return 'İletildi';
            case 'queued': return 'Sırada';
            case 'rejected': return 'Reddedildi';
            default: return status;
        }
    }

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-slate-500">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-4" />
                <p>İletişimler yükleniyor...</p>
            </div>
        );
    }

    return (
        <div
            className="flex h-full w-full bg-slate-950 text-slate-200 font-sans overflow-hidden selection:bg-blue-500/30"
            style={{ backgroundColor: '#020617', color: '#e2e8f0' }}
        >

            {/* --- COLUMN 1: AKTIF OPERASYONLAR --- */}
            <div className="w-[340px] flex flex-col border-r border-slate-800/60 bg-slate-950">
                {/* Header */}
                <div className="p-4 border-b border-slate-800/60 flex flex-col gap-4">
                    <div>
                        <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                            <div className="p-1 rounded bg-blue-600 text-white"><LayoutGrid size={14} /></div>
                            Aktif Operasyonlar
                        </h2>
                        <p className="text-[10px] text-slate-500 mt-1 pl-7">{opportunities.length} İhale Takipte</p>
                    </div>
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
                        <input
                            className="w-full h-9 bg-slate-900 border border-slate-800 rounded-lg pl-8 text-xs text-slate-300 placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-all"
                            placeholder="Q Fırsat Ara..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                {/* List */}
                <div className="flex-1 overflow-y-auto p-3 pr-2 space-y-3 custom-scrollbar">
                    {filteredOpportunities.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-40 text-slate-500 text-xs">
                            <p>Arama sonucu bulunamadı.</p>
                        </div>
                    ) : (
                        filteredOpportunities.map((opp) => {
                        const isActive = selectedOppId === opp.id;
                        const percent = opp.stats.total > 0 ? Math.round((opp.stats.contacted / opp.stats.total) * 100) : 0;

                        return (
                            <div
                                key={opp.id}
                                onClick={() => handleOppChange(opp.id)}
                                className={`p-3 rounded-xl border cursor-pointer transition-all group relative overflow-hidden
                  ${isActive
                                        ? "bg-slate-900 border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                                        : "bg-slate-950 border-slate-800/60 hover:border-slate-700 hover:bg-slate-900/50"
                                    }`}
                            >
                                {isActive && <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-blue-500" />}

                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-[9px] font-mono text-slate-500 border border-slate-800 px-1.5 py-0.5 rounded bg-slate-950">
                                        {opp.noticeId}
                                    </span>
                                    {opp.stats.negotiating > 0 && (
                                        <span className="text-[9px] font-bold text-amber-500 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                                            {opp.stats.negotiating} Pazarlık
                                        </span>
                                    )}
                                </div>

                                <h3 className={`text-xs font-semibold mb-2 leading-relaxed ${isActive ? 'text-blue-100' : 'text-slate-300'}`}>
                                    {opp.title}
                                </h3>

                                <div className="flex items-center gap-2 text-[10px] text-slate-500 mb-3">
                                    <span className="flex items-center gap-1"><Building2 size={10} /> {opp.agency}</span>
                                    <span className="w-1 h-1 rounded-full bg-slate-700" />
                                    <span>{opp.deadline}</span>
                                </div>

                                {/* Progress Mini Card */}
                                <div className="bg-slate-950 rounded-lg p-2 border border-slate-800/50">
                                    <div className="flex justify-between text-[10px] mb-1.5">
                                        <span className="text-slate-400">İletişim Kapsamı</span>
                                        <span className="text-slate-200 font-medium">{opp.stats.contacted}/{opp.stats.total} Otel</span>
                                    </div>
                                    <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden mb-2">
                                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${percent}%` }}></div>
                                    </div>
                                    <div className="flex gap-3">
                                        <div className="flex items-center gap-1 text-[9px] text-emerald-500">
                                            <ArrowDownLeft size={10} /> {opp.stats.replied} Yanıt
                                        </div>
                                        <div className="flex items-center gap-1 text-[9px] text-blue-400">
                                            <ArrowUpRight size={10} /> {opp.stats.contacted} Giden
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    }))}
                </div>
            </div>

            {/* --- COLUMN 2: HEDEF OTELLER --- */}
            <div className="w-[380px] flex flex-col border-r border-slate-800/60 bg-slate-950">
                <div className="h-[69px] border-b border-slate-800/60 flex items-center justify-between px-4 bg-slate-950">
                    <div>
                        <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                            <span className="p-1 rounded bg-purple-500/10 text-purple-400"><Building2 size={14} /></span>
                            Hedef Oteller
                        </h2>
                        <p className="text-[10px] text-slate-500 mt-0.5 ml-8">
                            {selectedOpp ? `Bu fırsat için ${selectedOpp.stats.total} otel ile iletişimde` : "Bir fırsat seçin"}
                        </p>
                    </div>
                    <button 
                        onClick={() => {
                            // Cycle through filter options
                            const filters: (HotelStatus | 'all')[] = ['all', 'queued', 'sent', 'replied', 'negotiating'];
                            const currentIndex = filters.indexOf(hotelFilter);
                            setHotelFilter(filters[(currentIndex + 1) % filters.length]);
                        }}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-800 text-[10px] text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-colors"
                    >
                        <Filter size={10} /> {hotelFilter === 'all' ? 'Filtrele' : getStatusLabel(hotelFilter)}
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-3 pr-2 custom-scrollbar">
                    {currentHotelList.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-40 text-slate-500 text-xs">
                            <Building2 className="w-8 h-8 mb-2 opacity-20" />
                            <p>Bu fırsat için otel bulunamadı.</p>
                        </div>
                    ) : (
                        currentHotelList.map((hotel) => {
                            const isSelected = selectedHotelId === hotel.id;
                            return (
                                <div
                                    key={hotel.id}
                                    onClick={() => setSelectedHotelId(hotel.id)}
                                    className={`group px-4 py-3 border-b border-slate-800/40 cursor-pointer transition-all relative
                      ${isSelected ? "bg-slate-900" : "hover:bg-slate-900/50"}
                    `}
                                >
                                    {isSelected && <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-blue-500" />}

                                    <div className="flex justify-between items-start mb-1">
                                        <h4 className={`text-xs font-medium truncate pr-4 ${isSelected ? "text-white" : "text-slate-300"}`}>
                                            {hotel.name}
                                        </h4>
                                        <span className="text-[10px] text-slate-500 whitespace-nowrap">{hotel.lastUpdate}</span>
                                    </div>

                                    <div className="flex justify-between items-center mt-2">
                                        <div className="flex items-center gap-2">
                                            <Badge variant={getStatusBadgeVariant(hotel.status)}>
                                                {getStatusLabel(hotel.status)}
                                            </Badge>
                                            {hotel.price && <span className="text-[11px] text-slate-400 font-mono tracking-tight">{hotel.price}</span>}
                                        </div>
                                        {hotel.unread > 0 && (
                                            <div className="h-5 w-5 rounded-full bg-blue-600 flex items-center justify-center text-[10px] font-bold text-white shadow-lg shadow-blue-500/20">
                                                {hotel.unread}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>

            {/* --- COLUMN 3: CHAT AREA --- */}
            <div className="flex-1 flex flex-col bg-slate-950">
                {selectedHotel ? (
                    <>
                        {/* Chat Header */}
                        <div className="h-[69px] border-b border-slate-800/60 flex items-center justify-between px-6 bg-slate-950">
                            <div className="flex items-center gap-3">
                                <Avatar className="h-9 w-9 bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-semibold text-xs border border-white/10">
                                    {selectedHotel.name 
                                        ? selectedHotel.name.split(' ').map(n => n[0]).filter(Boolean).join('').substring(0, 2).toUpperCase() || 'H'
                                        : 'H'}
                                </Avatar>
                                <div>
                                    <h2 className="text-sm font-semibold text-white">{selectedHotel.name}</h2>
                                    <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                                        <span className="text-slate-300">{selectedHotel.manager || "Yetkili"}</span>
                                        <span className="w-1 h-1 rounded-full bg-slate-600" />
                                        <span className="flex items-center gap-0.5 text-amber-400"><Star size={10} fill="currentColor" /> {selectedHotel.rating || "N/A"}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-1 text-slate-400">
                                <button className="p-2 hover:text-white hover:bg-slate-800/50 rounded-full transition-colors"><Phone size={16} /></button>
                                <button className="p-2 hover:text-white hover:bg-slate-800/50 rounded-full transition-colors"><Video size={16} /></button>
                                <button className="p-2 hover:text-white hover:bg-slate-800/50 rounded-full transition-colors"><MoreVertical size={16} /></button>
                            </div>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-6 pr-4 space-y-6 bg-slate-900/30 custom-scrollbar">
                            {/* Context Banner */}
                            {selectedOpp?.deadline && (() => {
                                const daysLeft = getDaysUntilDeadline(selectedOpp.deadline);
                                return daysLeft !== null && daysLeft >= 0 ? (
                                    <div className="flex justify-center mb-8">
                                        <div className="bg-blue-900/20 border border-blue-500/30 px-4 py-2 rounded-lg flex items-center gap-2 text-[10px] text-blue-200 shadow-sm">
                                            <Clock size={12} className="text-blue-400" />
                                            <span>Son Teslim Tarihine <span className="text-blue-400 font-bold">{daysLeft} gün</span> kaldı</span>
                                        </div>
                                    </div>
                                ) : null;
                            })()}

                            {loadingMessages ? (
                                <div className="flex justify-center py-8">
                                    <Loader2 className="w-6 h-6 animate-spin text-slate-600" />
                                </div>
                            ) : messages.length === 0 ? (
                                <div className="text-center text-slate-500 py-12">
                                    <p>Henüz mesaj yok. Konuşmayı başlatın!</p>
                                </div>
                            ) : (
                                messages.map((msg) => {
                                    if (msg.type === 'system') {
                                        return (
                                            <div key={msg.id} className="flex justify-center my-4">
                                                <span className="text-[10px] text-slate-500 bg-slate-900/50 border border-slate-800 px-3 py-1.5 rounded-full">
                                                    {msg.text}
                                                </span>
                                            </div>
                                        );
                                    }
                                    const isOut = msg.type === 'out';
                                    return (
                                        <div key={msg.id} className={`flex gap-3 ${isOut ? 'flex-row-reverse' : ''}`}>
                                            {!isOut && (
                                                <Avatar className="h-8 w-8 mt-1 bg-slate-800 text-slate-400 text-[10px] border border-slate-700">H</Avatar>
                                            )}
                                            {isOut && (
                                                <Avatar className="h-8 w-8 mt-1 bg-blue-900 text-blue-200 text-[10px] border border-blue-700">M</Avatar>
                                            )}

                                            <div className={`max-w-[70%] space-y-1 ${isOut ? 'items-end flex flex-col' : ''}`}>
                                                <div className={`px-4 py-3 text-xs leading-relaxed shadow-sm
                            ${isOut
                                                        ? 'bg-blue-600 text-white rounded-2xl rounded-tr-sm'
                                                        : 'bg-slate-800 text-slate-200 rounded-2xl rounded-tl-sm border border-slate-700/50'
                                                    }
                          `}>
                                                    {msg.text}
                                                </div>
                                                <span className="text-[9px] text-slate-600 px-1">{msg.time}</span>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <div className="p-4 bg-slate-950 border-t border-slate-800/60">
                            <div className="relative flex items-center bg-slate-900 border border-slate-800 rounded-2xl px-2 shadow-sm focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/20 transition-all">
                                <input
                                    className="flex-1 bg-transparent border-none text-xs text-slate-200 placeholder:text-slate-500 px-3 py-3.5 focus:outline-none disabled:opacity-50"
                                    placeholder="Mesaj yazın veya AI önerisi seçin..."
                                    value={msgInput}
                                    onChange={(e) => setMsgInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault();
                                            handleSendMessage();
                                        }
                                    }}
                                    disabled={sendingMessage || !selectedHotelId}
                                />
                                <button className="p-2 text-slate-400 hover:text-slate-200 transition-colors">
                                    <Paperclip size={16} />
                                </button>
                                <button
                                    onClick={handleSendMessage}
                                    disabled={sendingMessage || !msgInput.trim() || !selectedHotelId}
                                    className="p-2 m-1 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-colors shadow-lg shadow-blue-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {sendingMessage ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                                </button>
                            </div>

                            {/* AI Chips */}
                            <div className="flex gap-2 mt-3 pl-1 overflow-x-auto no-scrollbar">
                                <button 
                                    onClick={() => handleAISuggestion("Teklifinizi gözden geçirip revize edebilir misiniz?")}
                                    disabled={sendingMessage}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-[10px] text-slate-400 hover:text-blue-300 hover:border-blue-500/30 hover:bg-blue-950/20 transition-all whitespace-nowrap group disabled:opacity-50"
                                >
                                    <span className="text-blue-500 group-hover:animate-pulse">✨</span> Teklif revizesi yap
                                </button>
                                <button 
                                    onClick={() => handleAISuggestion("Toplantı yaparak detayları görüşmek ister misiniz?")}
                                    disabled={sendingMessage}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-[10px] text-slate-400 hover:text-blue-300 hover:border-blue-500/30 hover:bg-blue-950/20 transition-all whitespace-nowrap disabled:opacity-50"
                                >
                                    <span>📅</span> Toplantı öner
                                </button>
                                <button 
                                    onClick={() => handleAISuggestion("Teşekkür ederiz, geri dönüşünüzü bekliyoruz.")}
                                    disabled={sendingMessage}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-[10px] text-slate-400 hover:text-blue-300 hover:border-blue-500/30 hover:bg-blue-950/20 transition-all whitespace-nowrap disabled:opacity-50"
                                >
                                    <span>👍</span> Teşekkür et
                                </button>
                            </div>
                            {error && (
                                <div className="mt-2 px-3 py-2 bg-red-900/20 border border-red-500/30 rounded-lg text-[10px] text-red-400">
                                    {error}
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500">
                        <Building2 className="w-16 h-16 mb-4 opacity-20" />
                        <p>İletişime başlamak için bir otel seçin.</p>
                    </div>
                )}
            </div>

            <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #475569;
        }
        .no-scrollbar::-webkit-scrollbar {
            display: none;
        }
        .no-scrollbar {
            -ms-overflow-style: none;
            scrollbar-width: none;
        }
      `}</style>
        </div>
    );
}
