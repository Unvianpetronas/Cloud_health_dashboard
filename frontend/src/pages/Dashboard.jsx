import React, { useState, useEffect, useCallback } from 'react';
import useDashboardData from '../hooks/useDashboardData';
import {
    AlertTriangle, DollarSign,
    RefreshCw, Server, Shield, Zap,
} from 'lucide-react';

import Header from '../components/common/Header';
import Card from '../components/common/Card';
import MetricsCard from '../components/dashboard/MetricsCard';
import Loading from '../components/common/Loading';
import EC2InstancesTable from '../components/dashboard/EC2InstancesTable';
import GuardDutyFindingsTable from '../components/dashboard/GuardDutyFindingsTable';

// LocalStorage keys (same as Settings page)
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
    const [refreshInterval, setRefreshInterval] = useState(300); // seconds
    const [nextRefreshIn, setNextRefreshIn] = useState(null);

    const { data, loading, error, lastUpdated, refresh } = useDashboardData(selectedTimeRange);

    // Load auto-refresh settings from localStorage
    useEffect(() => {
        const loadSettings = () => {
            const autoRefresh = localStorage.getItem(STORAGE_KEYS.AUTO_REFRESH);
            const interval = localStorage.getItem(STORAGE_KEYS.REFRESH_INTERVAL);

            setAutoRefreshEnabled(autoRefresh !== null ? autoRefresh === 'true' : true);
            setRefreshInterval(interval !== null ? parseInt(interval) : 300);
        };

        loadSettings();

        // Listen for storage changes (if user changes settings in another tab)
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
        await refresh();
        setRefreshing(false);
        setNextRefreshIn(refreshInterval); // Reset countdown after manual refresh
    }, [refresh, refreshInterval]);

    // Auto-refresh effect
    useEffect(() => {
        if (!autoRefreshEnabled) {
            setNextRefreshIn(null);
            return;
        }

        // Initialize countdown
        setNextRefreshIn(refreshInterval);

        // Countdown timer (updates every second)
        const countdownTimer = setInterval(() => {
            setNextRefreshIn(prev => {
                if (prev === null || prev <= 1) {
                    return refreshInterval;
                }
                return prev - 1;
            });
        }, 1000);

        // Actual refresh timer
        const refreshTimer = setInterval(() => {
            refresh();
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

    // ✅ Custom label renderer for pie chart
    const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }) => {
        const RADIAN = Math.PI / 180;
        const radius = outerRadius + 35;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);
        const textAnchor = x > cx ? 'start' : 'end';

        return (
            <text
                x={x}
                y={y}
                fill="#e6e9f5"
                textAnchor={textAnchor}
                dominantBaseline="central"
                style={{
                    fontSize: '13px',
                    fontWeight: '500',
                    textShadow: '0 2px 4px rgba(0,0,0,0.5)'
                }}
            >
                {`${name} ${(percent * 100).toFixed(0)}%`}
            </text>
        );
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
                        <button onClick={handleRefresh} className="btn btn-primary">
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

    // Calculate EC2 metrics
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

            <main className="container mx-auto px-6 py-8 space-y-6">
                {/* Status Banner - Updated with dynamic auto-refresh info */}
                <div className="mb-6 animate-fade-in">
                    <div className="flex items-center justify-center">
                        <div className="inline-flex items-center space-x-3 text-sm text-cosmic-secondary bg-cosmic-card px-6 py-3 rounded-full border border-cosmic-border backdrop-blur-sm shadow-lg">
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

                {/* Top Section: Metrics Cards */}
                <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
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
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
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
                        instances={ec2Instances || []}
                        loading={loading}
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
