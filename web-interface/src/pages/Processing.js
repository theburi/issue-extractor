import React, { useState, useEffect } from 'react';
import { useNotify, Title, Button, SimpleForm, SelectInput, TextField } from 'react-admin';
import { Box } from '@mui/system';
import CircularProgress from '@mui/material/CircularProgress';

// API service functions
const apiService = {
    fetchProjects: () => fetch('/api/projects').then(res => res.json()),
    fetchIssueCount: (projectId) => fetch(`/api/issues/count?project=${projectId}`).then(res => res.json()),
    fetchTaskStatus: (taskId) => fetch(`/api/jira/status/${taskId}`).then(res => res.json()),
    startExtraction: (projectId) => fetch(`/api/jira/extract?project=${projectId}`).then(res => res.json()),
};

// Custom hook for task polling
const useTaskPolling = (taskId, onStatusChange) => {
    useEffect(() => {
        if (!taskId) return;

        const pollInterval = setInterval(async () => {
            try {
                const data = await apiService.fetchTaskStatus(taskId);
                onStatusChange(data);

                // Stop polling if the task is completed or failed
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);
                }
            } catch (error) {
                console.error('Polling error:', error);
                clearInterval(pollInterval);
            }
        }, 3000);

        return () => clearInterval(pollInterval);
    }, [taskId, onStatusChange]);
};

const Processing = () => {
    const [loading, setLoading] = useState({
        projects: false,
        processing: false,
    });
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState('');
    const [task, setTask] = useState({
        id: null,
        status: null,
        issueCount: null,
    });
    const notify = useNotify();

    // Projects fetch
    useEffect(() => {
        const loadProjects = async () => {
            setLoading(prev => ({ ...prev, projects: true }));
            try {
                const data = await apiService.fetchProjects();
                setProjects(data);
            } catch (error) {
                notify('Failed to load projects', { type: 'error' });
            } finally {
                setLoading(prev => ({ ...prev, projects: false }));
            }
        };
        loadProjects();
    }, [notify]);

    // Issue count fetch
    useEffect(() => {
        if (!selectedProject) {
            setTask(prev => ({ ...prev, issueCount: null }));
            return;
        }

        const loadIssueCount = async () => {
            try {
                const data = await apiService.fetchIssueCount(selectedProject);
                setTask(prev => ({ ...prev, issueCount: data.count || 0 }));
            } catch (error) {
                notify('Failed to fetch issue count', { type: 'error' });
            }
        };
        loadIssueCount();
    }, [selectedProject, notify]);

    // Task status polling
    useTaskPolling(task.id, (statusData) => {
        setTask(prev => ({ ...prev, status: statusData }));
        if (statusData.status === 'completed') {
            setLoading(prev => ({ ...prev, processing: false }));
            setTask(prev => ({ ...prev, id: null }));
            notify('Processing completed', { type: 'info' });
        } else if (statusData.status === 'failed') {
            setLoading(prev => ({ ...prev, processing: false }));
            setTask(prev => ({ ...prev, id: null }));
            notify(`Processing failed: ${statusData.result}`, { type: 'error' });
        }
    });

    const handleButtonClick = async () => {
        if (!selectedProject) {
            notify('Please select a project before processing', { type: 'warning' });
            return;
        }

        setLoading(prev => ({ ...prev, processing: true }));
        notify('Processing started', { type: 'info' });

        try {
            const data = await apiService.startExtraction(selectedProject);
            setTask(prev => ({ ...prev, id: data.task_id, status: null }));
        } catch (error) {
            setLoading(prev => ({ ...prev, processing: false }));
            notify('Failed to start processing', { type: 'error' });
        }
    };

    return (
        <Box m={2}>
            <Title title="Processing Page" />

            <Box display="flex" flexDirection="column" gap={2}>
                <h2>Jira Extraction</h2>
                <SimpleForm toolbar={null}>
                {/* Dropdown to select project */}
                <SelectInput
                    source="project"
                    label="Select Project"
                    choices={projects.map((project) => ({
                        id: project.id, // Adjust if your API uses a different key for ID
                        name: project.name, // Adjust if your API uses a different key for Name
                    }))}
                    optionText="name"
                    optionValue="id"
                    value={selectedProject}
                    onChange={(event) => setSelectedProject(event.target.value)}
                    fullWidth
                />
                {/* Display selected project's source */}                 
                {selectedProject && (
                    <Box mt={2}>
                        <strong>JIRA Query:</strong>{' '}
                        <TextField
                            source="jira_source"
                            label="JIRA Query"
                            record={{ jira_source: projects.find((project) => project.id === selectedProject)?.jira_source || "No source available" }}
                        />
                    </Box>
                )}
                </SimpleForm>
                {loading.processing ? (
                    <Box display="flex" justifyContent="center" alignItems="center" mt={2}>
                        <CircularProgress />
                    </Box>
                ) : (
                    <Button
                        label="Start Processing"
                        onClick={handleButtonClick}
                        disabled={!selectedProject}
                    />
                )}
                            {/* Show task status */}
                <Box mt={2}>
                    {task.status ? (
                        <p>
                            Task Status: {task.status.status}
                            {task.status.result && (
                                <>
                                    <br />
                                    Result: {task.status.result}
                                </>
                            )}
                        </p>
                    ) : (
                        task.id && <p>Checking task status...</p>
                    )}
                </Box>
            </Box>
            
            {/* Display the number of issues for the selected project */}
            <Box mt={2}>
                {task.issueCount !== null ? (
                    <p>Number of issues for this project: {task.issueCount}</p>
                ) : (
                    <p>Select a project to view the issue count.</p>
                )}
            </Box>
        </Box>
    );
};

export default Processing;