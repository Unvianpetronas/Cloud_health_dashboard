import { useState, useEffect } from 'react';

const STORAGE_KEYS = {
    AUTO_REFRESH: 'dashboard_autoRefresh',
    REFRESH_INTERVAL: 'dashboard_refreshInterval'
};

export const useAutoRefresh = (refreshCallback) => {
    const [isEnabled, setIsEnabled] = useState(true);
    const [interval, setIntervalMs] = useState(300000); // 5 min default

    useEffect(() => {
        // Load from localStorage
        const autoRefresh = localStorage.getItem(STORAGE_KEYS.AUTO_REFRESH);
        const refreshInterval = localStorage.getItem(STORAGE_KEYS.REFRESH_INTERVAL);

        setIsEnabled(autoRefresh !== null ? autoRefresh === 'true' : true);
        setIntervalMs((refreshInterval ? parseInt(refreshInterval) : 300) * 1000);
    }, []);

    useEffect(() => {
        if (!isEnabled || !refreshCallback) return;

        const timer = setInterval(() => {
            refreshCallback();
        }, interval);

        return () => clearInterval(timer);
    }, [isEnabled, interval, refreshCallback]);

    return { isEnabled, intervalSeconds: interval / 1000 };
};