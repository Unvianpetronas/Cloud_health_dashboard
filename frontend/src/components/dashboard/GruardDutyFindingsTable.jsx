/**
 * GuardDuty Findings Table Component
 * Displays all GuardDuty security findings in a detailed table with click-to-expand functionality
 */

import React, { useState } from 'react';
import { Shield, AlertTriangle, Info, MapPin, Clock, Activity, ChevronRight, X, Filter } from 'lucide-react';

const GuardDutyFindingsTable = ({ findings = [], loading = false }) => {
    const [selectedFinding, setSelectedFinding] = useState(null);
    const [severityFilter, setSeverityFilter] = useState('ALL');
    const [sortField, setSortField] = useState('Severity');
    const [sortDirection, setSortDirection] = useState('desc');

    // Filter findings by severity
    const filteredFindings = findings.filter((finding) => {
        if (severityFilter === 'ALL') return true;
        return finding.Severity === severityFilter || finding.severity === severityFilter;
    });

    // Sort findings
    const sortedFindings = [...filteredFindings].sort((a, b) => {
        let aValue, bValue;

        if (sortField === 'Severity') {
            const severityOrder = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
            aValue = severityOrder[a.Severity || a.severity] || 0;
            bValue = severityOrder[b.Severity || b.severity] || 0;
        } else {
            aValue = a[sortField] || '';
            bValue = b[sortField] || '';
        }

        if (sortDirection === 'asc') {
            return aValue > bValue ? 1 : -1;
        }
        return aValue < bValue ? 1 : -1;
    });

    // Get severity color
    const getSeverityColor = (severity) => {
        switch (severity?.toUpperCase()) {
            case 'CRITICAL':
                return 'text-red-500 bg-red-500/10 border-red-500/30';
            case 'HIGH':
                return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
            case 'MEDIUM':
                return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
            case 'LOW':
                return 'text-blue-500 bg-blue-500/10 border-blue-500/30';
            default:
                return 'text-gray-500 bg-gray-500/10 border-gray-500/30';
        }
    };

    // Get severity icon
    const getSeverityIcon = (severity) => {
        switch (severity?.toUpperCase()) {
            case 'CRITICAL':
            case 'HIGH':
                return <AlertTriangle className="w-4 h-4" />;
            case 'MEDIUM':
                return <Info className="w-4 h-4" />;
            case 'LOW':
                return <Shield className="w-4 h-4" />;
            default:
                return <Info className="w-4 h-4" />;
        }
    };

    // Format timestamp
    const formatTimestamp = (timestamp) => {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    };

    // Extract resource info
    const getResourceInfo = (finding) => {
        const resource = finding.Resource || {};
        if (resource.InstanceDetails) {
            return {
                type: 'EC2 Instance',
                id: resource.InstanceDetails.InstanceId || 'N/A'
            };
        } else if (resource.AccessKeyDetails) {
            return {
                type: 'Access Key',
                id: resource.AccessKeyDetails.AccessKeyId || 'N/A'
            };
        } else if (resource.S3BucketDetails) {
            const buckets = resource.S3BucketDetails || [];
            return {
                type: 'S3 Bucket',
                id: buckets.length > 0 ? buckets[0].Name : 'N/A'
            };
        }
        return {
            type: finding.resource_type || 'Unknown',
            id: finding.resource_id || 'N/A'
        };
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

    if (!findings || findings.length === 0) {
        return (
            <div className="text-center py-12 text-cosmic-txt-2">
                <Shield className="w-16 h-16 mx-auto mb-4 opacity-50 text-green-400" />
                <p className="text-lg">No security findings</p>
                <p className="text-sm mt-2">Your AWS account is secure!</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Table Header with Filters */}
            <div className="flex items-center justify-between flex-wrap gap-4">
                <h3 className="text-lg font-semibold text-cosmic-txt-1 flex items-center">
                    <Shield className="w-5 h-5 mr-2 text-purple-400" />
                    GuardDuty Findings ({filteredFindings.length})
                </h3>

                {/* Severity Filter */}
                <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-cosmic-txt-2" />
                    <select
                        value={severityFilter}
                        onChange={(e) => setSeverityFilter(e.target.value)}
                        className="bg-cosmic-bg-2 border border-cosmic-border text-cosmic-txt-1 px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cosmic-blue"
                    >
                        <option value="ALL">All Severities</option>
                        <option value="CRITICAL">Critical</option>
                        <option value="HIGH">High</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="LOW">Low</option>
                    </select>
                </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto rounded-lg border border-cosmic-border">
                <table className="w-full">
                    <thead className="bg-cosmic-bg-2">
                        <tr>
                            <th className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider">
                                Severity
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider">
                                Finding
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider">
                                Resource
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider">
                                Region
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider">
                                Last Seen
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-medium text-cosmic-txt-2 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-cosmic-border">
                        {sortedFindings.map((finding, index) => {
                            const severity = finding.Severity || finding.severity || 'UNKNOWN';
                            const resource = getResourceInfo(finding);

                            return (
                                <tr
                                    key={finding.Id || finding.id || index}
                                    className="hover:bg-cosmic-bg-2 transition-colors cursor-pointer"
                                    onClick={() => setSelectedFinding(finding)}
                                >
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${getSeverityColor(severity)}`}>
                                            {getSeverityIcon(severity)}
                                            {severity}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col max-w-md">
                                            <span className="text-sm font-medium text-cosmic-txt-1 line-clamp-1">
                                                {finding.Title || finding.title || 'Unknown Finding'}
                                            </span>
                                            <span className="text-xs text-cosmic-txt-2 line-clamp-2 mt-1">
                                                {finding.Description || finding.description || 'No description available'}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col">
                                            <span className="text-sm text-cosmic-txt-1">{resource.type}</span>
                                            <span className="text-xs text-cosmic-txt-2 font-mono">{resource.id}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-sm text-cosmic-txt-1">{finding.Region || finding.region || 'N/A'}</span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-xs text-cosmic-txt-2">
                                            {formatTimestamp(finding.UpdatedAt || finding.CreatedAt || finding.timestamp)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <button
                                            className="text-blue-400 hover:text-blue-300 transition-colors text-sm flex items-center"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setSelectedFinding(finding);
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
            {selectedFinding && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-cosmic-card-bg border border-cosmic-border rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-scale-in">
                        {/* Modal Header */}
                        <div className="sticky top-0 bg-cosmic-card-bg border-b border-cosmic-border px-6 py-4 flex items-center justify-between">
                            <div className="flex items-center">
                                <div className={`p-2 rounded-lg ${getSeverityColor(selectedFinding.Severity || selectedFinding.severity)} mr-3`}>
                                    {getSeverityIcon(selectedFinding.Severity || selectedFinding.severity)}
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-cosmic-txt-1">
                                        Security Finding Details
                                    </h2>
                                    <p className="text-sm text-cosmic-txt-2">
                                        {selectedFinding.Type || selectedFinding.type || 'Unknown Type'}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSelectedFinding(null)}
                                className="p-2 hover:bg-cosmic-bg-2 rounded-lg transition-colors"
                            >
                                <X className="w-6 h-6 text-cosmic-txt-2" />
                            </button>
                        </div>

                        {/* Modal Content */}
                        <div className="p-6 space-y-6">
                            {/* Finding Overview */}
                            <section>
                                <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                    <AlertTriangle className="w-5 h-5 mr-2 text-orange-400" />
                                    Finding Overview
                                </h3>
                                <div className="space-y-4">
                                    <div className="bg-cosmic-bg-2 rounded-lg p-4 border border-cosmic-border">
                                        <div className="text-xs text-cosmic-txt-2 mb-2">Title</div>
                                        <div className="text-base text-cosmic-txt-1 font-semibold">
                                            {selectedFinding.Title || selectedFinding.title || 'Unknown Finding'}
                                        </div>
                                    </div>
                                    <div className="bg-cosmic-bg-2 rounded-lg p-4 border border-cosmic-border">
                                        <div className="text-xs text-cosmic-txt-2 mb-2">Description</div>
                                        <div className="text-sm text-cosmic-txt-1 leading-relaxed">
                                            {selectedFinding.Description || selectedFinding.description || 'No description available'}
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <InfoItem
                                            label="Severity"
                                            value={
                                                <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${getSeverityColor(selectedFinding.Severity || selectedFinding.severity)}`}>
                                                    {getSeverityIcon(selectedFinding.Severity || selectedFinding.severity)}
                                                    {selectedFinding.Severity || selectedFinding.severity || 'UNKNOWN'}
                                                </span>
                                            }
                                        />
                                        <InfoItem label="Type" value={selectedFinding.Type || selectedFinding.type || 'Unknown'} />
                                        <InfoItem label="Finding ID" value={selectedFinding.Id || selectedFinding.id || 'N/A'} />
                                    </div>
                                </div>
                            </section>

                            {/* Resource Information */}
                            <section>
                                <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                    <Activity className="w-5 h-5 mr-2 text-blue-400" />
                                    Affected Resource
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <InfoItem label="Resource Type" value={getResourceInfo(selectedFinding).type} />
                                    <InfoItem label="Resource ID" value={getResourceInfo(selectedFinding).id} />
                                    <InfoItem label="Account ID" value={selectedFinding.AccountId || selectedFinding.account_id || 'N/A'} />
                                    <InfoItem label="Region" value={selectedFinding.Region || selectedFinding.region || 'N/A'} />
                                </div>
                            </section>

                            {/* Service Information */}
                            {selectedFinding.Service && (
                                <section>
                                    <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                        <Clock className="w-5 h-5 mr-2 text-yellow-400" />
                                        Timeline
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <InfoItem
                                            label="First Seen"
                                            value={formatTimestamp(selectedFinding.Service.EventFirstSeen || selectedFinding.CreatedAt)}
                                        />
                                        <InfoItem
                                            label="Last Seen"
                                            value={formatTimestamp(selectedFinding.Service.EventLastSeen || selectedFinding.UpdatedAt)}
                                        />
                                        <InfoItem
                                            label="Count"
                                            value={selectedFinding.Service.Count || 1}
                                        />
                                    </div>
                                </section>
                            )}

                            {/* Additional Details */}
                            {selectedFinding.Resource && (
                                <section>
                                    <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                                        <MapPin className="w-5 h-5 mr-2 text-green-400" />
                                        Additional Details
                                    </h3>
                                    <div className="bg-cosmic-bg-2 rounded-lg p-4 border border-cosmic-border">
                                        <pre className="text-xs text-cosmic-txt-1 overflow-x-auto">
                                            {JSON.stringify(selectedFinding.Resource, null, 2)}
                                        </pre>
                                    </div>
                                </section>
                            )}

                            {/* Recommendations */}
                            <section>
                                <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4">Recommended Actions</h3>
                                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                                    <ul className="space-y-2 text-sm text-cosmic-txt-1">
                                        <li className="flex items-start">
                                            <span className="text-blue-400 mr-2">•</span>
                                            <span>Review the finding details and assess the security impact</span>
                                        </li>
                                        <li className="flex items-start">
                                            <span className="text-blue-400 mr-2">•</span>
                                            <span>Investigate the affected resource for any unauthorized changes</span>
                                        </li>
                                        <li className="flex items-start">
                                            <span className="text-blue-400 mr-2">•</span>
                                            <span>Follow AWS security best practices to remediate the issue</span>
                                        </li>
                                        <li className="flex items-start">
                                            <span className="text-blue-400 mr-2">•</span>
                                            <span>Archive the finding once resolved in AWS GuardDuty console</span>
                                        </li>
                                    </ul>
                                </div>
                            </section>
                        </div>

                        {/* Modal Footer */}
                        <div className="sticky bottom-0 bg-cosmic-card-bg border-t border-cosmic-border px-6 py-4 flex justify-between items-center">
                            <a
                                href={`https://console.aws.amazon.com/guardduty/home?region=${selectedFinding.Region || 'us-east-1'}#/findings?search=id%3D${selectedFinding.Id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center"
                            >
                                View in AWS Console →
                            </a>
                            <button
                                onClick={() => setSelectedFinding(null)}
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

export default GuardDutyFindingsTable;