import { useState } from "react";
import {
    Search, Send, Paperclip, MoreVertical,
    Phone
} from "lucide-react";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { Textarea } from "./ui/textarea";

// --- MOCK DATA ---
const conversations = [
    {
        id: "1",
        noticeId: "SAM-721110-2025-001",
        title: "Hotel Accommodation Services - Washington DC",
        contact: "John Doe (Hotel Manager)",
        lastMessage: "Fiyat teklifinizi aldık, yönetimle görüşüp döneceğim.",
        time: "10 dk önce",
        status: "waiting_reply", // waiting_reply, action_needed, closed
        unread: 2,
        avatar: "JD"
    },
    {
        id: "2",
        noticeId: "SAM-721110-2025-003",
        title: "Emergency Housing Services - Disaster Relief",
        contact: "Sarah Smith (Procurement)",
        lastMessage: "Siz: Teklif dosyasını ekte iletiyorum.",
        time: "2 saat önce",
        status: "proposal_sent",
        unread: 0,
        avatar: "SS"
    },
    {
        id: "3",
        noticeId: "SAM-721110-2025-004",
        title: "Conference Center & Lodging",
        contact: "Michael Brown",
        lastMessage: "Lütfen SOW formunu imzalayıp gönderin.",
        time: "1 gün önce",
        status: "action_needed",
        unread: 1,
        avatar: "MB"
    }
];

const messages = [
    {
        id: 1,
        type: "system",
        content: "Fırsat takibe alındı ve AI analizi tamamlandı.",
        date: "24 Kas 09:00"
    },
    {
        id: 2,
        type: "out",
        sender: "MergenLite (Otomatik)",
        content: "Sayın Yetkili, Washington DC'deki konaklama ihalesi (SAM-721110-2025-001) için müsaitlik durumunuzu ve oda fiyatlarınızı öğrenmek istiyoruz. Detaylı SOW ektedir.",
        date: "24 Kas 09:15",
        attachments: ["SOW_Request.pdf"]
    },
    {
        id: 3,
        type: "in",
        sender: "John Doe <john.doe@hotel.com>",
        content: "Merhaba, talebinizi aldık. Belirttiğiniz tarihlerde müsaitliğimiz var. Standart oda fiyatımız $150/gece şeklindedir. Kahvaltı dahil mi olsun?",
        date: "24 Kas 14:30"
    },
    {
        id: 4,
        type: "out",
        sender: "Özgür Şarlı",
        content: "Merhaba John, evet kahvaltı dahil fiyat revizesi yapabilir misin? Ayrıca toplantı odası kapasitelerini de teyit etmek isteriz.",
        date: "Bugün 09:45"
    },
    {
        id: 5,
        type: "in",
        sender: "John Doe <john.doe@hotel.com>",
        content: "Fiyat teklifinizi aldık, yönetimle görüşüp döneceğim. Muhtemelen yarına kadar netleşir.",
        date: "10 dk önce"
    }
];

export default function Communication() {
    const [selectedId, setSelectedId] = useState("1");
    const selectedChat = conversations.find(c => c.id === selectedId);

    return (
        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-12rem)]">

            {/* SOL PANEL: KONUŞMA LİSTESİ */}
            <Card className="col-span-4 bg-slate-900/50 border-slate-800 flex flex-col overflow-hidden backdrop-blur-sm">
                <div className="p-4 border-b border-slate-800">
                    <div className="relative">
                        <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                        <Input
                            placeholder="Fırsat veya kişi ara..."
                            className="pl-9 bg-slate-950/50 border-slate-800 text-slate-200 focus:border-blue-500"
                        />
                    </div>
                </div>

                <ScrollArea className="flex-1">
                    <div className="flex flex-col p-2 gap-1">
                        {conversations.map((chat) => (
                            <button
                                key={chat.id}
                                onClick={() => setSelectedId(chat.id)}
                                className={`flex items-start gap-3 p-3 rounded-lg transition-all text-left group ${selectedId === chat.id
                                        ? "bg-blue-600/10 border border-blue-600/20"
                                        : "hover:bg-slate-800/50 border border-transparent"
                                    }`}
                            >
                                <Avatar className="h-10 w-10 border border-slate-700">
                                    <AvatarImage src="" />
                                    <AvatarFallback className="bg-slate-800 text-slate-300">{chat.avatar}</AvatarFallback>
                                </Avatar>

                                <div className="flex-1 overflow-hidden">
                                    <div className="flex justify-between items-center mb-1">
                                        <span className={`font-semibold text-sm truncate ${selectedId === chat.id ? "text-blue-400" : "text-slate-200"}`}>
                                            {chat.contact}
                                        </span>
                                        <span className="text-[10px] text-slate-500">{chat.time}</span>
                                    </div>
                                    <p className="text-xs text-slate-400 truncate mb-1.5">{chat.title}</p>
                                    <p className="text-xs text-slate-500 truncate">{chat.lastMessage}</p>

                                    <div className="mt-2 flex items-center gap-2">
                                        {chat.status === "action_needed" && (
                                            <Badge variant="outline" className="text-[10px] h-5 border-red-500/30 text-red-400 bg-red-500/10">Aksiyon Gerekli</Badge>
                                        )}
                                        {chat.status === "waiting_reply" && (
                                            <Badge variant="outline" className="text-[10px] h-5 border-yellow-500/30 text-yellow-400 bg-yellow-500/10">Cevap Bekleniyor</Badge>
                                        )}
                                        {chat.status === "proposal_sent" && (
                                            <Badge variant="outline" className="text-[10px] h-5 border-blue-500/30 text-blue-400 bg-blue-500/10">Teklif İletildi</Badge>
                                        )}
                                    </div>
                                </div>

                                {chat.unread > 0 && (
                                    <div className="h-2 w-2 rounded-full bg-blue-500 mt-2"></div>
                                )}
                            </button>
                        ))}
                    </div>
                </ScrollArea>
            </Card>

            {/* SAĞ PANEL: DETAY VE MESAJLAŞMA */}
            <Card className="col-span-8 bg-slate-900/50 border-slate-800 flex flex-col overflow-hidden backdrop-blur-sm">

                {/* HEADER */}
                <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/80">
                    <div className="flex items-center gap-4">
                        <Avatar className="h-10 w-10 border border-slate-700">
                            <AvatarFallback className="bg-blue-600 text-white">{selectedChat?.avatar}</AvatarFallback>
                        </Avatar>
                        <div>
                            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                                {selectedChat?.contact}
                                <Badge variant="secondary" className="text-[10px] bg-slate-800 text-slate-300">{selectedChat?.noticeId}</Badge>
                            </h3>
                            <p className="text-xs text-slate-400">{selectedChat?.title}</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="ghost" size="icon" className="text-slate-400 hover:text-white hover:bg-slate-800">
                            <Phone className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="text-slate-400 hover:text-white hover:bg-slate-800">
                            <MoreVertical className="h-4 w-4" />
                        </Button>
                    </div>
                </div>

                {/* MESAJ ALANI */}
                <ScrollArea className="flex-1 p-6 bg-slate-950/30">
                    <div className="space-y-6">
                        {messages.map((msg) => (
                            <div key={msg.id}>
                                {msg.type === "system" ? (
                                    <div className="flex justify-center my-4">
                                        <span className="text-[10px] bg-slate-800/50 text-slate-400 px-3 py-1 rounded-full border border-slate-700/50">
                                            {msg.content} • {msg.date}
                                        </span>
                                    </div>
                                ) : (
                                    <div className={`flex gap-4 ${msg.type === "out" ? "flex-row-reverse" : ""}`}>
                                        <Avatar className="h-8 w-8 border border-slate-700 mt-1">
                                            <AvatarFallback className={msg.type === "out" ? "bg-blue-600 text-white" : "bg-emerald-600 text-white"}>
                                                {msg.sender ? msg.sender[0] : "?"}
                                            </AvatarFallback>
                                        </Avatar>

                                        <div className={`flex flex-col max-w-[75%] ${msg.type === "out" ? "items-end" : "items-start"}`}>
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-xs text-slate-300 font-medium">{msg.sender}</span>
                                                <span className="text-[10px] text-slate-500">{msg.date}</span>
                                            </div>

                                            <div className={`p-4 rounded-2xl text-sm leading-relaxed shadow-md ${msg.type === "out"
                                                    ? "bg-blue-600 text-white rounded-tr-none"
                                                    : "bg-slate-800 text-slate-200 border border-slate-700 rounded-tl-none"
                                                }`}>
                                                {msg.content}

                                                {msg.attachments && (
                                                    <div className="mt-3 pt-3 border-t border-white/10 flex flex-col gap-2">
                                                        {msg.attachments.map((file, i) => (
                                                            <div key={i} className="flex items-center gap-2 bg-black/20 p-2 rounded-lg text-xs hover:bg-black/30 cursor-pointer transition-colors">
                                                                <Paperclip className="h-3 w-3" />
                                                                {file}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </ScrollArea>

                {/* YAZMA ALANI */}
                <div className="p-4 bg-slate-900 border-t border-slate-800">
                    <div className="relative">
                        <Textarea
                            placeholder="Bir cevap yazın..."
                            className="min-h-[80px] bg-slate-950/50 border-slate-800 text-slate-200 pr-24 resize-none focus:border-blue-500/50"
                        />
                        <div className="absolute bottom-3 right-3 flex gap-2">
                            <Button size="icon" variant="ghost" className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800">
                                <Paperclip className="h-4 w-4" />
                            </Button>
                            <Button size="icon" className="h-8 w-8 bg-blue-600 hover:bg-blue-700 text-white">
                                <Send className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                    <div className="mt-2 flex gap-2">
                        <Badge variant="outline" className="text-[10px] cursor-pointer hover:bg-slate-800 text-slate-400 border-slate-700">
                            + Hızlı Cevap: Teşekkürler
                        </Badge>
                        <Badge variant="outline" className="text-[10px] cursor-pointer hover:bg-slate-800 text-slate-400 border-slate-700">
                            + Toplantı Ayarla
                        </Badge>
                    </div>
                </div>

            </Card>
        </div>
    );
}
