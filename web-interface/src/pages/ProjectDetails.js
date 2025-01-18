import React from 'react';
import { useRecordContext } from 'react-admin';

const ProjectDetails = () => {
    const record = useRecordContext(); // Access the selected project's data
    if (!record) return null;

    return (
        <div>            
            <h3>Issues</h3>
            {/* <ul>
                {record.issues && record.issues.map((issue) => (
                    <li key={issue.id}>{issue.description}</li>
                ))}
            </ul> */}
            <h3>Processed Issues</h3>
            {/* <ul>
                {record.processedIssues && record.processedIssues.map((issue) => (
                    <li key={issue.id}>{issue.result}</li>
                ))}
            </ul> */}
        </div>
    );
};

export default ProjectDetails;