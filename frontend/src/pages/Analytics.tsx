import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, Users, Calendar, RefreshCw } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import { useAuth } from '../contexts/AuthContext';

interface AnalyticsData {
    dailyCalls: { date: string; count: number; completed: number; failed: number }[];
    outcomeDistribution: {
        interested: number;
        notInterested: number;
        noAnswer: number;
        other: number;
    };
    hourlyBreakdown: { hour: number; count: number }[];
    averageDuration: number;
    successRate: number;
    totalCalls: number;
    completedCalls: number;
    dateRange: { start: string; end: string; days: number };
}

type DateRange = 7 | 30 | 90;

export default function Analytics() {
    const { userId } = useAuth();
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [dateRange, setDateRange] = useState<DateRange>(7);

    useEffect(() => {
        if (userId) {
            fetchAnalytics();
        }
    }, [userId, dateRange]);

    async function fetchAnalytics() {
        try {
            setLoading(true);
            const response = await fetch(`/api/analytics?days=${dateRange}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
                }
            });

            if (response.ok) {
                const result = await response.json();
                setData(result);
            }
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
        } finally {
            setLoading(false);
        }
    }

    // Get max value for chart scaling
    const maxDailyCount = data?.dailyCalls.reduce((max, d) => Math.max(max, d.count), 0) || 1;
    const maxHourlyCount = data?.hourlyBreakdown.reduce((max, d) => Math.max(max, d.count), 0) || 1;

    // Calculate outcome totals
    const totalOutcomes = data ?
        data.outcomeDistribution.interested +
        data.outcomeDistribution.notInterested +
        data.outcomeDistribution.noAnswer +
        data.outcomeDistribution.other : 0;

    const getOutcomePercentage = (value: number) =>
        totalOutcomes > 0 ? Math.round((value / totalOutcomes) * 100) : 0;

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-text">Analytics</h1>
                        <p className="text-gray-600 mt-1">Track your call performance and trends</p>
                    </div>
                    <div className="flex items-center gap-4">
                        {/* Date Range Selector */}
                        <div className="flex bg-gray-100 rounded-lg p-1">
                            {([7, 30, 90] as DateRange[]).map((days) => (
                                <button
                                    key={days}
                                    onClick={() => setDateRange(days)}
                                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${dateRange === days
                                        ? 'bg-white text-blue-600 shadow-sm'
                                        : 'text-gray-600 hover:text-gray-900'
                                        }`}
                                >
                                    {days}D
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={fetchAnalytics}
                            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                            title="Refresh"
                        >
                            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Total Calls</p>
                                <p className="text-3xl font-bold text-gray-900 mt-2">
                                    {loading ? '—' : data?.totalCalls || 0}
                                </p>
                            </div>
                            <div className="p-3 bg-blue-100 rounded-full text-blue-600">
                                <BarChart3 className="w-6 h-6" />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                                <p className="text-3xl font-bold text-gray-900 mt-2">
                                    {loading ? '—' : `${data?.successRate || 0}%`}
                                </p>
                            </div>
                            <div className="p-3 bg-green-100 rounded-full text-green-600">
                                <TrendingUp className="w-6 h-6" />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Avg Duration</p>
                                <p className="text-3xl font-bold text-gray-900 mt-2">
                                    {loading ? '—' : `${Math.round(data?.averageDuration || 0)}s`}
                                </p>
                            </div>
                            <div className="p-3 bg-purple-100 rounded-full text-purple-600">
                                <Clock className="w-6 h-6" />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Interested</p>
                                <p className="text-3xl font-bold text-gray-900 mt-2">
                                    {loading ? '—' : data?.outcomeDistribution.interested || 0}
                                </p>
                            </div>
                            <div className="p-3 bg-indigo-100 rounded-full text-indigo-600">
                                <Users className="w-6 h-6" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Daily Calls Chart */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <Calendar className="w-5 h-5 text-blue-600" />
                            Daily Call Volume
                        </h3>
                        {loading ? (
                            <div className="h-48 flex items-center justify-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                            </div>
                        ) : (
                            <div className="h-48 flex items-end gap-1">
                                {data?.dailyCalls.slice(-14).map((day, idx) => (
                                    <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                                        <div
                                            className="w-full bg-blue-500 rounded-t hover:bg-blue-600 transition-colors cursor-pointer"
                                            style={{ height: `${(day.count / maxDailyCount) * 100}%`, minHeight: day.count > 0 ? '4px' : '0' }}
                                            title={`${day.date}: ${day.count} calls`}
                                        />
                                        <span className="text-xs text-gray-500 transform -rotate-45 origin-left">
                                            {new Date(day.date).getDate()}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                        {!loading && data?.dailyCalls.length === 0 && (
                            <div className="h-48 flex items-center justify-center text-gray-500">
                                No data for this period
                            </div>
                        )}
                    </div>

                    {/* Outcome Distribution */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <Users className="w-5 h-5 text-green-600" />
                            Outcome Distribution
                        </h3>
                        {loading ? (
                            <div className="h-48 flex items-center justify-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                            </div>
                        ) : totalOutcomes > 0 ? (
                            <div className="space-y-4">
                                {/* Interested */}
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-gray-600">Interested</span>
                                        <span className="font-medium">{data?.outcomeDistribution.interested} ({getOutcomePercentage(data?.outcomeDistribution.interested ?? 0)}%)</span>
                                    </div>
                                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-green-500 rounded-full transition-all"
                                            style={{ width: `${getOutcomePercentage(data?.outcomeDistribution.interested ?? 0)}%` }}
                                        />
                                    </div>
                                </div>

                                {/* Not Interested */}
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-gray-600">Not Interested</span>
                                        <span className="font-medium">{data?.outcomeDistribution.notInterested} ({getOutcomePercentage(data?.outcomeDistribution.notInterested ?? 0)}%)</span>
                                    </div>
                                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-red-500 rounded-full transition-all"
                                            style={{ width: `${getOutcomePercentage(data?.outcomeDistribution.notInterested ?? 0)}%` }}
                                        />
                                    </div>
                                </div>

                                {/* No Answer */}
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-gray-600">No Answer</span>
                                        <span className="font-medium">{data?.outcomeDistribution.noAnswer} ({getOutcomePercentage(data?.outcomeDistribution.noAnswer ?? 0)}%)</span>
                                    </div>
                                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-yellow-500 rounded-full transition-all"
                                            style={{ width: `${getOutcomePercentage(data?.outcomeDistribution.noAnswer ?? 0)}%` }}
                                        />
                                    </div>
                                </div>

                                {/* Other */}
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-gray-600">Other</span>
                                        <span className="font-medium">{data?.outcomeDistribution.other} ({getOutcomePercentage(data?.outcomeDistribution.other ?? 0)}%)</span>
                                    </div>
                                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gray-400 rounded-full transition-all"
                                            style={{ width: `${getOutcomePercentage(data?.outcomeDistribution.other ?? 0)}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="h-48 flex items-center justify-center text-gray-500">
                                No outcome data yet
                            </div>
                        )}
                    </div>
                </div>

                {/* Hourly Breakdown */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <Clock className="w-5 h-5 text-purple-600" />
                        Best Times to Call
                    </h3>
                    {loading ? (
                        <div className="h-32 flex items-center justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                        </div>
                    ) : (
                        <div className="h-32 flex items-end gap-1">
                            {data?.hourlyBreakdown.map((hour, idx) => (
                                <div key={idx} className="flex-1 flex flex-col items-center">
                                    <div
                                        className={`w-full rounded-t transition-colors cursor-pointer ${hour.count === maxHourlyCount && maxHourlyCount > 0
                                            ? 'bg-purple-600'
                                            : 'bg-purple-300 hover:bg-purple-400'
                                            }`}
                                        style={{ height: `${(hour.count / maxHourlyCount) * 100}%`, minHeight: hour.count > 0 ? '4px' : '0' }}
                                        title={`${hour.hour}:00 - ${hour.count} calls`}
                                    />
                                    {idx % 3 === 0 && (
                                        <span className="text-xs text-gray-500 mt-1">{hour.hour}</span>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                    <p className="text-sm text-gray-500 mt-2 text-center">
                        Hours shown in 24-hour format. Peak hours are highlighted.
                    </p>
                </div>
            </div>
        </DashboardLayout>
    );
}
