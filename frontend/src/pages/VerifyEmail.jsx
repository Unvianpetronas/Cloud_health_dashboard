import React, { useState, useEffect } from 'react';

import { useNavigate, useSearchParams } from 'react-router-dom';

import { CheckCircle, XCircle, Loader } from 'lucide-react';

import { settingsApi } from '../services/settingsApi';

import Button from '../components/common/Button';

import logger from '../utils/logger';



const VerifyEmail = () => {

    const [searchParams] = useSearchParams();

    const navigate = useNavigate();

    const [status, setStatus] = useState('verifying'); // verifying, success, error

    const [message, setMessage] = useState('');



    useEffect(() => {

        verifyEmailToken();

    }, []);



    const verifyEmailToken = async () => {

        const token = searchParams.get('token');



        if (!token) {

            setStatus('error');

            setMessage('No verification token provided. Please check your email link.');

            logger.error('No token in URL');

            return;

        }



        logger.info('Verifying email with token:', token.substring(0, 10) + '...');



        const result = await settingsApi.verifyEmail(token);



        if (result.success) {

            setStatus('success');

            setMessage(result.message || 'Your email has been verified successfully!');

            logger.info('Email verified successfully');



            // Redirect to settings page after 3 seconds

            setTimeout(() => {

                navigate('/settings');

            }, 3000);

        } else {

            setStatus('error');

            setMessage(result.error || 'Failed to verify email. The link may be expired or invalid.');

            logger.error('Email verification failed:', result.error);

        }

    };



    return (

        <div className="min-h-screen bg-cosmic-bg-0 flex items-center justify-center p-6">

            <div className="max-w-md w-full">

                {/* Verification Card */}

                <div className="bg-cosmic-bg-1 border border-cosmic-border rounded-2xl shadow-cosmic-glow overflow-hidden">

                    {/* Header */}

                    <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-8 text-center">

                        <div className="text-6xl mb-4">☁️</div>

                        <h1 className="text-2xl font-bold text-white">AWS Cloud Health Dashboard</h1>

                    </div>



                    {/* Content */}

                    <div className="p-8">

                        {status === 'verifying' && (

                            <div className="text-center">

                                <div className="flex justify-center mb-6">

                                    <Loader className="h-16 w-16 text-blue-500 animate-spin" />

                                </div>

                                <h2 className="text-xl font-semibold text-cosmic-txt-1 mb-2">

                                    Verifying Your Email

                                </h2>

                                <p className="text-cosmic-txt-2">

                                    Please wait while we verify your email address...

                                </p>

                            </div>

                        )}



                        {status === 'success' && (

                            <div className="text-center">

                                <div className="flex justify-center mb-6">

                                    <div className="h-16 w-16 bg-green-500/20 rounded-full flex items-center justify-center">

                                        <CheckCircle className="h-10 w-10 text-green-500" />

                                    </div>

                                </div>

                                <h2 className="text-xl font-semibold text-cosmic-txt-1 mb-2">

                                    Email Verified!

                                </h2>

                                <p className="text-cosmic-txt-2 mb-6">

                                    {message}

                                </p>

                                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 mb-6">

                                    <p className="text-sm text-cosmic-txt-2">

                                        You can now enable email notifications in your settings to receive:

                                    </p>

                                    <ul className="text-sm text-cosmic-txt-2 mt-2 space-y-1">

                                        <li>• Critical security alerts</li>

                                        <li>• Daily health summaries</li>

                                        <li>• Cost anomaly notifications</li>

                                    </ul>

                                </div>

                                <p className="text-sm text-cosmic-txt-2 mb-4">

                                    Redirecting to settings in 3 seconds...

                                </p>

                                <Button

                                    onClick={() => navigate('/settings')}

                                    variant="primary"

                                    className="w-full"

                                >

                                    Go to Settings Now

                                </Button>

                            </div>

                        )}



                        {status === 'error' && (

                            <div className="text-center">

                                <div className="flex justify-center mb-6">

                                    <div className="h-16 w-16 bg-red-500/20 rounded-full flex items-center justify-center">

                                        <XCircle className="h-10 w-10 text-red-500" />

                                    </div>

                                </div>

                                <h2 className="text-xl font-semibold text-cosmic-txt-1 mb-2">

                                    Verification Failed

                                </h2>

                                <p className="text-cosmic-txt-2 mb-6">

                                    {message}

                                </p>

                                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 mb-6">

                                    <p className="text-sm text-cosmic-txt-2">

                                        <strong>Common reasons:</strong>

                                    </p>

                                    <ul className="text-sm text-cosmic-txt-2 mt-2 space-y-1 text-left">

                                        <li>• The verification link has expired (24 hours)</li>

                                        <li>• The link has already been used</li>

                                        <li>• The link is invalid or malformed</li>

                                    </ul>

                                </div>

                                <div className="space-y-2">

                                    <Button

                                        onClick={() => navigate('/settings')}

                                        variant="primary"

                                        className="w-full"

                                    >

                                        Go to Settings

                                    </Button>

                                    <p className="text-sm text-cosmic-txt-2">

                                        You can request a new verification email from the settings page.

                                    </p>

                                </div>

                            </div>

                        )}

                    </div>



                    {/* Footer */}

                    <div className="bg-cosmic-bg-2 border-t border-cosmic-border p-4 text-center">

                        <p className="text-xs text-cosmic-txt-2">

                            © 2025 AWS Cloud Health Dashboard

                        </p>

                    </div>

                </div>



                {/* Back to Login */}

                <div className="text-center mt-6">

                    <button

                        onClick={() => navigate('/login')}

                        className="text-sm text-cosmic-txt-2 hover:text-cosmic-txt-1 transition-colors"

                    >

                        Back to Login

                    </button>

                </div>

            </div>

        </div>

    );

};



export default VerifyEmail;

