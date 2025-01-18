import React, { useEffect, useState } from 'react';
import { useRecordContext } from 'react-admin';
import axios from 'axios';

const ProjectReports = () => {
    const record = useRecordContext(); // Access the selected project's data
    const [reports, setReports] = useState([]);

    useEffect(() => {
        if (record) {
            axios.get(`/api/reports?projectId=${record.id}`)
                .then((response) => setReports(response.data))
                .catch((error) => console.error('Error fetching reports:', error));
        }
    }, [record]);

    if (!record) return null;

    return (
        <div>
            <h3>Reports for Project: {record.name}</h3>
            <ul>
                {reports.map((report) => (
                    <li key={report.id}>
                        <a href={report.url} target="_blank" rel="noopener noreferrer">{report.title}</a>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default ProjectReports;