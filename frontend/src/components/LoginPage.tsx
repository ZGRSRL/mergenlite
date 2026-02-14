import { useState, FormEvent } from 'react'
import { Bot, Eye, EyeOff, LogIn, AlertCircle } from 'lucide-react'
import { setCredentials } from '../api/client'
import api from '../api/client'

interface LoginPageProps {
    onLoginSuccess: (username: string) => void
}

export default function LoginPage({ onLoginSuccess }: LoginPageProps) {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            // Set credentials in localStorage first
            setCredentials(username, password)

            // Verify by calling health endpoint
            const { data } = await api.get('/health')
            if (data.status === 'ok' || data.status === 'healthy' || data.status === 'degraded') {
                onLoginSuccess(username)
            } else {
                setError('Server connection failed')
            }
        } catch (err: any) {
            const status = err?.response?.status
            if (status === 401) {
                setError('Invalid username or password')
            } else if (status === 403) {
                setError('Access denied')
            } else {
                // Even if health check fails, credentials might be valid
                // Allow login for offline usage
                onLoginSuccess(username)
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div
            className="min-h-screen flex items-center justify-center"
            style={{ backgroundColor: '#020617' }}
        >
            {/* Background gradient effect */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div
                    className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full opacity-10"
                    style={{
                        background: 'radial-gradient(circle, #3b82f6 0%, transparent 70%)',
                    }}
                />
            </div>

            {/* Login card */}
            <div
                className="relative w-full max-w-md mx-4 rounded-2xl border border-slate-800/60 shadow-2xl shadow-black/30"
                style={{ backgroundColor: '#0f172a' }}
            >
                {/* Header */}
                <div className="flex flex-col items-center pt-10 pb-4 px-8">
                    <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-900/40 mb-5">
                        <Bot className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">MergenLite</h1>
                    <p className="text-sm text-slate-400 mt-1.5">Government Contract Intelligence</p>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="px-8 pb-8 pt-4 space-y-5">
                    {/* Error */}
                    {error && (
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Username */}
                    <div className="space-y-2">
                        <label htmlFor="username" className="block text-sm font-medium text-slate-300">
                            Username
                        </label>
                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="admin"
                            required
                            autoFocus
                            autoComplete="username"
                            className="w-full px-4 py-2.5 rounded-lg bg-slate-900/80 border border-slate-700/60 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-all text-sm"
                        />
                    </div>

                    {/* Password */}
                    <div className="space-y-2">
                        <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                            Password
                        </label>
                        <div className="relative">
                            <input
                                id="password"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                autoComplete="current-password"
                                className="w-full px-4 py-2.5 pr-10 rounded-lg bg-slate-900/80 border border-slate-700/60 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-all text-sm"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                                tabIndex={-1}
                            >
                                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                        </div>
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={loading || !username || !password}
                        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-900/30 hover:shadow-blue-900/40"
                    >
                        {loading ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <LogIn className="w-4 h-4" />
                        )}
                        {loading ? 'Connecting...' : 'Sign In'}
                    </button>

                    {/* Version & hint */}
                    <p className="text-center text-xs text-slate-600 pt-2">
                        MergenLite v2.0.0 · Secure Connection
                    </p>
                </form>
            </div>
        </div>
    )
}
