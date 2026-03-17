import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Zap, DollarSign, Database, TrendingUp, Clock } from 'lucide-react';
import ApiService from '../services/api';

const SystemHealthPage = () => {
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const data = await ApiService.getAnalyticsSummary();
                setMetrics(data);
            } catch (err) {
                console.error("Failed to fetch analytics:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchMetrics();
        const interval = setInterval(fetchMetrics, 5000); // 5s refresh
        return () => clearInterval(interval);
    }, []);

    if (loading && !metrics) {
        return <div className="min-h-screen pt-32 text-center text-teal-500 font-bold">LOADING SYSTEM DATA...</div>;
    }

    // Default to some 0s if no data
    const safeMetrics = metrics || {};
    const faithfulness = safeMetrics.faithfulness_pct ?? 100;
    const p90_latency = safeMetrics.p90_latency_s ?? 0.0;
    const relevance = safeMetrics.relevance_pct ?? 100;
    const mistake_rate = (100 - relevance).toFixed(1);
    const cost_per_session = safeMetrics.cost_per_session_usd ?? 0.0;
    const daily_spend = safeMetrics.total_cost_usd ?? 0.0;
    const total_tokens = safeMetrics.total_tokens ?? 0;
    
    // Efficiency: (tokens out) / (tokens in) — dummy proxy for output saturation
    const token_efficiency = safeMetrics.total_tokens_in > 0 
        ? (safeMetrics.total_tokens_out / safeMetrics.total_tokens_in).toFixed(2) 
        : 0;

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8 bg-[#0a0a0a]">
            <div className="max-w-7xl mx-auto">
                <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div>
                        <h1 className="text-4xl font-black tracking-tight text-white mb-2">
                            System Monitoring <span className="text-teal-500">Dashboard</span>
                        </h1>
                        <p className="text-gray-400 max-w-2xl">
                            Real-time observability layer for OTT Scout. Tracking AI accuracy, performance bottlenecks, and resource efficiency.
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="px-3 py-1 bg-green-500/10 border border-green-500/20 text-green-500 rounded-full text-xs font-bold flex items-center gap-2">
                            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                            SYSTEM OPERATIONAL
                        </div>
                        <div className="px-3 py-1 bg-white/5 border border-white/10 text-gray-400 rounded-full text-xs font-bold">
                            LAST UPDATED: JUST NOW
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <MetricCard 
                        title="Faithfulness Score" 
                        value={`${faithfulness}%`} 
                        subtext="Hallucination-free recommendations"
                        icon={<ShieldCheck className="text-teal-500" />}
                        trend={metrics?.total_requests ? `${metrics.total_requests} evaluated` : 'No data'}
                    />
                    <MetricCard 
                        title="P90 Latency" 
                        value={`${p90_latency}s`} 
                        subtext="Average recommendation time"
                        icon={<Zap className="text-yellow-500" />}
                        trend="Real-time execution"
                        isWarning={p90_latency > 2.0}
                    />
                    <MetricCard 
                        title="Cost / User Session" 
                        value={`$${cost_per_session}`} 
                        subtext="SaaS viability threshold: $0.10"
                        icon={<DollarSign className="text-blue-500" />}
                        trend="Based on 70b Groq pricing"
                    />
                    <MetricCard 
                        title="Mistake Rate" 
                        value={`${mistake_rate}%`} 
                        subtext="Thematic matching accuracy"
                        icon={<Activity className="text-red-500" />}
                        trend="LLM-as-a-Judge (Relevancy)"
                        isWarning={mistake_rate > 10}
                    />
                </div>

                {/* Secondary Metrics / Charts Area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Token Efficiency */}
                    <div className="lg:col-span-2 bg-[#141414] border border-white/5 rounded-3xl p-8">
                        <div className="flex items-center justify-between mb-8">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <TrendingUp size={20} className="text-teal-500" />
                                    Model Performance Trends
                                </h3>
                                <p className="text-sm text-gray-500">Input vs Output token efficiency (Last 24h)</p>
                            </div>
                            <div className="flex gap-2">
                                <span className="px-3 py-1 bg-white/5 text-gray-400 text-[10px] font-black rounded-lg">GROQ</span>
                                <span className="px-3 py-1 bg-white/5 text-gray-400 text-[10px] font-black rounded-lg">LLAMA-3.3</span>
                            </div>
                        </div>

                        {/* Visualization of steps */}
                        <div className="space-y-6">
                            {safeMetrics.pipeline_steps?.map((step, idx) => (
                                <StepMetric 
                                    key={idx}
                                    name={step.name} 
                                    time={`${step.time_ms}ms`} 
                                    status={step.status} 
                                    progress={step.progress} 
                                    isWarning={step.is_bottleneck} 
                                />
                            ))}
                            {(!safeMetrics.pipeline_steps || safeMetrics.pipeline_steps.length === 0) && (
                                <p className="text-gray-500 text-sm">No recent pipeline data to visualize.</p>
                            )}
                        </div>

                        <div className="mt-8 pt-8 border-t border-white/5 grid grid-cols-3 gap-4 text-center">
                            <div>
                                <p className="text-2xl font-black text-white">${daily_spend}</p>
                                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Total Spend</p>
                            </div>
                            <div>
                                <p className="text-2xl font-black text-white">{total_tokens}</p>
                                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Total Tokens</p>
                            </div>
                            <div>
                                <p className="text-2xl font-black text-white">{token_efficiency}</p>
                                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Efficiency ID</p>
                            </div>
                        </div>
                    </div>

                    {/* AI Traces Sidebar */}
                    <div className="bg-[#141414] border border-white/5 rounded-3xl p-8">
                        <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-6">
                            <Clock size={20} className="text-teal-500" />
                            Live Traces
                        </h3>
                        <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                            {safeMetrics.recent_traces?.map(trace => (
                                <TraceItem 
                                    key={trace.id}
                                    id={trace.id} 
                                    query={trace.query} 
                                    status={trace.status === 'ok' ? '200 OK' : 'ERROR'} 
                                    latency={`${trace.latency_s}s`} 
                                    score={trace.relevance !== null ? `${Math.round(trace.relevance * 100)}% Match` : 'N/A'} 
                                    warning={trace.status !== 'ok'}
                                />
                            ))}
                            {(!safeMetrics.recent_traces || safeMetrics.recent_traces.length === 0) && (
                                <p className="text-gray-500 text-sm">Waiting for incoming requests...</p>
                            )}
                        </div>
                        <button 
                            onClick={() => window.open('https://cloud.langfuse.com/project/cmmu985wg044zad08l2v1s4f7', '_blank')}
                            className="w-full mt-8 py-3 bg-white/5 hover:bg-white/10 text-white text-sm font-bold rounded-2xl transition-all border border-white/5"
                        >
                            VIEW FULL LOGS ON LANGFUSE
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const MetricCard = ({ title, value, subtext, icon, trend, isWarning }) => (
    <div className={`p-6 rounded-3xl border transition-all duration-300 ${isWarning ? 'bg-red-500/5 border-red-500/20' : 'bg-[#141414] border-white/5 hover:border-teal-500/30'}`}>
        <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-white/5 rounded-2xl">{icon}</div>
            <div className="text-[10px] font-bold p-1 px-2 bg-white/5 text-gray-500 rounded-lg">{trend}</div>
        </div>
        <h4 className="text-gray-500 text-xs font-bold uppercase tracking-widest mb-1">{title}</h4>
        <p className="text-3xl font-black text-white mb-2">{value}</p>
        <p className="text-[10px] text-gray-500 font-medium">{subtext}</p>
    </div>
);

const StepMetric = ({ name, time, status, progress, isWarning }) => (
    <div>
        <div className="flex items-center justify-between mb-2">
            <div>
                <span className="text-sm font-bold text-gray-300">{name}</span>
                <span className={`ml-3 text-[10px] font-black uppercase px-2 py-0.5 rounded ${isWarning ? 'bg-yellow-500/10 text-yellow-500' : 'bg-green-500/10 text-green-500'}`}>
                    {status}
                </span>
            </div>
            <span className="text-sm font-black text-white">{time}</span>
        </div>
        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
            <div 
                className={`h-full rounded-full transition-all duration-1000 ${isWarning ? 'bg-yellow-500' : 'bg-teal-500'}`}
                style={{ width: `${progress}%` }}
            ></div>
        </div>
    </div>
);

const TraceItem = ({ id, query, status, latency, score, warning }) => (
    <div className="p-4 bg-white/5 border border-white/5 rounded-2xl hover:bg-white/10 transition-all cursor-pointer">
        <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-mono text-teal-500">{id}</span>
            <span className={`text-[10px] font-black ${warning ? 'text-yellow-500' : 'text-green-500'}`}>{status}</span>
        </div>
        <p className="text-sm font-bold text-gray-200 truncate mb-2">"{query}"</p>
        <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-gray-500 uppercase">LATENCY: {latency}</span>
            <span className="text-[10px] font-bold text-gray-500 uppercase">SCORE: {score}</span>
        </div>
    </div>
);

export default SystemHealthPage;
