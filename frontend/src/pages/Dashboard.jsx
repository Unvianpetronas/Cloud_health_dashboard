import React, { useState } from 'react';
import useDashboardData from '../hooks/useDashboardData';
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
    Activity, AlertTriangle, CheckCircle, Cloud, DollarSign,
    Monitor, RefreshCw, Server, Shield, Zap, TrendingUp,
    ChevronDown, ChevronUp
} from 'lucide-react';

import Header from '../components/common/Header';
import Card from '../components/common/Card';
import MetricsCard from '../components/dashboard/MetricsCard';
import Loading from '../components/common/Loading';

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

    const { ec2Summary, ec2Cost, performance, serviceHealth, alerts, serviceStatus } = data;

    // Calculate metrics
    const totalInstances = ec2Summary?.total_instances || 0;
    const runningInstances = ec2Summary?.by_state?.running || 0;
    const totalCost = ec2Cost?.total_estimated_cost || 0;
    const regionsActive = ec2Summary?.regions_with_instances || 0;

    // Prepare metrics data
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
            title: 'Active Alerts',
            value: alerts?.length || 0,
            change: '1 critical',
            changeType: 'negative',
            icon: AlertTriangle,
            iconColor: '#ef4444',
            iconBgColor: '#fef2f2'
        },
        {
            title: 'Active Regions',
            value: regionsActive,
            change: 'with EC2 instances',
            changeType: 'positive',
            icon: Zap,
            iconColor: '#0ea5e9',
            iconBgColor: '#f0f9ff'
        }
    ];

    // Prepare chart data
    const regionData = ec2Summary?.by_region ?
        Object.entries(ec2Summary.by_region).map(([region, instances]) => ({
            region: region.replace('us-', 'US ').replace('eu-', 'EU ').replace('-', ' '),
            instances
        })) : [];

    const costsData = [
        { name: 'Jan', cost: 1200, budget: 1500 },
        { name: 'Feb', cost: 1350, budget: 1500 },
        { name: 'Mar', cost: 1100, budget: 1500 },
        { name: 'Apr', cost: 1400, budget: 1500 },
        { name: 'May', cost: 1250, budget: 1500 },
        { name: 'Jun', cost: 1600, budget: 1500 },
        { name: 'Jul', cost: totalCost, budget: 1500 }
    ];

    const getSeverityColor = (severity) => {
        switch (severity) {
            case 'critical': return '#ef4444';
            case 'warning': return '#f59e0b';
            case 'info': return '#3b82f6';
            default: return '#6b7280';
        }
    };

    const getSeverityBg = (severity) => {
        switch (severity) {
            case 'critical': return 'rgba(239, 68, 68, 0.1)';
            case 'warning': return 'rgba(245, 158, 11, 0.1)';
            case 'info': return 'rgba(59, 130, 246, 0.1)';
            default: return 'rgba(107, 114, 128, 0.1)';
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'healthy': return '#10b981';
            case 'warning': return '#f59e0b';
            case 'critical': return '#ef4444';
            default: return '#6b7280';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'healthy': return <CheckCircle size={16} />;
            case 'warning': return <AlertTriangle size={16} />;
            case 'critical': return <AlertTriangle size={16} />;
            default: return <Monitor size={16} />;
        }
    };

    return (
        <div className="min-h-screen">
            {/* Cosmic Header */}
            <Header
                title="AWS Cloud Health Dashboard"
                onRefresh={handleRefresh}
                refreshing={refreshing}
                selectedTimeRange={selectedTimeRange}
                onTimeRangeChange={setSelectedTimeRange}
            />

            <main className="container mx-auto px-6 py-8">
                {/* Status Banner */}
                <div className="badge mb-6 animate-fade-in inline-flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span>System Status: All Services Operational</span>
                </div>

                {/* Metrics Cards */}
                <section className="mb-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {metricsData.map((metric, index) => (
                            <div key={index} className="relative">
                                <Card
                                    className="p-6 animate-fade-in"
                                    style={{
                                        animationDelay: `${index * 0.1}s`,
                                        overflow: 'visible'
                                    }}
                                >
                                    <MetricsCard {...metric} />
                                </Card>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Charts Section */}
                <section className="mb-8">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Cost Trend Chart */}
                        <Card className="lg:col-span-2 p-6 animate-slide-up">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-cosmic-txt-1 flex items-center">
                                    <TrendingUp size={20} className="mr-2 text-blue-400" />
                                    Cost Trends vs Budget
                                </h3>
                                <span className="badge text-xs">Last 7 Months</span>
                            </div>
                            <ResponsiveContainer width="100%" height={300}>
                                <AreaChart data={costsData}>
                                    <defs>
                                        <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(110, 168, 255, 0.1)" />
                                    <XAxis dataKey="name" stroke="#8b93ad" fontSize={12} />
                                    <YAxis stroke="#8b93ad" fontSize={12} />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'rgba(15, 20, 40, 0.95)',
                                            border: '1px solid rgba(110, 168, 255, 0.3)',
                                            borderRadius: '0.75rem',
                                            color: '#e6e9f5',
                                            backdropFilter: 'blur(12px)'
                                        }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="budget"
                                        stroke="rgba(139, 147, 173, 0.5)"
                                        fill="rgba(139, 147, 173, 0.1)"
                                        name="Budget"
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="cost"
                                        stroke="#3b82f6"
                                        fill="url(#costGradient)"
                                        name="Actual Cost"
                                    />
                                    <Legend />
                                </AreaChart>
                            </ResponsiveContainer>
                        </Card>

                        {/* Service Health - SIDE BY SIDE (NO CLIPPING!) */}
                        <Card className="p-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                            <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                <Activity size={20} className="mr-2 text-green-400" />
                                Service Health
                            </h3>

                            <div className="flex flex-col">
                                {/* Pie Chart */}
                                <div style={{ width: '100%', height: '180px' }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={serviceHealth}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ percent }) => {
                                                    const p = (percent * 100).toFixed(0);
                                                    return p > 5 ? `${p}%` : '';
                                                }}
                                                outerRadius={70}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {serviceHealth?.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: 'rgba(15, 20, 40, 0.95)',
                                                    border: '1px solid rgba(110, 168, 255, 0.3)',
                                                    borderRadius: '0.75rem',
                                                    color: '#e6e9f5',
                                                    backdropFilter: 'blur(12px)'
                                                }}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>

                                {/* Legend Below */}
                                <div className="space-y-2 mt-4">
                                    {serviceHealth?.map((item, index) => (
                                        <div
                                            key={index}
                                            className="flex items-center justify-between p-2 rounded-lg bg-cosmic-bg-2 border border-cosmic-border hover:border-blue-500/30 transition-all"
                                        >
                                            <div className="flex items-center space-x-2">
                                                <div
                                                    className="w-3 h-3 rounded-full flex-shrink-0"
                                                    style={{
                                                        backgroundColor: item.color,
                                                        boxShadow: `0 0 6px ${item.color}60`
                                                    }}
                                                />
                                                <span className="text-xs font-medium text-cosmic-txt-2">
                                    {item.name}
                                </span>
                                            </div>
                                            <span className="text-sm font-bold text-cosmic-txt-1">
                                {item.value}
                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </Card>
                    </div>
                </section>

                {/* Regions Chart */}
                {regionData.length > 0 && (
                    <section className="mb-8">
                        <Card className="p-6 animate-slide-up">
                            <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                <Cloud size={20} className="mr-2 text-blue-400" />
                                EC2 Instances by Region
                            </h3>
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={regionData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(110, 168, 255, 0.1)" />
                                    <XAxis dataKey="region" stroke="#8b93ad" fontSize={12} />
                                    <YAxis stroke="#8b93ad" fontSize={12} />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'rgba(15, 20, 40, 0.95)',
                                            border: '1px solid rgba(110, 168, 255, 0.3)',
                                            borderRadius: '0.75rem',
                                            color: '#e6e9f5',
                                            backdropFilter: 'blur(12px)'
                                        }}
                                    />
                                    <Bar dataKey="instances" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </Card>
                    </section>
                )}

                {/* Performance Chart */}
                <section className="mb-8">
                    <Card className="p-6 animate-slide-up">
                        <div
                            className="flex items-center justify-between mb-4 cursor-pointer"
                            onClick={() => setPerformanceExpanded(!performanceExpanded)}
                        >
                            <h3 className="text-lg font-semibold text-cosmic-txt-1 flex items-center">
                                <Activity size={20} className="mr-2 text-orange-400" />
                                Performance Metrics (Last 24 Hours)
                            </h3>
                            {performanceExpanded ?
                                <ChevronUp size={20} className="text-cosmic-txt-2" /> :
                                <ChevronDown size={20} className="text-cosmic-txt-2" />
                            }
                        </div>
                        {performanceExpanded && (
                            <ResponsiveContainer width="100%" height={350}>
                                <LineChart data={performance}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(110, 168, 255, 0.1)" />
                                    <XAxis dataKey="time" stroke="#8b93ad" fontSize={12} />
                                    <YAxis stroke="#8b93ad" fontSize={12} />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'rgba(15, 20, 40, 0.95)',
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