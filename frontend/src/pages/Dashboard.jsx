import React, { useState, useEffect, useCallback } from 'react';
import useDashboardData from '../hooks/useDashboardData';
import {
    AlertTriangle, DollarSign,
    RefreshCw, Server, Shield, Zap,
    Gift, CheckCircle, Clock, Lock
} from 'lucide-react';

import Header from '../components/common/Header';
import Card from '../components/common/Card';
import MetricsCard from '../components/dashboard/MetricsCard';
import Loading from '../components/common/Loading';
import EC2InstancesTable from '../components/dashboard/EC2InstancesTable';
import GuardDutyFindingsTable from '../components/dashboard/GuardDutyFindingsTable';
import apiClient from '../services/api';

// --- PERMISSION ERROR BANNER COMPONENT ---
const PermissionErrorBanner = ({ service, permissions, instructions }) => {
    return (
        <div className="mb-6 rounded-xl overflow-hidden border border-red-500/30 bg-gradient-to-r from-red-900/40 to-orange-900/40 backdrop-blur-sm animate-fade-in">
            <div className="p-4 border-b border-red-500/30 flex justify-between items-center bg-red-900/20">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-red-500 rounded-lg shadow-lg shadow-red-500/20">
                        <Lock className="text-white h-5 w-5" />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-white">Permission Required</h2>
                        <p className="text-red-300 text-xs">AWS {service} service access is required</p>
                    </div>
                </div>
                <div className="px-3 py-1 bg-red-500/20 border border-red-500 text-red-300 rounded-full text-xs font-bold flex items-center gap-2">
                    <AlertTriangle size={14} /> Access Denied
                </div>
            </div>

            <div className="p-5 space-y-4">
                <div className="flex items-start gap-3">
                    <AlertTriangle className="text-red-400 flex-shrink-0 mt-1" size={20} />
                    <div className="flex-1">
                        <h3 className="text-white font-semibold mb-2">What happened?</h3>
                        <p className="text-gray-300 text-sm leading-relaxed">
                            {instructions || `Your AWS account does not have permission to access the ${service} service.`}
                        </p>
                    </div>
                </div>

                {permissions && permissions.length > 0 && (
                    <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
                        <h4 className="text-white font-semibold text-sm mb-2">Required IAM Permissions:</h4>
                        <ul className="space-y-1">
                            {permissions.map((perm, index) => (
                                <li key={index} className="text-emerald-400 text-sm font-mono flex items-center gap-2">
                                    <span className="text-gray-500">•</span>
                                    {perm}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                    <h4 className="text-white font-semibold text-sm mb-2 flex items-center gap-2">
                        <span>🔧</span> How to fix this:
                    </h4>
                    <ol className="space-y-2 text-sm text-gray-300">
                        <li className="flex gap-2">
                            <span className="text-blue-400 font-bold">1.</span>
                            <span>Go to AWS IAM Console → Users → Select your IAM user</span>
                        </li>
                        <li className="flex gap-2">
                            <span className="text-blue-400 font-bold">2.</span>
                            <span>Click "Add permissions" → "Create inline policy"</span>
                        </li>
                        <li className="flex gap-2">
                            <span className="text-blue-400 font-bold">3.</span>
                            <span>Add the required permissions listed above</span>
                        </li>
                        <li className="flex gap-2">
                            <span className="text-blue-400 font-bold">4.</span>
                            <span>Refresh this dashboard</span>
                        </li>
                    </ol>
                    <a
                        href="https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_manage-attach-detach.html"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 mt-3 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                    >
                        View AWS IAM Documentation
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                    </a>
                </div>
            </div>
        </div>
    );
};

// --- FREE TIER BANNER COMPONENT ---
const FreeTierBanner = ({ data, loading }) => {
    if (loading || !data || !data.is_active || !data.offers || data.offers.length === 0) {
        return null;
    }

    return (
        <div className="mb-6 rounded-xl overflow-hidden border border-emerald-500/30 bg-gradient-to-r from-emerald-900/40 to-teal-900/40 backdrop-blur-sm animate-fade-in">
            <div className="p-4 border-b border-emerald-500/30 flex justify-between items-center bg-emerald-900/20">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-500 rounded-lg shadow-lg shadow-emerald-500/20">
                        <Gift className="text-white h-5 w-5" />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-white">AWS Free Tier Status</h2>
                        <p className="text-emerald-300 text-xs">Your account is currently using free tier benefits</p>
                    </div>
                </div>
                <div className="px-3 py-1 bg-emerald-500/20 border border-emerald-500 text-emerald-300 rounded-full text-xs font-bold flex items-center gap-2">
                    <CheckCircle size={14} /> Active
                </div>
            </div>

            <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {data.offers.map((offer, index) => {
                    let progressColor = "bg-emerald-500";
                    if (offer.percent_used > 80) progressColor = "bg-yellow-500";
                    if (offer.percent_used >= 100) progressColor = "bg-red-500";

                    return (
                        <div key={index} className="bg-gray-900/50 p-3 rounded-lg border border-gray-700 hover:border-emerald-500/50 transition-colors">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="text-sm font-bold text-white truncate pr-2" title={offer.service}>{offer.service}</h3>
                                <span className="text-[10px] bg-gray-700 px-2 py-0.5 rounded text-gray-300 whitespace-nowrap">{offer.type}</span>
                            </div>

                            <div className="flex justify-between text-xs mb-1">
                                <span className="text-gray-300">{offer.usage} / {offer.limit} {offer.unit}</span>
                                <span className={offer.percent_used >= 100 ? "text-red-400 font-bold" : "text-emerald-400"}>
                                    {offer.percent_used}%
                                </span>
                            </div>

                            <div className="w-full bg-gray-700 h-1.5 rounded-full overflow-hidden mb-2">
                                <div
                                    className={`h-full rounded-full ${progressColor} transition-all duration-500`}
                                    style={{ width: `${Math.min(offer.percent_used, 100)}%` }}
                                ></div>
                            </div>

                            <div className="text-xs text-gray-500 flex items-center gap-1">
                                <Clock size={10} />
                                <span>Remaining: <strong className="text-gray-300">{offer.remaining} {offer.unit}</strong></span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// LocalStorage keys
const STORAGE_KEYS = {
    AUTO_REFRESH: 'dashboard_autoRefresh',
    REFRESH_INTERVAL: 'dashboard_refreshInterval',
    DEFAULT_TIME_RANGE: 'dashboard_defaultTimeRange'
};

// Helper to format interval for display
const formatInterval = (seconds) => {
    if (seconds < 60) return `${seconds} seconds`;
    if (seconds === 60) return '1 minute';
    return `${seconds / 60} minutes`;
};

const AWSCloudHealthDashboard = () => {
    // Load default time range from localStorage
    const getDefaultTimeRange = () => {
        return localStorage.getItem(STORAGE_KEYS.DEFAULT_TIME_RANGE) || '24h';
    };

    const [selectedTimeRange, setSelectedTimeRange] = useState(getDefaultTimeRange);
    const [alertsExpanded, setAlertsExpanded] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    // Auto-refresh settings state
    const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
    const [refreshInterval, setRefreshInterval] = useState(300);
    const [nextRefreshIn, setNextRefreshIn] = useState(null);

    // Dashboard Data Hook
    const { data, loading, error, lastUpdated, refresh } = useDashboardData(selectedTimeRange);

    // Free Tier State
    const [billingData, setBillingData] = useState(null);
    const [billingLoading, setBillingLoading] = useState(true);

    // Function to fetch billing
    const fetchBilling = async () => {
        try {
            setBillingLoading(true);
            const res = await apiClient.get('/aws/billing');
            setBillingData(res.data);
        } catch (e) {
            console.error("Failed to fetch billing data", e);
        } finally {
            setBillingLoading(false);
        }
    };

    // Load auto-refresh settings from localStorage
    useEffect(() => {
        const loadSettings = () => {
            const autoRefresh = localStorage.getItem(STORAGE_KEYS.AUTO_REFRESH);
            const interval = localStorage.getItem(STORAGE_KEYS.REFRESH_INTERVAL);

            setAutoRefreshEnabled(autoRefresh !== null ? autoRefresh === 'true' : true);
            setRefreshInterval(interval !== null ? parseInt(interval) : 300);
        };

        loadSettings();
        fetchBilling();

        const handleStorageChange = (e) => {
            if (Object.values(STORAGE_KEYS).includes(e.key)) {
                loadSettings();
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, []);

    // Handle manual refresh
    const handleRefresh = useCallback(async () => {
        setRefreshing(true);
        await Promise.all([refresh(), fetchBilling()]);
        setRefreshing(false);
        setNextRefreshIn(refreshInterval);
    }, [refresh, refreshInterval]);

    // Auto-refresh effect
    useEffect(() => {
        if (!autoRefreshEnabled) {
            setNextRefreshIn(null);
            return;
        }

        setNextRefreshIn(refreshInterval);

        const countdownTimer = setInterval(() => {
            setNextRefreshIn(prev => {
                if (prev === null || prev <= 1) {
                    return refreshInterval;
                }
                return prev - 1;
            });
        }, 1000);

        const refreshTimer = setInterval(() => {
            refresh();
            fetchBilling();
        }, refreshInterval * 1000);

        return () => {
            clearInterval(countdownTimer);
            clearInterval(refreshTimer);
        };
    }, [autoRefreshEnabled, refreshInterval, refresh]);

    // Update time range in localStorage when changed
    const handleTimeRangeChange = (newRange) => {
        setSelectedTimeRange(newRange);
        localStorage.setItem(STORAGE_KEYS.DEFAULT_TIME_RANGE, newRange);
    };

    // Loading state
    if (loading && !data.ec2Summary) {
        return (
            <div className="min-h-screen">
                <Header
                    title="AWS Cloud Health Dashboard"
                    onRefresh={handleRefresh}
                    refreshing={refreshing}
                    selectedTimeRange={selectedTimeRange}
                    onTimeRangeChange={handleTimeRangeChange}
                />
                <main className="container mx-auto px-6 flex items-center justify-center min-h-96">
                    <Card className="p-8 text-center animate-fade-in">
                        <Loading size="lg" text="Loading dashboard data..." />
                        <p className="text-cosmic-txt-2 mt-4">
                            Scanning AWS resources across all regions...
                        </p>
                    </Card>
                </main>
            </div>
        );
    }

    // Error state
    if (error && !data.ec2Summary) {
        return (
            <div className="min-h-screen">
                <Header
                    title="AWS Cloud Health Dashboard"
                    onRefresh={handleRefresh}
                    refreshing={refreshing}
                    selectedTimeRange={selectedTimeRange}
                    onTimeRangeChange={handleTimeRangeChange}
                />
                <main className="container mx-auto px-6 flex items-center justify-center min-h-96">
                    <Card className="p-8 text-center max-w-md animate-scale-in">
                        <AlertTriangle size={48} className="mx-auto text-red-400 mb-4 animate-pulse" />
                        <h3 className="text-xl font-semibold text-cosmic-txt-1 mb-2">
                            Error Loading Dashboard
                        </h3>
                        <p className="text-cosmic-txt-2 mb-6">{error}</p>
                        <button onClick={handleRefresh} className="btn btn-primary px-12 py-3 flex items-center justify-center mx-auto">
                            <RefreshCw size={16} className="mr-2" />
                            Retry
                        </button>
                    </Card>
                </main>
            </div>
        );
    }

    const {
        ec2Summary,
        ec2Instances,
        ec2Cost,
        guarddutyStatus,
        guarddutyCritical,
        guarddutySummary,
        allFindings,
        serviceHealth
    } = data;

    // ✅ Check for EC2 permission error
    const hasEC2PermissionError = ec2Summary?.error === 'permission_denied';

    // Calculate EC2 metrics (with null checks for permission errors)
    const totalInstances = ec2Summary?.total_instances || 0;
    const runningInstances = ec2Summary?.by_state?.running || 0;
    const totalCost = ec2Cost?.total_estimated_cost || 0;
    const regionsActive = ec2Summary?.regions_with_instances || 0;

    // GuardDuty metrics calculations
    const criticalFindings = guarddutyCritical?.count || 0;
    const totalFindings = guarddutySummary?.total_findings || 0;
    const gdEnabled = guarddutyStatus?.enabled || false;
    const highSeverityCount = guarddutySummary?.by_severity?.HIGH || 0;

    const metricsData = [
        {
            title: 'EC2 Monthly Cost',
            value: `$${totalCost.toFixed(2)}`,
            change: `${runningInstances} running instances`,
            changeType: runningInstances > 0 ? 'positive' : 'neutral',
            icon: DollarSign,
            iconColor: '#3b82f6',
            iconBgColor: '#dbeafe'
        },
        {
            title: 'EC2 Instances',
            value: totalInstances,
            change: ec2Summary?.has_instances ? `${runningInstances} running` : 'No instances',
            changeType: ec2Summary?.has_instances ? 'positive' : 'neutral',
            icon: Server,
            iconColor: '#10b981',
            iconBgColor: '#d1fae5'
        },
        {
            title: 'Critical Findings',
            value: criticalFindings,
            change: criticalFindings > 0 ? 'Requires attention' : 'All clear',
            changeType: criticalFindings > 0 ? 'negative' : 'positive',
            icon: AlertTriangle,
            iconColor: '#ef4444',
            iconBgColor: '#fef2f2'
        },
        {
            title: 'Security Findings',
            value: totalFindings,
            change: `${highSeverityCount} high severity`,
            changeType: totalFindings > 10 ? 'warning' : 'neutral',
            icon: Shield,
            iconColor: '#8b5cf6',
            iconBgColor: '#ede9fe'
        },
        {
            title: 'Active Regions',
            value: regionsActive,
            change: 'with EC2 instances',
            changeType: 'positive',
            icon: Zap,
            iconColor: '#f59e0b',
            iconBgColor: '#fef3c7'
        }
    ];

    return (
        <div className="min-h-screen">
            <Header
                title="AWS Cloud Health Dashboard"
                onRefresh={handleRefresh}
                refreshing={refreshing}
                selectedTimeRange={selectedTimeRange}
                onTimeRangeChange={handleTimeRangeChange}
            />

            <main className="container mx-auto px-3 sm:px-6 py-4 sm:py-8 space-y-4 sm:space-y-6">
                {/* Status Banner */}
                <div className="mb-4 sm:mb-6 animate-fade-in">
                    <div className="flex items-center justify-center">
                        <div className="inline-flex items-center flex-wrap justify-center gap-2 sm:gap-3 text-xs sm:text-sm text-cosmic-secondary bg-cosmic-card px-3 sm:px-6 py-2 sm:py-3 rounded-full border border-cosmic-border backdrop-blur-sm shadow-lg">
                            <div className={`w-2 h-2 rounded-full ${autoRefreshEnabled ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                            <span>Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Never'}</span>
                            <span className="text-cosmic-muted">•</span>
                            {autoRefreshEnabled ? (
                                <>
                                    <span>Auto-refresh: {formatInterval(refreshInterval)}</span>
                                    {nextRefreshIn !== null && (
                                        <>
                                            <span className="text-cosmic-muted">•</span>
                                            <span className="text-blue-400">
                                                Next: {nextRefreshIn}s
                                            </span>
                                        </>
                                    )}
                                </>
                            ) : (
                                <span className="text-yellow-400">Auto-refresh: Off</span>
                            )}
                        </div>
                    </div>
                </div>

                {/* ✅ EC2 Permission Error Banner (shown BEFORE Free Tier) */}
                {hasEC2PermissionError && (
                    <PermissionErrorBanner
                        service={ec2Summary.service}
                        permissions={ec2Summary.required_permissions}
                        instructions={ec2Summary.instructions}
                    />
                )}

                {/* Free Tier Banner */}
                <FreeTierBanner data={billingData} loading={billingLoading} />

                {/* Top Section: Metrics Cards */}
                <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-6">
                    {metricsData.map((metric, index) => (
                        <MetricsCard
                            key={index}
                            {...metric}
                            className="animate-slide-up"
                            style={{ animationDelay: `${index * 0.1}s` }}
                        />
                    ))}
                </section>

                {/* GuardDuty Security Overview Section */}
                <section className="mb-6">
                    <Card className="p-6 animate-slide-up">
                        <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                            <Shield size={20} className="mr-2 text-purple-400" />
                            GuardDuty Security Overview
                        </h3>

                        {guarddutyStatus === null ? (
                            <div className="text-center py-8 text-cosmic-txt-2">
                                <AlertTriangle size={48} className="mx-auto mb-2 opacity-50" />
                                <p>GuardDuty data unavailable</p>
                                <p className="text-xs mt-2">Make sure GuardDuty is enabled in your AWS account</p>
                            </div>
                        ) : (
                            <>
                                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4 mb-4">
                                    <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm text-cosmic-txt-2">Status</span>
                                            <div className={`w-3 h-3 rounded-full ${gdEnabled ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                                        </div>
                                        <p className="text-2xl font-bold text-cosmic-txt-1">
                                            {gdEnabled ? 'Enabled' : 'Disabled'}
                                        </p>
                                    </div>

                                    <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-red-500/30">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm text-cosmic-txt-2">Critical</span>
                                            <AlertTriangle size={16} className="text-red-400" />
                                        </div>
                                        <p className="text-2xl font-bold text-red-400">
                                            {criticalFindings}
                                        </p>
                                        <p className="text-xs text-cosmic-txt-2 mt-1">Findings</p>
                                    </div>

                                    <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm text-cosmic-txt-2">Total</span>
                                            <Shield size={16} className="text-purple-400" />
                                        </div>
                                        <p className="text-2xl font-bold text-cosmic-txt-1">
                                            {totalFindings}
                                        </p>
                                        <p className="text-xs text-cosmic-txt-2 mt-1">All severities</p>
                                    </div>
                                </div>

                                {guarddutySummary?.by_severity && (
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                        <div className="text-center p-3 bg-red-500/10 rounded-lg border border-red-500/30">
                                            <p className="text-sm text-cosmic-txt-2 mb-1">Critical</p>
                                            <p className="text-xl font-bold text-red-400">
                                                {guarddutySummary.by_severity.CRITICAL || 0}
                                            </p>
                                        </div>
                                        <div className="text-center p-3 bg-orange-500/10 rounded-lg border border-orange-500/30">
                                            <p className="text-sm text-cosmic-txt-2 mb-1">High</p>
                                            <p className="text-xl font-bold text-orange-400">
                                                {guarddutySummary.by_severity.HIGH || 0}
                                            </p>
                                        </div>
                                        <div className="text-center p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
                                            <p className="text-sm text-cosmic-txt-2 mb-1">Medium</p>
                                            <p className="text-xl font-bold text-yellow-400">
                                                {guarddutySummary.by_severity.MEDIUM || 0}
                                            </p>
                                        </div>
                                        <div className="text-center p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
                                            <p className="text-sm text-cosmic-txt-2 mb-1">Low</p>
                                            <p className="text-xl font-bold text-blue-400">
                                                {guarddutySummary.by_severity.LOW || 0}
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </Card>
                </section>

                {/* EC2 Instances Table Section */}
                <section className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
                    <EC2InstancesTable
                        instances={hasEC2PermissionError ? [] : (ec2Instances || [])}
                        loading={loading}
                        permissionError={hasEC2PermissionError}
                    />
                </section>

                {/* GuardDuty Findings Table Section */}
                <section className="animate-slide-up" style={{ animationDelay: '0.3s' }}>
                    <GuardDutyFindingsTable
                        findings={allFindings || []}
                        loading={loading}
                    />
                </section>
            </main>
        </div>
    );
};

export default AWSCloudHealthDashboard;