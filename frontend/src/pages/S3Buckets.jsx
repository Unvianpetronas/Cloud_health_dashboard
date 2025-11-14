import React, { useState, useEffect } from 'react';
import { RefreshCw, Database, HardDrive, Lock, Unlock, Globe, Shield, AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
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

    const result = await s3Api.getSummary(false);

    if (result.success) {
      setData(result.data);
      logger.info(`Loaded ${result.data.total_buckets} S3 buckets`);
    } else {
      setError(result.error);
      logger.error('Failed to load S3 data:', result.error);
    }

    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    const result = await s3Api.getSummary(true);

    if (result.success) {
      setData(result.data);
      logger.info('S3 data refreshed');
    } else {
      setError(result.error);
    }

    setRefreshing(false);
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatNumber = (num) => {
    if (!num || num === 0) return '0';
    return num.toLocaleString();
  };

  const getTotalStorage = () => {
    if (!data?.buckets) return 0;
    return data.buckets.reduce((sum, bucket) => sum + (bucket.metrics?.size_bytes || 0), 0);
  };

  const getTotalObjects = () => {
    if (!data?.buckets) return 0;
    return data.buckets.reduce((sum, bucket) => sum + (bucket.metrics?.object_count || 0), 0);
  };

  const getEncryptedBuckets = () => {
    if (!data?.buckets) return 0;
    return data.buckets.filter(b => b.metrics?.encryption_enabled).length;
  };

  const getPublicBuckets = () => {
    if (!data?.buckets) return 0;
    return data.buckets.filter(b => b.metrics?.public_access).length;
  };

  const getRegionDistribution = () => {
    if (!data?.buckets) return [];

    const regions = {};
    data.buckets.forEach(bucket => {
      const region = bucket.region || 'unknown';
      regions[region] = (regions[region] || 0) + 1;
    });

    return Object.entries(regions).map(([name, value]) => ({ name, value }));
  };

  const getStorageByBucket = () => {
    if (!data?.buckets) return [];

    return data.buckets
      .map(bucket => ({
        name: bucket.bucket?.substring(0, 20) || 'Unknown',
        storage: (bucket.metrics?.size_bytes || 0) / (1024 * 1024 * 1024), // Convert to GB
        objects: bucket.metrics?.object_count || 0
      }))
      .sort((a, b) => b.storage - a.storage)
      .slice(0, 10);
  };

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#84cc16'];

  if (loading) {
    return (
      <div className="min-h-screen bg-cosmic-bg-0">
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
      <div className="min-h-screen bg-cosmic-bg-0">
        <Header title="S3 Buckets" showNavigation={true} />
        <main className="p-6 max-w-7xl mx-auto">
          <Card className="p-8 text-center">
            <AlertTriangle className="h-16 w-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-cosmic-txt-1 mb-2">Failed to Load S3 Data</h2>
            <p className="text-cosmic-txt-2 mb-4">{error}</p>
            <Button onClick={fetchS3Data} variant="primary">
              Retry
            </Button>
          </Card>
        </main>
      </div>
    );
  }

  const regionData = getRegionDistribution();
  const storageData = getStorageByBucket();

  return (
    <div className="min-h-screen bg-cosmic-bg-0">
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
                <div className="text-3xl font-bold text-cosmic-txt-1">{formatBytes(getTotalStorage())}</div>
                <div className="text-sm text-cosmic-txt-2">Total Storage</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 animate-fade-in" style={{animationDelay: '0.2s'}}>
            <div className="flex items-center justify-between mb-2">
              <Lock className="h-8 w-8 text-green-400" />
              <div className="text-right">
                <div className="text-3xl font-bold text-cosmic-txt-1">{getEncryptedBuckets()}</div>
                <div className="text-sm text-cosmic-txt-2">Encrypted</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 animate-fade-in" style={{animationDelay: '0.3s'}}>
            <div className="flex items-center justify-between mb-2">
              {getPublicBuckets() > 0 ? (
                <AlertTriangle className="h-8 w-8 text-red-400" />
              ) : (
                <Shield className="h-8 w-8 text-green-400" />
              )}
              <div className="text-right">
                <div className={`text-3xl font-bold ${getPublicBuckets() > 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {getPublicBuckets()}
                </div>
                <div className="text-sm text-cosmic-txt-2">Public Access</div>
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
              <h2 className="text-xl font-semibold text-cosmic-txt-1 mb-4">Top 10 Buckets by Storage</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={storageData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                  <YAxis tick={{ fill: '#9ca3af' }} label={{ value: 'GB', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                    labelStyle={{ color: '#f3f4f6' }}
                    formatter={(value) => `${value.toFixed(2)} GB`}
                  />
                  <Bar dataKey="storage" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>

        {/* Buckets Table */}
        <Card className="p-6 animate-fade-in" style={{animationDelay: '0.6s'}}>
          <h2 className="text-xl font-semibold text-cosmic-txt-1 mb-4">All Buckets ({data?.total_buckets || 0})</h2>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-cosmic-border">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Bucket Name</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Region</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Size</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Objects</th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Encryption</th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-cosmic-txt-1">Public</th>
                </tr>
              </thead>
              <tbody>
                {data?.buckets && data.buckets.length > 0 ? (
                  data.buckets.map((bucket, index) => (
                    <tr key={index} className="border-b border-cosmic-border hover:bg-cosmic-bg-2 transition-colors">
                      <td className="py-3 px-4 text-sm text-cosmic-txt-1 font-medium">{bucket.bucket || 'Unknown'}</td>
                      <td className="py-3 px-4 text-sm text-cosmic-txt-2">{bucket.region || 'unknown'}</td>
                      <td className="py-3 px-4 text-sm text-cosmic-txt-2 text-right">
                        {formatBytes(bucket.metrics?.size_bytes || 0)}
                      </td>
                      <td className="py-3 px-4 text-sm text-cosmic-txt-2 text-right">
                        {formatNumber(bucket.metrics?.object_count || 0)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {bucket.metrics?.encryption_enabled ? (
                          <Lock className="h-4 w-4 text-green-400 inline" />
                        ) : (
                          <Unlock className="h-4 w-4 text-yellow-400 inline" />
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {bucket.metrics?.public_access ? (
                          <Globe className="h-4 w-4 text-red-400 inline" />
                        ) : (
                          <Shield className="h-4 w-4 text-green-400 inline" />
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="py-8 text-center text-cosmic-txt-2">
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
