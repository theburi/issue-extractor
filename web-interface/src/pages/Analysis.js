import React, { useEffect, useState } from 'react';
import { fetchAnalysisData } from '../services/api'; // Ensure this is correctly exported from api.js

const Analysis = () => {
    const [data, setData] = useState(null);

    useEffect(() => {
        const getData = async () => {
            try {
                const result = await fetchAnalysisData();
                setData(result);
            } catch (error) {
                console.error('Error fetching analysis data:', error);
            }
        };

        getData();
    }, []);

    return (
        <div>
            <h1>Analysis</h1>
            {data ? (
                <pre>{JSON.stringify(data, null, 2)}</pre>
            ) : (
                <p>Loading...</p>
            )}
        </div>
    );
};

export default Analysis;