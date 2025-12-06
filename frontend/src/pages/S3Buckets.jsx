import React, { useState, useEffect } from 'react';
import { RefreshCw, Database, HardDrive, Lock, Unlock, Globe, Shield, AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/common/Header';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import s3Api from '../services/s3Api';
import logger from '../utils/logger';

const S3Buckets = () => {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      fetchS3Data();
    }
  }, [isAuthenticated]);

  const fetchS3Data = async () => {
    setLoading(true);
    setError(null);

    // This calls your updated /s3/summary endpoint
    const result = await s3Api.getSummary(false);

    if (result.success) {
      setData(result.data);
      logger.info(`Loaded S3 summary data`);
    } else {
      setError(result.error);
      logger.error('Failed to load S3 data:', result.error);
    }

    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const result = await s3Api.getSummary(true);

      if (result.success) {
        setData(result.data);
        logger.info('S3 data refreshed');
      } else {
        setError(result.error);
        logger.error('Failed to refresh S3 data:', result.error);
      }
    } catch (error) {
      setError('Failed to refresh S3 data');
      logger.error('Error refreshing S3 data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Helper to display GB nicely
  const formatGB = (gb) => {
    if (!gb) return '0 GB';
    if (gb < 1) return (gb * 1024).toFixed(2) + ' MB';
    return gb.toFixed(4) + ' GB';
  };

  const formatNumber = (num) => {
    if (!num || num === 0) return '0';
    return num.toLocaleString();
  };

  // --- DATA MAPPING (Adapted to New Backend Structure) ---

  // 1. Region Distribution
  const getRegionDistribution = () => {
    // The backend sends 'all_buckets_details'
    const buckets = data?.all_buckets_details || [];
    if (buckets.length === 0) return [];

    const regions = {};
    buckets.forEach(bucket => {
      const region = bucket.region || 'unknown';
      regions[region] = (regions[region] || 0) + 1;
    });

    return Object.entries(regions).map(([name, value]) => ({ name, value }));
  };

  // 2. Top 10 Storage (Already provided by Backend!)
  const getStorageByBucket = () => {
    const top10 = data?.top_10_buckets || [];
    return top10.map(b => ({
      name: b.name.substring(0, 15) + (b.name.length > 15 ? '...' : ''), // Shorten name for chart
      storage: b.size_gb,
      full_name: b.name
    }));
  };

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#84cc16'];

  if (loading) {
    return (
        <div className="min-h-screen">
          <Header title="S3 Buckets" showNavigation={true} />
          <main className="p-6 max-w-7xl mx-auto">
            <div className="flex items-center justify-center h-96">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
            </div>
          </main>
        </div>
    );
  }

  if (error) {
    return (
        <div className="min-h-screen">
          <Header title="S3 Buckets" showNavigation={true} />
          <main className="p-6 max-w-7xl mx-auto">
            <Card className="p-8 text-center">
              <AlertTriangle className="h-16 w-16 text-red-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-cosmic-txt-1 mb-2">Failed to Load S3 Data</h2>
              <p className="text-cosmic-txt-2 mb-4">{error}</p>
              <Button onClick={fetchS3Data} variant="primary" className="px-12 py-3 flex items-center justify-center mx-auto">
                <RefreshCw size={16} className="mr-2" />
                Retry
              </Button>
            </Card>
          </main>
        </div>
    );
  }

  const regionData = getRegionDistribution();
  const storageData = getStorageByBucket();

  // Calculate usage color
  const usagePercent = data?.free_tier_usage_percent || 0;
  const usageColor = usagePercent > 100 ? 'text-red-500' : usagePercent > 80 ? 'text-yellow-400' : 'text-green-400';

  return (
      <div className="min-h-screen">
        <Header title="S3 Buckets" showNavigation={true} />

        <main className="p-6 max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center animate-fade-in">
            <div>
              <h1 className="text-3xl font-bold text-cosmic-txt-1 mb-2">S3 Storage Overview</h1>
              <p className="text-cosmic-txt-2">Manage and monitor your S3 buckets across all regions</p>
            </div>
            <Button
                onClick={handleRefresh}
                disabled={refreshing}
                variant="primary"
                className="flex items-center space-x-2"
            >
              {refreshing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    <span>Refreshing...</span>
                  </>
              ) : (
                  <>
                    <RefreshCw size={18} />
                    <span>Refresh</span>
                  </>
              )}
            </Button>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-6 animate-fade-in">
              <div className="flex items-center justify-between mb-2">
                <Database className="h-8 w-8 text-blue-400" />
                <div className="text-right">
                  <div className="text-3xl font-bold text-cosmic-txt-1">{data?.total_buckets || 0}</div>
                  <div className="text-sm text-cosmic-txt-2">Total Buckets</div>
                </div>
              </div>
            </Card>

            <Card className="p-6 animate-fade-in" style={{animationDelay: '0.1s'}}>
              <div className="flex items-center justify-between mb-2">
                <HardDrive className="h-8 w-8 text-purple-400" />
                <div className="text-right">
                  {/* USE BACKEND TOTAL DIRECTLY */}
                  <div className="text-3xl font-bold text-cosmic-txt-1">{data?.total_storage_gb?.toFixed(4)} GB</div>
                  <div className="text-sm text-cosmic-txt-2">Total Storage</div>
                </div>
              </div>
            </Card>

            <Card className="p-6 animate-fade-in" style={{animationDelay: '0.2s'}}>
              <div className="flex items-center justify-between mb-2">
                {usagePercent > 100 ? (
                    <AlertTriangle className="h-8 w-8 text-red-500" />
                ) : (
                    <Shield className="h-8 w-8 text-green-400" />
                )}
                <div className="text-right">
                  <div className={`text-3xl font-bold ${usageColor}`}>
                    {usagePercent.toFixed(1)}%
                  </div>
                  <div className="text-sm text-cosmic-txt-2">Free Tier Used (5GB)</div>
                </div>
              </div>
            </Card>

            <Card className="p-6 animate-fade-in" style={{animationDelay: '0.3s'}}>
              <div className="flex items-center justify-between mb-2">
                <Globe className="h-8 w-8 text-blue-400" />
                <div className="text-right">
                  <div className="text-3xl font-bold text-cosmic-txt-1">
                    {regionData.length}
                  </div>
                  <div className="text-sm text-cosmic-txt-2">Active Regions</div>
                </div>
              </div>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Region Distribution */}
            {regionData.length > 0 && (
                <Card className="p-6 animate-fade-in" style={{animationDelay: '0.4s'}}>
                  <h2 className="text-xl font-semibold text-cosmic-txt-1 mb-4">Buckets by Region</h2>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                          data={regionData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                      >
                        {regionData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                          contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                          labelStyle={{ color: '#f3f4f6' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </Card>
            )}

            {/* Storage by Bucket */}
            {storageData.length > 0 && (
                <Card className="p-6 animate-fade-in" style={{animationDelay: '0.5s'}}>
                  <h2 className="text-xl font-semibold text-cosmic-txt-1 mb-4">Top 10 Buckets by Storage (GB)</h2>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={storageData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                      <YAxis tick={{ fill: '#9ca3af' }} label={{ value: 'GB', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
                      <Tooltip
                          contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                          labelStyle={{ color: '#f3f4f6' }}
                          formatter={(value) => `${value.toFixed(4)} GB`}
                      />
                      <Bar dataKey="storage" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
            )}
          </div>

          {/* Buckets Table */}
          <Card className="p-6 animate-fade-in" style={{animationDelay: '0.6s'}}>
            <h2 className="text-xl font-semibold text-cosmic-txt-1 mb-4">All Buckets Details</h2>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                <tr className="border-b border-cosmic-border">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Bucket Name</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Region</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Size</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Objects</th>
                </tr>
                </thead>
                <tbody>
                {/* Use all_buckets_details from backend */}
                {data?.all_buckets_details && data.all_buckets_details.length > 0 ? (
                    data.all_buckets_details.map((bucket, index) => (
                        <tr key={index} className="border-b border-cosmic-border hover:bg-cosmic-bg-2 transition-colors">
                          <td className="py-3 px-4 text-sm text-cosmic-txt-1 font-medium">{bucket.name}</td>
                          <td className="py-3 px-4 text-sm text-cosmic-txt-2">{bucket.region}</td>
                          <td className="py-3 px-4 text-sm text-cosmic-txt-2 text-right">
                            {formatGB(bucket.size_gb)}
                          </td>
                          <td className="py-3 px-4 text-sm text-cosmic-txt-2 text-right">
                            {formatNumber(bucket.object_count)}
                          </td>
                        </tr>
                    ))
                ) : (
                    <tr>
                      <td colSpan="4" className="py-8 text-center text-cosmic-txt-2">
                        No S3 buckets found
                      </td>
                    </tr>
                )}
                </tbody>
              </table>
            </div>
          </Card>
        </main>
      </div>
  );
};

export default S3Buckets;