import { useEffect, useState } from "react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "./ui/table";
import { Mail, ArrowUpRight, ArrowDownLeft, Loader2 } from "lucide-react";
import api from "../api/client";

interface EmailLog {
    id: number;
    direction: "inbound" | "outbound";
    subject: string;
    from_address: string;
    to_address: string;
    created_at: string;
    parsed_summary?: string;
}

interface EmailHistoryProps {
    opportunityId: number;
}

export default function EmailHistory({ opportunityId }: EmailHistoryProps) {
    const [emails, setEmails] = useState<EmailLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchEmails = async () => {
            try {
                setLoading(true);
                const response = await api.get(`/opportunities/${opportunityId}/emails`);
                setEmails(response.data);
                setError(null);
            } catch (err) {
                console.error("Error fetching emails:", err);
                setError("E-posta geçmişi yüklenirken bir hata oluştu.");
            } finally {
                setLoading(false);
            }
        };

        if (opportunityId) {
            fetchEmails();
        }
    }, [opportunityId]);

    if (loading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 text-center text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg">
                {error}
            </div>
        );
    }

    if (emails.length === 0) {
        return (
            <Card className="bg-slate-900/50 border-slate-800 p-8 text-center backdrop-blur-sm">
                <div className="flex flex-col items-center gap-4">
                    <div className="p-4 rounded-full bg-slate-800">
                        <Mail className="w-8 h-8 text-slate-400" />
                    </div>
                    <div>
                        <h3 className="text-white text-lg font-medium mb-2">E-posta Geçmişi Boş</h3>
                        <p className="text-slate-400 max-w-md mx-auto">
                            Bu fırsat için henüz herhangi bir e-posta iletişimi kaydedilmemiş.
                        </p>
                    </div>
                </div>
            </Card>
        );
    }

    return (
        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm overflow-hidden">
            <div className="p-6 border-b border-slate-800">
                <h3 className="text-white flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    İletişim Geçmişi
                </h3>
            </div>
            <div className="overflow-x-auto">
                <Table>
                    <TableHeader>
                        <TableRow className="border-slate-800 hover:bg-slate-800/50">
                            <TableHead className="text-slate-400">Yön</TableHead>
                            <TableHead className="text-slate-400">Konu</TableHead>
                            <TableHead className="text-slate-400">Kimden/Kime</TableHead>
                            <TableHead className="text-slate-400">Tarih</TableHead>
                            <TableHead className="text-slate-400">Özet</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {emails.map((email) => (
                            <TableRow key={email.id} className="border-slate-800 hover:bg-slate-800/50">
                                <TableCell>
                                    {email.direction === "inbound" ? (
                                        <Badge variant="outline" className="border-emerald-500/50 text-emerald-400 bg-emerald-500/10 gap-1">
                                            <ArrowDownLeft className="w-3 h-3" /> Gelen
                                        </Badge>
                                    ) : (
                                        <Badge variant="outline" className="border-blue-500/50 text-blue-400 bg-blue-500/10 gap-1">
                                            <ArrowUpRight className="w-3 h-3" /> Giden
                                        </Badge>
                                    )}
                                </TableCell>
                                <TableCell className="text-slate-300 font-medium">{email.subject}</TableCell>
                                <TableCell className="text-slate-400 text-sm">
                                    <div className="flex flex-col">
                                        <span>{email.from_address}</span>
                                        <span className="text-xs text-slate-500">to: {email.to_address}</span>
                                    </div>
                                </TableCell>
                                <TableCell className="text-slate-400 whitespace-nowrap">
                                    {new Date(email.created_at).toLocaleString('tr-TR')}
                                </TableCell>
                                <TableCell className="text-slate-400 max-w-md truncate">
                                    {email.parsed_summary || "-"}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </Card>
    );
}
