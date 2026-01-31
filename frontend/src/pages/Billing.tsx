import React, { useEffect, useState } from 'react';
import { CreditCard, Check, Zap, AlertTriangle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import DashboardLayout from '../components/dashboard/DashboardLayout';

interface UsageStats {
    total_calls: number;
    total_minutes: number;
    period: string;
}

interface PlanLimits {
    max_calls: number;
    max_minutes: number;
}

interface PlanInfo {
    name: string;
    limits: PlanLimits;
    features: string[];
}

const Billing = () => {
    const { user } = useAuth();
    const [usage, setUsage] = useState<UsageStats>({ total_calls: 0, total_minutes: 0, period: 'all_time' });
    const [plan, setPlan] = useState<PlanInfo>({
        name: 'Free',
        limits: { max_calls: 50, max_minutes: 200 },
        features: []
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchUsage();
    }, []);

    const fetchUsage = async () => {
        try {
            const response = await fetch('/api/usage', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                setUsage(data.usage);
                setPlan(data.plan);
            }
        } catch (error) {
            console.error('Failed to fetch usage:', error);
        } finally {
            setLoading(false);
        }
    };

    const calculatePercentage = (current: number, max: number) => {
        return Math.min(100, Math.round((current / max) * 100));
    };

    if (loading) {
        return (
            <DashboardLayout>
                <div className="p-8 text-center text-gray-400">Loading plan details...</div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-2xl font-bold text-text">Billing & Usage</h1>
                    <p className="text-text-secondary">Manage your subscription and track your usage</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Usage Card */}
                    <div className="bg-surface rounded-xl border border-border p-6 shadow-sm">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="p-2 bg-primary/10 rounded-lg">
                                <Zap className="w-5 h-5 text-primary" />
                            </div>
                            <h2 className="text-lg font-semibold text-text">Current Usage</h2>
                        </div>

                        <div className="space-y-6">
                            {/* Calls Usage */}
                            <div>
                                <div className="flex justify-between text-sm mb-2">
                                    <span className="text-text-secondary">Monthly Calls</span>
                                    <span className="text-text font-medium">
                                        {usage.total_calls} / {plan.limits.max_calls}
                                    </span>
                                </div>
                                <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full transition-all duration-500 ${calculatePercentage(usage.total_calls, plan.limits.max_calls) > 90
                                            ? 'bg-red-500'
                                            : 'bg-primary'
                                            }`}
                                        style={{ width: `${calculatePercentage(usage.total_calls, plan.limits.max_calls)}%` }}
                                    />
                                </div>
                            </div>

                            {/* Minutes Usage */}
                            <div>
                                <div className="flex justify-between text-sm mb-2">
                                    <span className="text-text-secondary">Minutes Used</span>
                                    <span className="text-text font-medium">
                                        {usage.total_minutes} / {plan.limits.max_minutes} mins
                                    </span>
                                </div>
                                <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500 rounded-full transition-all duration-500"
                                        style={{ width: `${calculatePercentage(usage.total_minutes, plan.limits.max_minutes)}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Current Plan Card */}
                    <div className="bg-surface rounded-xl border border-border p-6 shadow-sm relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-16 -mt-16 pointer-events-none" />

                        <div className="flex justify-between items-start mb-6">
                            <div className="flex items-center space-x-3">
                                <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                                    <CreditCard className="w-5 h-5 text-text" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-semibold text-text">Current Plan</h2>
                                    <p className="text-sm text-primary font-medium">{plan.name} Tier</p>
                                </div>
                            </div>
                            <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                                Active
                            </span>
                        </div>

                        <div className="space-y-3 mb-6">
                            {plan.features.map((feature, idx) => (
                                <div key={idx} className="flex items-center text-sm text-text-secondary">
                                    <Check className="w-4 h-4 text-primary mr-2" />
                                    {feature}
                                </div>
                            ))}
                        </div>

                        <button className="w-full py-2 px-4 bg-text text-bg rounded-lg hover:bg-gray-800 transition-colors font-medium">
                            Upgrade Plan
                        </button>
                    </div>
                </div>

                {/* Upgrade Banner */}
                <div className="bg-gradient-to-r from-primary/10 to-primary/5 border border-primary/20 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-primary/20 rounded-full text-primary">
                            <Zap className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-text">Unlock Pro Features</h3>
                            <p className="text-text-secondary text-sm">Get 1000 calls per month, advanced analytics, and priority support.</p>
                        </div>
                    </div>
                    <button className="px-6 py-2 bg-primary text-white hover:bg-primary-dark rounded-lg font-medium transition-colors shadow-sm whitespace-nowrap">
                        Upgrade to Pro
                    </button>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default Billing;
