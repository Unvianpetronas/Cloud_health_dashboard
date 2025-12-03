/**
 * EC2 Instances Table Component
 * Displays all EC2 instances in a detailed table with click-to-expand functionality
 */

import React, { useState } from 'react';
import { Server, MapPin, Activity, DollarSign, Clock, Tag, ChevronDown, ChevronRight, X } from 'lucide-react';

const EC2InstancesTable = ({ instances = [], loading = false }) => {
    const [selectedInstance, setSelectedInstance] = useState(null);
    const [sortField, setSortField] = useState('InstanceId');
    const [sortDirection, setSortDirection] = useState('asc');

    // Sort instances
    const sortedInstances = [...instances].sort((a, b) => {
        const aValue = a[sortField] || '';
        const bValue = b[sortField] || '';

        if (sortDirection === 'asc') {
            return aValue > bValue ? 1 : -1;
        }
        return aValue < bValue ? 1 : -1;
    });

    // Handle sort click
    const handleSort = (field) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('asc');
        }
    };

    // Get state color
    const getStateColor = (state) => {
        switch (state?.toLowerCase()) {
            case 'running':
                return 'text-green-400 bg-green-400/10 border-green-400/30';
            case 'stopped':
                return 'text-red-400 bg-red-400/10 border-red-400/30';
            case 'pending':
                return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
            case 'stopping':
            case 'shutting-down':
                return 'text-orange-400 bg-orange-400/10 border-orange-400/30';
            default:
                return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
        }
    };

    // Format launch time
    const formatLaunchTime = (launchTime) => {
        if (!launchTime) return 'N/A';
        const date = new Date(launchTime);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    };

    // Extract instance name from tags
    const getInstanceName = (tags) => {
        if (!tags || tags.length === 0) return 'Unnamed Instance';
        const nameTag = tags.find(tag => tag.Key === 'Name');
        return nameTag ? nameTag.Value : 'Unnamed Instance';
    };

    if (loading) {
        return (
            <div className="animate-pulse space-y-4">
                <div className="h-12 bg-cosmic-bg-2 rounded"></div>
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-16 bg-cosmic-bg-2 rounded"></div>
                ))}
            </div>
        );
    }

    if (!instances || instances.length === 0) {
        return (
            <div className="text-center py-12 text-cosmic-txt-2">
                <Server className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">No EC2 instances found</p>
                <p className="text-sm mt-2">Launch some instances to see them here</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Table Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-cosmic-txt-1 flex items-center">
                    <Server className="w-5 h-5 mr-2 text-blue-400" />
                    EC2 Instances ({instances.length})
                </h3>
            </div>

            {/* Table */}
            <div className="overflow-x-auto rounded-lg border border-cosmic-border">
                <table className="w-full">
                    <thead className="bg-cosmic-bg-2">
                        <tr>
                            <th
                                className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider cursor-pointer hover:text-cosmic-txt-1"
                                onClick={() => handleSort('InstanceId')}
                            >
                                Instance
                            </th>
                            <th
                                className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider cursor-pointer hover:text-cosmic-txt-1"
                                onClick={() => handleSort('InstanceType')}
                            >
                                Type
                            </th>
                            <th
                                className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider cursor-pointer hover:text-cosmic-txt-1"
                                onClick={() => handleSort('State')}
                            >
                                State
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider">
                                Region / AZ
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider">
                                IP Address
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-cosmic-border">
                        {sortedInstances.map((instance) => {
                            const state = instance.State?.Name || instance.state || 'unknown';
                            const instanceName = getInstanceName(instance.Tags || instance.tags);

                            return (
                                <tr
                                    key={instance.InstanceId}
                                    className="hover:bg-cosmic-bg-2 transition-colors cursor-pointer"
                                    onClick={() => setSelectedInstance(instance)}
                                >
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col">
                                            <span className="text-sm font-medium text-cosmic-txt-1">
                                                {instanceName}
                                            </span>
                                            <span className="text-xs text-cosmic-txt-2 font-mono">
                                                {instance.InstanceId}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-sm text-cosmic-txt-1 font-mono bg-cosmic-bg-2 px-2 py-1 rounded">
                                            {instance.InstanceType}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getStateColor(state)}`}>
                                            {state}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col text-sm">
                                            <span className="text-cosmic-txt-1">{instance.Region || instance.region || 'N/A'}</span>
                                            <span className="text-xs text-cosmic-txt-2">{instance.Placement?.AvailabilityZone || 'N/A'}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col text-xs">
                                            <span className="text-cosmic-txt-1 font-mono">
                                                {instance.PublicIpAddress || instance.public_ip || '-'}
                                            </span>
                                            <span className="text-cosmic-txt-2 font-mono">
                                                {instance.PrivateIpAddress || instance.private_ip || '-'}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <button
                                            className="text-blue-400 hover:text-blue-300 transition-colors text-sm flex items-center"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setSelectedInstance(instance);
                                            }}
                                        >
                                            <ChevronRight className="w-4 h-4 mr-1" />
                                            Details
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Detail Modal */}
            {selectedInstance && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-cosmic-card-bg border border-cosmic-border rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-scale-in">
                        {/* Modal Header */}
                        <div className="sticky top-0 bg-cosmic-bg-1 backdrop-blur-md border-b border-cosmic-border px-6 py-4 flex items-center justify-between z-10">
                            <div className="flex items-center">
                                <Server className="w-6 h-6 text-blue-400 mr-3" />
                                <div>
                                    <h2 className="text-xl font-bold text-cosmic-txt-1">
                                        {getInstanceName(selectedInstance.Tags || selectedInstance.tags)}
                                    </h2>
                                    <p className="text-sm text-cosmic-txt-2 font-mono">
                                        {selectedInstance.InstanceId}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSelectedInstance(null)}
                                className="p-2 hover:bg-cosmic-bg-2 rounded-lg transition-colors"
                            >
                                <X className="w-6 h-6 text-cosmic-txt-2" />
                            </button>
                        </div>

                        {/* Modal Content */}
                        <div className="p-6 space-y-6">
                            {/* Instance Information */}
                            <section>
                                <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                    <Activity className="w-5 h-5 mr-2 text-green-400" />
                                    Instance Information
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <InfoItem label="Instance ID" value={selectedInstance.InstanceId} />
                                    <InfoItem label="Instance Type" value={selectedInstance.InstanceType} />
                                    <InfoItem
                                        label="State"
                                        value={
                                            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStateColor(selectedInstance.State?.Name || selectedInstance.state)}`}>
                                                {selectedInstance.State?.Name || selectedInstance.state || 'unknown'}
                                            </span>
                                        }
                                    />
                                    <InfoItem label="Architecture" value={selectedInstance.Architecture || 'N/A'} />
                                    <InfoItem label="Platform" value={selectedInstance.Platform || 'Linux/Unix'} />
                                    <InfoItem label="Virtualization Type" value={selectedInstance.VirtualizationType || 'N/A'} />
                                </div>
                            </section>

                            {/* Network Information */}
                            <section>
                                <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                    <MapPin className="w-5 h-5 mr-2 text-purple-400" />
                                    Network & Location
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <InfoItem label="Region" value={selectedInstance.Region || selectedInstance.region || 'N/A'} />
                                    <InfoItem label="Availability Zone" value={selectedInstance.Placement?.AvailabilityZone || 'N/A'} />
                                    <InfoItem label="Public IP" value={selectedInstance.PublicIpAddress || '-'} />
                                    <InfoItem label="Private IP" value={selectedInstance.PrivateIpAddress || '-'} />
                                    <InfoItem label="VPC ID" value={selectedInstance.VpcId || 'N/A'} />
                                    <InfoItem label="Subnet ID" value={selectedInstance.SubnetId || 'N/A'} />
                                    <InfoItem label="Public DNS" value={selectedInstance.PublicDnsName || '-'} />
                                    <InfoItem label="Private DNS" value={selectedInstance.PrivateDnsName || '-'} />
                                </div>
                            </section>

                            {/* Launch Information */}
                            <section>
                                <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                    <Clock className="w-5 h-5 mr-2 text-yellow-400" />
                                    Launch Information
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <InfoItem label="Launch Time" value={formatLaunchTime(selectedInstance.LaunchTime)} />
                                    <InfoItem label="Image ID" value={selectedInstance.ImageId || 'N/A'} />
                                    <InfoItem label="Key Name" value={selectedInstance.KeyName || 'None'} />
                                    <InfoItem label="IAM Instance Profile" value={selectedInstance.IamInstanceProfile?.Arn || 'None'} />
                                </div>
                            </section>

                            {/* Tags */}
                            {(selectedInstance.Tags || selectedInstance.tags) && (selectedInstance.Tags?.length > 0 || selectedInstance.tags?.length > 0) && (
                                <section>
                                    <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                        <Tag className="w-5 h-5 mr-2 text-pink-400" />
                                        Tags
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        {(selectedInstance.Tags || selectedInstance.tags).map((tag, index) => (
                                            <div key={index} className="bg-cosmic-bg-2 rounded-lg p-3 border border-cosmic-border">
                                                <div className="text-xs text-cosmic-txt-2 mb-1">{tag.Key}</div>
                                                <div className="text-sm text-cosmic-txt-1 font-medium">{tag.Value}</div>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Security Groups */}
                            {selectedInstance.SecurityGroups && selectedInstance.SecurityGroups.length > 0 && (
                                <section>
                                    <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4">Security Groups</h3>
                                    <div className="space-y-2">
                                        {selectedInstance.SecurityGroups.map((sg, index) => (
                                            <div key={index} className="bg-cosmic-bg-2 rounded-lg p-3 border border-cosmic-border flex items-center justify-between">
                                                <div>
                                                    <div className="text-sm text-cosmic-txt-1 font-medium">{sg.GroupName}</div>
                                                    <div className="text-xs text-cosmic-txt-2 font-mono">{sg.GroupId}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}
                        </div>

                        {/* Modal Footer */}
                        <div className="sticky bottom-0 bg-cosmic-card-bg border-t border-cosmic-border px-6 py-4 flex justify-end">
                            <button
                                onClick={() => setSelectedInstance(null)}
                                className="px-6 py-2 bg-cosmic-blue hover:bg-cosmic-blue-light text-white rounded-lg transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Info Item Component
const InfoItem = ({ label, value }) => (
    <div className="bg-cosmic-bg-2 rounded-lg p-4 border border-cosmic-border">
        <div className="text-xs text-cosmic-txt-2 mb-1">{label}</div>
        <div className="text-sm text-cosmic-txt-1 font-medium break-all">
            {value || 'N/A'}
        </div>
    </div>
);

export default EC2InstancesTable;