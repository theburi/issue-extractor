import React, { useState, useEffect } from 'react';
import { useNotify, Title, Button, SimpleForm, SelectInput } from 'react-admin';
import { Box } from '@mui/system';
import CircularProgress from '@mui/material/CircularProgress';
import DOMPurify from 'dompurify';

// API service functions
const apiService = {
    fetchProjects: () => fetch('/api/projects').then((res) => res.json()),
    fetchIssueCount: (projectId) => fetch(`/api/issues/count?project=${projectId}`).then((res) => res.json()),
    fetchTaskStatus: (apiPath, taskId) => fetch(`${apiPath}/${taskId}`).then((res) => res.json()),
    startExtraction: (projectId) => fetch(`/api/jira/extract?project=${projectId}`).then((res) => res.json()),
    fetchProcessStage: (projectId, stage) =>
        fetch(`/api/process?project_id=${projectId}&stage=${stage}`).then((res) => res.json()),
    fetchReport: (projectId) => fetch(`/api/reports?projectid=${projectId}`).then((res) => res.json()),
};

// Custom hook for task polling
const useTaskPolling = (taskId, apiPath, onStatusChange) => {
    useEffect(() => {
        if (!taskId || !apiPath) return;

        const pollInterval = setInterval(async () => {
            try {
                const data = await apiService.fetchTaskStatus(apiPath, taskId);
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

        return () => clearInterval(pollInterval); // Cleanup on unmount or dependency change
    }, [taskId, apiPath, onStatusChange]);
};

const Processing = () => {
    const [loading, setLoading] = useState({
        projects: false,
        processing: false,
        stageProcessing: false,
    });
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState('');
    const [jiraTask, setJiraTask] = useState({ id: null, status: null });
    const [processTask, setProcessTask] = useState({ id: null, status: null });
    const [selectedStage, setSelectedStage] = useState('');
    const [report, setReport] = useState(null); // Declare state for the report
    
    const notify = useNotify();

    // Fetch projects
    useEffect(() => {
        const loadProjects = async () => {
            setLoading((prev) => ({ ...prev, projects: true }));
            try {
                const data = await apiService.fetchProjects();
                setProjects(data);
            } catch (error) {
                notify('Failed to load projects', { type: 'error' });
            } finally {
                setLoading((prev) => ({ ...prev, projects: false }));
            }
        };
        loadProjects();
    }, [notify]);

    // Poll JIRA task status
    useTaskPolling(jiraTask.id, '/api/jira/status', (statusData) => {
        setJiraTask((prev) => ({ ...prev, status: statusData }));
        if (statusData.status === 'completed' || statusData.status === 'failed') {
            setJiraTask((prev) => ({ ...prev, id: null }));
            setLoading((prev) => ({ ...prev, processing: false }));
        }
    });

    // Poll Process task status
    useTaskPolling(processTask.id, '/api/process/status', (statusData) => {
        setProcessTask((prev) => ({ ...prev, status: statusData }));
        if (statusData.status === 'completed' || statusData.status === 'failed') {
            setProcessTask((prev) => ({ ...prev, id: null }));
            setLoading((prev) => ({ ...prev, stageProcessing: false }));
        }
    });

    const handleJiraExtraction = async () => {
        if (!selectedProject) {
            notify('Please select a project before processing', { type: 'warning' });
            return;
        }

        setLoading((prev) => ({ ...prev, processing: true }));
        notify('Processing started', { type: 'info' });

        try {
            const data = await apiService.startExtraction(selectedProject);
            setJiraTask({ id: data.task_id, status: null });
        } catch (error) {
            setLoading((prev) => ({ ...prev, processing: false }));
            notify('Failed to start processing', { type: 'error' });
        }
    };

    const handleStageProcessing = async () => {
        if (!selectedStage) {
            notify('Please select a stage before processing', { type: 'warning' });
            return;
        }

        setLoading((prev) => ({ ...prev, stageProcessing: true }));
        notify('Stage processing started', { type: 'info' });

        try {
            const data = await apiService.fetchProcessStage(selectedProject, selectedStage);
            setProcessTask({ id: data.task_id, status: null });
        } catch (error) {
            setLoading((prev) => ({ ...prev, stageProcessing: false }));
            notify('Failed to process stage', { type: 'error' });
        }
    };

    return (
        <Box m={2}>
            <Title title="Processing Page" />

            {/* JIRA Extraction Section */}
            <Box display="flex" flexDirection="column" gap={2}>
                <h2>JIRA Extraction</h2>
                <SimpleForm toolbar={null}>
                    <SelectInput
                        source="project"
                        label="Select Project"
                        choices={projects.map((project) => ({
                            id: project.id,
                            name: project.name,
                        }))}
                        value={selectedProject}
                        onChange={(event) => setSelectedProject(event.target.value)}
                        fullWidth
                    />
                </SimpleForm>
                {loading.processing ? (
                    <CircularProgress />
                ) : (
                    <Button
                        label="Start Extraction"
                        onClick={handleJiraExtraction}
                        disabled={!selectedProject}
                    />
                )}
                {jiraTask.status && <p>Task Status: {jiraTask.status.status}</p>}
            </Box>

            {/* Process Stage Section */}
            <Box mt={4}>
                <h2>Process Stage</h2>
                <SimpleForm toolbar={null}>
                    <SelectInput
                        source="stage"
                        label="Select Stage"
                        choices={[
                            { id: '1', name: 'Stage 1' },
                            { id: '2', name: 'Stage 2' },
                        ]}
                        value={selectedStage}
                        onChange={(event) => setSelectedStage(event.target.value)}
                        fullWidth
                    />
                </SimpleForm>
                {loading.stageProcessing ? (
                    <CircularProgress />
                ) : (
                    <Button
                        label="Start Stage Processing"
                        onClick={handleStageProcessing}
                        disabled={!selectedStage}
                    />
                )}
                {processTask.status && <p>Task Status: {processTask.status.status}</p>}
                {/* {stageResult && <p>Stage Result: {JSON.stringify(stageResult)}</p>} */}
            </Box>
            {/* Add generated report taking from api/reports?projectid if available */}
        
            <Box mt={4}>
                <h2>Generated Report</h2>
                {selectedProject && (
                    <Button
                        label="Fetch Report"
                        onClick={async () => {
                            setLoading((prev) => ({ ...prev, report: true }));
                            try {
                                const reportData = await apiService.fetchReport(selectedProject);
                                notify('Report fetched successfully', { type: 'info' });
                                setReport(reportData);
                            } catch (error) {
                                notify('Failed to fetch report', { type: 'error' });
                            } finally {
                                setLoading((prev) => ({ ...prev, report: false }));
                            }
                        }}
                        disabled={loading.report}
                    />
                )}
                {loading.report && <CircularProgress />}
                {report && (
                    <Box mt={2}
                        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(report.report_html.replace(/\n/g, '')) }} >
                        
                    </Box>
                )}
            </Box>
        </Box>
    );
};

export default Processing;