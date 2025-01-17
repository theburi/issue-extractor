import React, { useEffect, useState } from 'react';
import { fetchReports } from '../services/api';

const Report = () => {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const getReports = async () => {
            try {
                const data = await fetchReports();
                setReports(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        getReports();
    }, []);

    if (loading) {
        return <div>Loading reports...</div>;
    }

    if (error) {
        return <div>Error fetching reports: {error}</div>;
    }

    return (
        <div>
            <h1>Generated Reports</h1>
            <ul>
                {reports.map((report) => (
                    <li key={report.id}>{report.title}</li>
                ))}
            </ul>
        </div>
    );
};

export default Report;