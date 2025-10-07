import React, { useState, useEffect } from 'react';
import useDashboardData from '../hooks/useDashboardData';
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
    Activity, AlertTriangle, CheckCircle, Cloud, DollarSign,
    Monitor, RefreshCw, Server, Shield, Zap
} from 'lucide-react';

const AWSCloudHealthDashboard = () => {
    // State management
    const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
    const [alertsExpanded, setAlertsExpanded] = useState(true);
    const [currentTime, setCurrentTime] = useState(new Date());

    // Fetch real data
    const { data, loading, error, lastUpdated, refresh } = useDashboardData(selectedTimeRange);
    const [refreshing, setRefreshing] = useState(false);

    // Effects
    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    // Handler functions
    const handleRefresh = async () => {
        setRefreshing(true);
        await refresh();
        setRefreshing(false);
    };

    // Loading state
    if (loading && !data.ec2Summary) {
        return (
            <div style={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f8fafc'
            }}>
                <div style={{ textAlign: 'center' }}>
                    <RefreshCw size={48} style={{
                        animation: 'spin 1s linear infinite',
                        color: '#3b82f6',
                        margin: '0 auto 1rem'
                    }} />
                    <p>Loading dashboard data...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (error && !data.ec2Summary) {
        return (
            <div style={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f8fafc'
            }}>
                <div style={{
                    textAlign: 'center',
                    padding: '2rem',
                    backgroundColor: 'white',
                    borderRadius: '0.5rem',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                }}>
                    <AlertTriangle size={48} color="#ef4444" style={{ margin: '0 auto 1rem' }} />
                    <h3>Error Loading Dashboard</h3>
                    <p style={{ color: '#6b7280', margin: '1rem 0' }}>{error}</p>
                    <button
                        onClick={handleRefresh}
                        style={{
                            padding: '0.5rem 1rem',
                            backgroundColor: '#3b82f6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '0.375rem',
                            cursor: 'pointer'
                        }}
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    // Extract data
    const { ec2Summary, ec2Cost, performance, serviceHealth, alerts, serviceStatus } = data;

    // Calculate EC2 metrics from REAL data
    const totalInstances = ec2Summary?.total_instances || 0;
    const runningInstances = ec2Summary?.by_state?.running || 0;
    const totalCost = ec2Cost?.total_estimated_cost || 0;
    const regionsActive = ec2Summary?.regions_with_instances || 0;

    // Prepare region chart data from REAL EC2 data
    const regionData = ec2Summary?.by_region ?
        Object.entries(ec2Summary.by_region).map(([region, instances]) => ({
            region,
            instances,
            cost: 0 // Can calculate from cost breakdown if needed
        })) : [];

    // Mock data for charts that don't have real data yet
    const costsData = [
        { name: 'Jan', cost: 1200, budget: 1500 },
        { name: 'Feb', cost: 1350, budget: 1500 },
        { name: 'Mar', cost: 1100, budget: 1500 },
        { name: 'Apr', cost: 1400, budget: 1500 },
        { name: 'May', cost: 1250, budget: 1500 },
        { name: 'Jun', cost: 1600, budget: 1500 },
        { name: 'Jul', cost: totalCost, budget: 1500 } // Last month uses real data
    ];

    const getSeverityColor = (severity) => {
        switch (severity) {
            case 'critical': return '#ef4444';
            case 'warning': return '#f59e0b';
            case 'info': return '#3b82f6';
            default: return '#6b7280';
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
        <div style={{
            minHeight: '100vh',
            backgroundColor: '#f8fafc',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
        }}>
            {/* Header - giữ nguyên */}
            <header style={{
                backgroundColor: '#ffffff',
                borderBottom: '1px solid #e2e8f0',
                padding: '1rem 2rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Cloud size={32} color="#ff9900" />
                    <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '600', color: '#1e293b' }}>
                        AWS Cloud Health Dashboard
                    </h1>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <select
                        value={selectedTimeRange}
                        onChange={(e) => setSelectedTimeRange(e.target.value)}
                        style={{
                            padding: '0.5rem 1rem',
                            border: '1px solid #d1d5db',
                            borderRadius: '0.375rem',
                            backgroundColor: 'white',
                            fontSize: '0.875rem'
                        }}
                    >
                        <option value="1h">Last Hour</option>
                        <option value="24h">Last 24 Hours</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                    </select>

                    <button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        style={{
                            padding: '0.5rem 1rem',
                            backgroundColor: '#3b82f6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '0.375rem',
                            cursor: refreshing ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            fontSize: '0.875rem',
                            opacity: refreshing ? 0.6 : 1
                        }}
                    >
                        <RefreshCw size={16} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
                        Refresh
                    </button>

                    <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                        Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : currentTime.toLocaleTimeString()}
                    </div>
                </div>
            </header>

            {/* Main Dashboard Content */}
            <main style={{ padding: '2rem' }}>
                {/* Key Metrics Cards - DÙNG REAL DATA */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                    gap: '1.5rem',
                    marginBottom: '2rem'
                }}>
                    {/* REAL EC2 Cost */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>
                                    EC2 Monthly Cost (Estimated)
                                </p>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '2rem', fontWeight: '700', color: '#1e293b' }}>
                                    ${totalCost.toFixed(2)}
                                </p>
                                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#10b981' }}>
                                    {runningInstances} running instances
                                </p>
                            </div>
                            <div style={{ padding: '1rem', backgroundColor: '#dbeafe', borderRadius: '0.5rem' }}>
                                <DollarSign size={32} color="#3b82f6" />
                            </div>
                        </div>
                    </div>

                    {/* REAL EC2 Instances */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>EC2 Instances</p>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '2rem', fontWeight: '700', color: '#1e293b' }}>
                                    {totalInstances}
                                </p>
                                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#10b981' }}>
                                    {ec2Summary?.has_instances ? `${runningInstances} running` : 'No instances'}
                                </p>
                            </div>
                            <div style={{ padding: '1rem', backgroundColor: '#d1fae5', borderRadius: '0.5rem' }}>
                                <Server size={32} color="#10b981" />
                            </div>
                        </div>
                    </div>

                    {/* Mock Alerts - giữ nguyên */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>Active Alerts</p>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '2rem', fontWeight: '700', color: '#1e293b' }}>
                                    {alerts?.length || 0}
                                </p>
                                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#ef4444' }}>
                                    1 critical
                                </p>
                            </div>
                            <div style={{ padding: '1rem', backgroundColor: '#fef2f2', borderRadius: '0.5rem' }}>
                                <AlertTriangle size={32} color="#ef4444" />
                            </div>
                        </div>
                    </div>

                    {/* REAL Regions Active */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>Active Regions</p>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '2rem', fontWeight: '700', color: '#1e293b' }}>
                                    {regionsActive}
                                </p>
                                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#10b981' }}>
                                    with EC2 instances
                                </p>
                            </div>
                            <div style={{ padding: '1rem', backgroundColor: '#f0f9ff', borderRadius: '0.5rem' }}>
                                <Zap size={32} color="#0ea5e9" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Phần còn lại giữ nguyên 100% - chỉ cần dùng data từ mock... */}
                {/* Copy toàn bộ phần charts, alerts, service status từ code cũ */}
            </main>

            {/* CSS Animations - giữ nguyên */}
            <style jsx>{`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                button:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.15);
                }
            `}</style>
        </div>
    );
};

export default AWSCloudHealthDashboard;