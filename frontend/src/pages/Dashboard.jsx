import React, { useState, useEffect } from 'react';
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';
import {
    Activity,
    AlertTriangle,
    CheckCircle,
    Cloud,
    CpuIcon,
    Database,
    DollarSign,
    HardDrive,
    Monitor,
    Network,
    RefreshCw,
    Server,
    Shield,
    TrendingUp,
    Users,
    Wifi,
    Zap
} from 'lucide-react';

const AWSCloudHealthDashboard = () => {
    // State management
    const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
    const [refreshing, setRefreshing] = useState(false);
    const [alertsExpanded, setAlertsExpanded] = useState(true);
    const [currentTime, setCurrentTime] = useState(new Date());

    // Mock data for costs over time
    const costsData = [
        { name: 'Jan', cost: 1200, budget: 1500 },
        { name: 'Feb', cost: 1350, budget: 1500 },
        { name: 'Mar', cost: 1100, budget: 1500 },
        { name: 'Apr', cost: 1400, budget: 1500 },
        { name: 'May', cost: 1250, budget: 1500 },
        { name: 'Jun', cost: 1600, budget: 1500 },
        { name: 'Jul', cost: 1800, budget: 1500 }
    ];

    // Mock data for performance metrics
    const performanceData = [
        { time: '00:00', cpu: 45, memory: 62, network: 23, storage: 78 },
        { time: '04:00', cpu: 52, memory: 58, network: 34, storage: 80 },
        { time: '08:00', cpu: 78, memory: 71, network: 67, storage: 82 },
        { time: '12:00', cpu: 85, memory: 76, network: 89, storage: 84 },
        { time: '16:00', cpu: 72, memory: 68, network: 45, storage: 86 },
        { time: '20:00', cpu: 58, memory: 64, network: 32, storage: 88 },
        { time: '24:00', cpu: 48, memory: 59, network: 28, storage: 90 }
    ];

    // Mock data for service health distribution
    const serviceHealthData = [
        { name: 'Healthy', value: 84, color: '#10b981' },
        { name: 'Warning', value: 12, color: '#f59e0b' },
        { name: 'Critical', value: 3, color: '#ef4444' },
        { name: 'Unknown', value: 1, color: '#6b7280' }
    ];

    // Mock data for regional distribution
    const regionData = [
        { region: 'US East', instances: 24, cost: 456 },
        { region: 'US West', instances: 18, cost: 342 },
        { region: 'EU Central', instances: 15, cost: 289 },
        { region: 'Asia Pacific', instances: 12, cost: 234 },
        { region: 'Canada', instances: 8, cost: 156 }
    ];

    // Mock alerts data
    const alertsData = [
        {
            id: 1,
            severity: 'critical',
            service: 'EC2',
            message: 'High CPU utilization on instance i-1234567890abcdef0',
            timestamp: '2 minutes ago',
            region: 'us-east-1'
        },
        {
            id: 2,
            severity: 'warning',
            service: 'RDS',
            message: 'Database connection pool near capacity',
            timestamp: '15 minutes ago',
            region: 'us-west-2'
        },
        {
            id: 3,
            severity: 'info',
            service: 'S3',
            message: 'Scheduled maintenance completed successfully',
            timestamp: '1 hour ago',
            region: 'eu-west-1'
        },
        {
            id: 4,
            severity: 'warning',
            service: 'Lambda',
            message: 'Function timeout threshold exceeded',
            timestamp: '2 hours ago',
            region: 'ap-southeast-1'
        }
    ];

    // Service status data
    const serviceStatus = [
        { name: 'EC2', status: 'healthy', instances: 24, region: 'us-east-1' },
        { name: 'RDS', status: 'warning', instances: 8, region: 'us-west-2' },
        { name: 'Lambda', status: 'healthy', instances: 156, region: 'global' },
        { name: 'S3', status: 'healthy', instances: 12, region: 'global' },
        { name: 'CloudFront', status: 'critical', instances: 3, region: 'global' },
        { name: 'ELB', status: 'healthy', instances: 15, region: 'us-east-1' }
    ];

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
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000));
        setRefreshing(false);
    };

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
            {/* Header */}
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
                        Last updated: {currentTime.toLocaleTimeString()}
                    </div>
                </div>
            </header>

            {/* Main Dashboard Content */}
            <main style={{ padding: '2rem' }}>
                {/* Key Metrics Cards */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                    gap: '1.5rem',
                    marginBottom: '2rem'
                }}>
                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>Total Monthly Cost</p>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '2rem', fontWeight: '700', color: '#1e293b' }}>
                                    $1,847
                                </p>
                                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#10b981' }}>
                                    ↑ 8.2% from last month
                                </p>
                            </div>
                            <div style={{ padding: '1rem', backgroundColor: '#dbeafe', borderRadius: '0.5rem' }}>
                                <DollarSign size={32} color="#3b82f6" />
                            </div>
                        </div>
                    </div>

                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>Active Resources</p>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '2rem', fontWeight: '700', color: '#1e293b' }}>
                                    247
                                </p>
                                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#10b981' }}>
                                    94% healthy
                                </p>
                            </div>
                            <div style={{ padding: '1rem', backgroundColor: '#d1fae5', borderRadius: '0.5rem' }}>
                                <Server size={32} color="#10b981" />
                            </div>
                        </div>
                    </div>

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
                                    {alertsData.length}
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

                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>Avg Response Time</p>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '2rem', fontWeight: '700', color: '#1e293b' }}>
                                    234ms
                                </p>
                                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#10b981' }}>
                                    ↓ 12ms from avg
                                </p>
                            </div>
                            <div style={{ padding: '1rem', backgroundColor: '#f0f9ff', borderRadius: '0.5rem' }}>
                                <Zap size={32} color="#0ea5e9" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Charts Section */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: '2fr 1fr',
                    gap: '1.5rem',
                    marginBottom: '2rem'
                }}>
                    {/* Cost Trends Chart */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.125rem', fontWeight: '600', color: '#1e293b' }}>
                            Cost Trends vs Budget
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={costsData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                                <YAxis stroke="#64748b" fontSize={12} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'white',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '0.375rem',
                                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                    }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="budget"
                                    stackId="1"
                                    stroke="#e2e8f0"
                                    fill="#f8fafc"
                                    fillOpacity={0.6}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="cost"
                                    stackId="2"
                                    stroke="#3b82f6"
                                    fill="#3b82f6"
                                    fillOpacity={0.6}
                                />
                                <Legend />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Service Health Pie Chart */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.125rem', fontWeight: '600', color: '#1e293b' }}>
                            Service Health Distribution
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={serviceHealthData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {serviceHealthData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Performance Metrics Chart */}
                <div style={{
                    backgroundColor: 'white',
                    padding: '1.5rem',
                    borderRadius: '0.5rem',
                    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                    border: '1px solid #e2e8f0',
                    marginBottom: '2rem'
                }}>
                    <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.125rem', fontWeight: '600', color: '#1e293b' }}>
                        Performance Metrics (Last 24 Hours)
                    </h3>
                    <ResponsiveContainer width="100%" height={350}>
                        <LineChart data={performanceData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                            <YAxis stroke="#64748b" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'white',
                                    border: '1px solid #e2e8f0',
                                    borderRadius: '0.375rem',
                                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="cpu" stroke="#ef4444" strokeWidth={2} name="CPU %" />
                            <Line type="monotone" dataKey="memory" stroke="#3b82f6" strokeWidth={2} name="Memory %" />
                            <Line type="monotone" dataKey="network" stroke="#10b981" strokeWidth={2} name="Network %" />
                            <Line type="monotone" dataKey="storage" stroke="#f59e0b" strokeWidth={2} name="Storage %" />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Bottom Section */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '1.5rem'
                }}>
                    {/* Alerts Panel */}
                    <div style={{
                        backgroundColor: 'white',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <div style={{
                            padding: '1.5rem 1.5rem 1rem 1.5rem',
                            borderBottom: '1px solid #e2e8f0',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: '600', color: '#1e293b' }}>
                                Recent Alerts
                            </h3>
                            <button
                                onClick={() => setAlertsExpanded(!alertsExpanded)}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    cursor: 'pointer',
                                    color: '#6b7280'
                                }}
                            >
                                {alertsExpanded ? '−' : '+'}
                            </button>
                        </div>

                        {alertsExpanded && (
                            <div style={{ padding: '1rem' }}>
                                {alertsData.map((alert) => (
                                    <div
                                        key={alert.id}
                                        style={{
                                            padding: '1rem',
                                            marginBottom: '0.75rem',
                                            border: `1px solid ${getSeverityColor(alert.severity)}`,
                                            borderRadius: '0.375rem',
                                            backgroundColor: `${getSeverityColor(alert.severity)}08`
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                                    <AlertTriangle size={16} color={getSeverityColor(alert.severity)} />
                                                    <span style={{
                                                        fontSize: '0.75rem',
                                                        fontWeight: '600',
                                                        color: getSeverityColor(alert.severity),
                                                        textTransform: 'uppercase'
                                                    }}>
                            {alert.severity}
                          </span>
                                                    <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                            {alert.service} • {alert.region}
                          </span>
                                                </div>
                                                <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', color: '#374151' }}>
                                                    {alert.message}
                                                </p>
                                                <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>
                                                    {alert.timestamp}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Service Status */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '0.5rem',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        border: '1px solid #e2e8f0'
                    }}>
                        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.125rem', fontWeight: '600', color: '#1e293b' }}>
                            Service Status
                        </h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {serviceStatus.map((service, index) => (
                                <div
                                    key={index}
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        padding: '1rem',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '0.375rem',
                                        backgroundColor: '#fafafa'
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <div style={{ color: getStatusColor(service.status) }}>
                                            {getStatusIcon(service.status)}
                                        </div>
                                        <div>
                                            <p style={{ margin: 0, fontSize: '0.875rem', fontWeight: '500', color: '#1e293b' }}>
                                                {service.name}
                                            </p>
                                            <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>
                                                {service.region}
                                            </p>
                                        </div>
                                    </div>

                                    <div style={{ textAlign: 'right' }}>
                                        <p style={{ margin: 0, fontSize: '0.875rem', fontWeight: '500', color: '#1e293b' }}>
                                            {service.instances} instances
                                        </p>
                                        <p style={{
                                            margin: 0,
                                            fontSize: '0.75rem',
                                            color: getStatusColor(service.status),
                                            textTransform: 'capitalize'
                                        }}>
                                            {service.status}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </main>

            {/* CSS Animations */}
            <style jsx>{`
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        
        button:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.15);
        }
        
        .recharts-tooltip-cursor {
          fill: rgba(59, 130, 246, 0.1);
        }
        
        .recharts-cartesian-grid-horizontal line,
        .recharts-cartesian-grid-vertical line {
          stroke-opacity: 0.5;
        }
        
        .recharts-legend-wrapper {
          padding-top: 20px;
        }
      `}</style>
        </div>
    );
};

export default AWSCloudHealthDashboard;