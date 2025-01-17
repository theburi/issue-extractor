import React, { useEffect, useState } from 'react';
import axios from 'axios';

const Dashboard = () => {
  const [issueStats, setIssueStats] = useState([]);
  const [processedIssueStats, setProcessedIssueStats] = useState([]);

  useEffect(() => {
    // Fetch statistics for issues
    axios.get('/issues/stats')
      .then(response => {
        console.log(response.data);
       setIssueStats(response.data);}) 
      .catch(error => console.error('Error fetching issue stats:', error));

    // Fetch statistics for processed issues
    axios.get('/processed_issues/stats')
      .then(response => setProcessedIssueStats(response.data))
      .catch(error => console.error('Error fetching processed issue stats:', error));
  }, []);

  return (
    <div>
      <h1>Admin Dashboard</h1>
      <div>
        <h2>Issue Statistics</h2>
        {issueStats.length > 0 ? (
          <ul>
            {issueStats.map((stat, index) => (
              <li key={index}>
                <strong>{stat._id}:</strong> {stat.count}
              </li>
            ))}
          </ul>
        ) : (
          <p>Loading issue statistics...</p>
        )}
      </div>
      <div>
        <h2>Processed Issue Statistics</h2>
        {processedIssueStats.length > 0 ? (
          <ul>
            {processedIssueStats.map((stat, index) => (
              <li key={index}>
                <strong>{stat._id}:</strong> {stat.count}
              </li>
            ))}
          </ul>
        ) : (
          <p>Loading processed issue statistics...</p>
        )}
      </div>
    </div>
  );
};

export default Dashboard;