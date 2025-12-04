// frontend/src/components/common/PermissionErrorBanner.jsx
import React from 'react';
import { AlertTriangle, Lock, ExternalLink } from 'lucide-react';

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
                        <ExternalLink size={14} />
                    </a>
                </div>
            </div>
        </div>
    );
};

export default PermissionErrorBanner;