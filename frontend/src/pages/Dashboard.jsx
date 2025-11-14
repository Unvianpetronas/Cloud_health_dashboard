import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import useDashboardData from '../hooks/useDashboardData';
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
    Activity, AlertTriangle, CheckCircle, Cloud, DollarSign,
    Monitor, RefreshCw, Server, Shield, Zap, TrendingUp,
    ChevronDown, ChevronUp, Database, ArrowRight
} from 'lucide-react';

import Header from '../components/common/Header';
import Card from '../components/common/Card';
import MetricsCard from '../components/dashboard/MetricsCard';
import Loading from '../components/common/Loading';
import EC2InstancesTable from '../components/dashboard/EC2InstancesTable';
import GuardDutyFindingsTable from '../components/dashboard/GuardDutyFindingsTable';

const AWSCloudHealthDashboard = () => {
    const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
    const [alertsExpanded, setAlertsExpanded] = useState(true);
    const [performanceExpanded, setPerformanceExpanded] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const { data, loading, error, lastUpdated, refresh } = useDashboardData(selectedTimeRange);

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

    const handleRefresh = async () => {
        setRefreshing(true);
        await refresh();
        setRefreshing(false);
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
                    onTimeRangeChange={setSelectedTimeRange}
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
                    onTimeRangeChange={setSelectedTimeRange}
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

    // 🆕 UPDATED: Added GuardDuty data destructuring
    const {
        ec2Summary,
        ec2Instances,  // NEW: All EC2 instances for table
        ec2Cost,
        guarddutyStatus,
        guarddutyCritical,
        guarddutySummary,
        allFindings,  // NEW: All GuardDuty findings for table
        performance,
        serviceHealth,
        alerts,
        serviceStatus
    } = data;

    // Calculate EC2 metrics
    const totalInstances = ec2Summary?.total_instances || 0;
    const runningInstances = ec2Summary?.by_state?.running || 0;
    const totalCost = ec2Cost?.total_estimated_cost || 0;
    const regionsActive = ec2Summary?.regions_with_instances || 0;

    // 🆕 NEW: GuardDuty metrics calculations
    const criticalFindings = guarddutyCritical?.count || 0;
    const totalFindings = guarddutySummary?.total_findings || 0;
    const gdEnabled = guarddutyStatus?.enabled || false;
    const highSeverityCount = guarddutySummary?.by_severity?.HIGH || 0;

    // 🆕 UPDATED: Added GuardDuty metrics cards
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
        // 🆕 NEW: Critical Security Findings
        {
            title: 'Critical Findings',
            value: criticalFindings,
            change: criticalFindings > 0 ? 'Requires attention' : 'All clear',
            changeType: criticalFindings > 0 ? 'negative' : 'positive',
            icon: AlertTriangle,
            iconColor: '#ef4444',
            iconBgColor: '#fef2f2'
        },
        // 🆕 NEW: Total GuardDuty Findings
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

    // Helper functions for styling
    const getSeverityColor = (severity) => {
        switch (severity?.toLowerCase()) {
            case 'critical': return '#ef4444';
            case 'high': return '#f97316';
            case 'warning': return '#f59e0b';
            case 'medium': return '#eab308';
            case 'low': return '#3b82f6';
            case 'info': return '#06b6d4';
            default: return '#6b7280';
        }
    };

    const getSeverityBg = (severity) => {
        switch (severity?.toLowerCase()) {
            case 'critical': return 'rgba(239, 68, 68, 0.1)';
            case 'high': return 'rgba(249, 115, 22, 0.1)';
            case 'warning': return 'rgba(245, 158, 11, 0.1)';
            case 'medium': return 'rgba(234, 179, 8, 0.1)';
            case 'low': return 'rgba(59, 130, 246, 0.1)';
            case 'info': return 'rgba(6, 182, 212, 0.1)';
            default: return 'rgba(107, 114, 128, 0.1)';
        }
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'healthy': return '#10b981';
            case 'warning': return '#f59e0b';
            case 'critical': return '#ef4444';
            case 'unknown': return '#6b7280';
            default: return '#6b7280';
        }
    };

    const getStatusIcon = (status) => {
        switch (status?.toLowerCase()) {
            case 'healthy': return <CheckCircle size={20} />;
            case 'warning': return <AlertTriangle size={20} />;
            case 'critical': return <AlertTriangle size={20} />;
            default: return <Monitor size={20} />;
        }
    };

    return (
        <div className="min-h-screen">
            <Header
                title="AWS Cloud Health Dashboard"
                onRefresh={handleRefresh}
                refreshing={refreshing}
                selectedTimeRange={selectedTimeRange}
                onTimeRangeChange={setSelectedTimeRange}
            />

            <main className="container mx-auto px-6 py-8 space-y-6">
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

                {/* Services Quick Access */}
                <section className="animate-slide-up" style={{animationDelay: '0.5s'}}>
                    <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                        <Cloud size={20} className="mr-2 text-blue-400" />
                        AWS Services
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Architecture Analysis Card */}
                        <Link to="/architecture">
                            <Card className="p-6 hover:scale-105 transition-all cursor-pointer border-2 border-transparent hover:border-blue-500">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center shadow-cosmic-glow">
                                        <Shield className="h-6 w-6 text-white" />
                                    </div>
                                    <ArrowRight className="h-5 w-5 text-cosmic-txt-2" />
                                </div>
                                <h4 className="text-lg font-semibold text-cosmic-txt-1 mb-2">Architecture Analysis</h4>
                                <p className="text-sm text-cosmic-txt-2 mb-3">
                                    AWS Well-Architected Framework assessment with recommendations
                                </p>
                                <div className="flex items-center space-x-2">
                                    <div className="bg-blue-500/20 px-3 py-1 rounded-lg text-xs text-blue-400 font-semibold">
                                        View Report
                                    </div>
                                </div>
                            </Card>
                        </Link>

                        {/* S3 Buckets Card */}
                        <Link to="/s3">
                            <Card className="p-6 hover:scale-105 transition-all cursor-pointer border-2 border-transparent hover:border-purple-500">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-cosmic-glow">
                                        <Database className="h-6 w-6 text-white" />
                                    </div>
                                    <ArrowRight className="h-5 w-5 text-cosmic-txt-2" />
                                </div>
                                <h4 className="text-lg font-semibold text-cosmic-txt-1 mb-2">S3 Buckets</h4>
                                <p className="text-sm text-cosmic-txt-2 mb-3">
                                    Monitor S3 storage, encryption, and access across all regions
                                </p>
                                <div className="flex items-center space-x-2">
                                    <div className="bg-purple-500/20 px-3 py-1 rounded-lg text-xs text-purple-400 font-semibold">
                                        View Buckets
                                    </div>
                                </div>
                            </Card>
                        </Link>

                        {/* Cost Explorer Card */}
                        <Link to="/costs">
                            <Card className="p-6 hover:scale-105 transition-all cursor-pointer border-2 border-transparent hover:border-green-500">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-cosmic-glow">
                                        <DollarSign className="h-6 w-6 text-white" />
                                    </div>
                                    <ArrowRight className="h-5 w-5 text-cosmic-txt-2" />
                                </div>
                                <h4 className="text-lg font-semibold text-cosmic-txt-1 mb-2">Cost Explorer</h4>
                                <p className="text-sm text-cosmic-txt-2 mb-3">
                                    Analyze AWS spending, forecasts, and optimization opportunities
                                </p>
                                <div className="flex items-center space-x-2">
                                    <div className="bg-green-500/20 px-3 py-1 rounded-lg text-xs text-green-400 font-semibold">
                                        View Costs
                                    </div>
                                </div>
                            </Card>
                        </Link>
                    </div>
                </section>

                {/* 🆕 NEW: GuardDuty Security Overview Section */}
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
                                    {/* Status Card */}
                                    <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm text-cosmic-txt-2">Status</span>
                                            <div className={`w-3 h-3 rounded-full ${gdEnabled ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                                        </div>
                                        <p className="text-2xl font-bold text-cosmic-txt-1">
                                            {gdEnabled ? 'Enabled' : 'Disabled'}
                                        </p>
                                    </div>

                                    {/* Critical Findings Card */}
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

                                    {/* Total Findings Card */}
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

                                {/* Findings by Severity */}
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

                {/* 🆕 NEW: EC2 Instances Table Section */}
                <section className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
                    <EC2InstancesTable
                        instances={ec2Instances || []}
                        loading={loading}
                    />
                </section>

                {/* 🆕 NEW: GuardDuty Findings Table Section */}
                <section className="animate-slide-up" style={{ animationDelay: '0.3s' }}>
                    <GuardDutyFindingsTable
                        findings={allFindings || []}
                        loading={loading}
                    />
                </section>

                {/* Middle Section: Service Health & Performance */}
                <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Service Health Pie Chart */}
                    <Card className="p-6 animate-slide-up">
                        <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                            <Activity size={20} className="mr-2 text-green-400" />
                            Service Health Overview
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={serviceHealth}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={renderCustomLabel}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {serviceHealth?.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(26, 32, 53, 0.95)',
                                        border: '1px solid rgba(110, 168, 255, 0.3)',
                                        borderRadius: '0.5rem',
                                        color: '#e6e9f5'
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </Card>

                    {/* Performance Metrics */}
                    <Card className="p-0 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                        <div
                            className="p-6 border-b border-cosmic-border flex justify-between items-center cursor-pointer"
                            onClick={() => setPerformanceExpanded(!performanceExpanded)}
                        >
                            <h3 className="text-lg font-semibold text-cosmic-txt-1 flex items-center">
                                <TrendingUp size={20} className="mr-2 text-blue-400" />
                                Performance Metrics
                            </h3>
                            {performanceExpanded ?
                                <ChevronUp size={20} className="text-cosmic-txt-2" /> :
                                <ChevronDown size={20} className="text-cosmic-txt-2" />
                            }
                        </div>
                        {performanceExpanded && (
                            <ResponsiveContainer width="100%" height={300} className="p-4">
                                <LineChart data={performance} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(110, 168, 255, 0.1)" />
                                    <XAxis
                                        dataKey="time"
                                        stroke="#a5b4fc"
                                        style={{ fontSize: '12px' }}
                                    />
                                    <YAxis
                                        stroke="#a5b4fc"
                                        style={{ fontSize: '12px' }}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'rgba(26, 32, 53, 0.95)',
                                            border: '1px solid rgba(110, 168, 255, 0.3)',
                                            borderRadius: '0.75rem',
                                            color: '#e6e9f5',
                                            backdropFilter: 'blur(12px)'
                                        }}
                                    />
                                    <Legend />
                                    <Line type="monotone" dataKey="cpu" stroke="#ef4444" strokeWidth={2} name="CPU %" dot={{ r: 4 }} />
                                    <Line type="monotone" dataKey="memory" stroke="#3b82f6" strokeWidth={2} name="Memory %" dot={{ r: 4 }} />
                                    <Line type="monotone" dataKey="network" stroke="#10b981" strokeWidth={2} name="Network %" dot={{ r: 4 }} />
                                    <Line type="monotone" dataKey="storage" stroke="#f59e0b" strokeWidth={2} name="Storage %" dot={{ r: 4 }} />
                                </LineChart>
                            </ResponsiveContainer>
                        )}
                    </Card>
                </section>

                {/* Bottom Section: Alerts & Service Status */}
                <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Alerts Panel */}
                    <Card className="p-0 animate-slide-up">
                        <div
                            className="p-6 border-b border-cosmic-border flex justify-between items-center cursor-pointer"
                            onClick={() => setAlertsExpanded(!alertsExpanded)}
                        >
                            <h3 className="text-lg font-semibold text-cosmic-txt-1 flex items-center">
                                <AlertTriangle size={20} className="mr-2 text-red-400" />
                                Recent Alerts
                            </h3>
                            {alertsExpanded ?
                                <ChevronUp size={20} className="text-cosmic-txt-2" /> :
                                <ChevronDown size={20} className="text-cosmic-txt-2" />
                            }
                        </div>
                        {alertsExpanded && (
                            <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
                                {alerts?.length === 0 ? (
                                    <div className="text-center py-8 text-cosmic-txt-2">
                                        <CheckCircle size={48} className="mx-auto mb-2 opacity-50 text-green-400" />
                                        <p>No alerts at this time</p>
                                    </div>
                                ) : (
                                    alerts?.map((alert) => (
                                        <div
                                            key={alert.id}
                                            className="p-4 rounded-xl border transition-all duration-200 hover:shadow-cosmic-glow"
                                            style={{
                                                borderColor: getSeverityColor(alert.severity),
                                                backgroundColor: getSeverityBg(alert.severity),
                                                backdropFilter: 'blur(8px)'
                                            }}
                                        >
                                            <div className="flex items-start space-x-3">
                                                <AlertTriangle
                                                    size={16}
                                                    style={{ color: getSeverityColor(alert.severity) }}
                                                    className="mt-0.5 flex-shrink-0"
                                                />
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center space-x-2 mb-2">
                                                        <span
                                                            className="text-xs font-semibold uppercase px-2 py-1 rounded"
                                                            style={{
                                                                color: getSeverityColor(alert.severity),
                                                                backgroundColor: 'rgba(15, 20, 40, 0.5)'
                                                            }}
                                                        >
                                                            {alert.severity}
                                                        </span>
                                                        <span className="text-sm text-cosmic-txt-2">
                                                            {alert.service} • {alert.region}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-cosmic-txt-1 mb-2 leading-relaxed">
                                                        {alert.message}
                                                    </p>
                                                    <p className="text-xs text-cosmic-muted">
                                                        {alert.timestamp}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}
                    </Card>

                    {/* Service Status List */}
                    <Card className="p-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                        <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                            <Shield size={20} className="mr-2 text-blue-400" />
                            Service Status
                        </h3>
                        <div className="space-y-3">
                            {serviceStatus?.length === 0 ? (
                                <div className="text-center py-8 text-cosmic-txt-2">
                                    <Monitor size={48} className="mx-auto mb-2 opacity-50" />
                                    <p>No services to display</p>
                                </div>
                            ) : (
                                serviceStatus?.map((service, index) => (
                                    <div
                                        key={index}
                                        className="flex items-center justify-between p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border hover:border-blue-500/50 transition-all duration-200"
                                    >
                                        <div className="flex items-center space-x-3">
                                            <div style={{ color: getStatusColor(service.status) }}>
                                                {getStatusIcon(service.status)}
                                            </div>
                                            <div>
                                                <p className="font-medium text-cosmic-txt-1">{service.name}</p>
                                                <p className="text-sm text-cosmic-txt-2">{service.region}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-medium text-cosmic-txt-1 mb-1">
                                                {service.instances} instances
                                            </p>
                                            <span
                                                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize"
                                                style={{
                                                    color: getStatusColor(service.status),
                                                    backgroundColor: `${getStatusColor(service.status)}20`
                                                }}
                                            >
                                                {service.status}
                                            </span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </Card>
                </section>

                {/* Footer Stats */}
                <div className="mt-8 text-center">
                    <div className="inline-flex items-center space-x-2 text-sm text-cosmic-txt-2 bg-cosmic-card px-6 py-3 rounded-full border border-cosmic-border backdrop-blur-sm">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        <span>Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Never'}</span>
                        <span>•</span>
                        <span>Auto-refresh: Every 5 minutes</span>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default AWSCloudHealthDashboard;