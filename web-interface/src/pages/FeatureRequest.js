import { TextInput, SimpleForm, SaveButton, Toolbar, useNotify } from 'react-admin';
import { Box, Grid, Stack, CircularProgress, IconButton } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { useState, useEffect } from 'react';
import { Collapse, Button } from '@mui/material';
import  Markdown  from 'react-markdown';
import remarkGfm  from 'remark-gfm';

// API service functions
const apiService = {
    processFeatureRequest: (jiraKey) => 
        fetch(`/api/feature-request?jira_key=${encodeURIComponent(jiraKey)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        }).then(res => {
            if (!res.ok) throw new Error('Failed to process request');
            return res.json();
        }),
    getFeatureSummary: (payload) => 
        fetch(`/api/issues/summary`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        }).then(res => {
            if (!res.ok) throw new Error('Failed to process request');
            return res.json();
        }),
    getTaskStatus: (apiPath, taskId) => fetch(`${apiPath}/${taskId}`).then((res) => res.json()),
};
const llm_default_prompts = [
    {
        id: 'get_problems',
        name: 'Get Problems',
        prompt: "You are an expert at analyzing customer issues. Identify the key problem described in the text below that is at a coare of the customer's request.\n {text}"
    },
    {
        id: 'get_solution',
        name: 'Get Solution',
        prompt: "You are an expert at analyzing customer issues. Identify solution that could address customer's Feature request below.\n {text}"
    },
    {
        id: 'refusal_message', 
        name: 'Refusal Message',
        prompt: "Write a message explaining to customer that their feature request will not be implemented. Here is Customer Request: {text}.\n Use the follwoing template:\n Hello,Thanks for your feature suggestion. After careful consideration, we've decided it doesn't align with our current product direction for reasons such as the described use case being too customer-specific.[... Please explain a little bit what the high level direction is and why it does not fit... The clearer we are here the better the customer experience.]Feel free to reach out through the ticket or your CSM if you have more questions.We can additionally involve Consulting if required.Appreciate your understanding.Best,[Your Name][Your Title/Position]"
    }
];

// Custom hook for task polling
const useTaskPolling = (taskId, apiPath, onStatusChange) => {
    useEffect(() => {
        if (!taskId || !apiPath) return;

        const pollInterval = setInterval(async () => {
            try {
                const data = await apiService.getTaskStatus(apiPath, taskId);
                onStatusChange(data);

                // Stop polling if the task is completed or failed
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);                    
                }
            } catch (error) {
                console.error('Polling error:', error);
                clearInterval(pollInterval);
            }
        }, 10000);

        return () => clearInterval(pollInterval); // Cleanup on unmount or dependency change
    }, [taskId, apiPath, onStatusChange]);
};

const FeatureRequest = () => {
    const [jiraKey, setJiraKey] = useState('');
    const [processingResult, setProcessingResult] = useState(null);
    const [jiraIssueLoading, setLoading] = useState(false);
    const [featureSummary, setSummary] = useState('');
    const [commentsOpen, setCommentsOpen] = useState(false);
    const [valueProposition, setValueProposition] = useState('');
    const [llmPrompts, setLlmPrompts] = useState(llm_default_prompts);
    const notify = useNotify();
    const [promptsVisible, setPromptsVisible] = useState({});
    const [taskId, setTaskId] = useState(null);
    const [taskApiPath, setTaskApiPath] = useState(null);
    const [loadingStates, setLoadingStates] = useState({});
    // Add the task polling hook
    useTaskPolling(taskId, taskApiPath, (data) => {
        if (data.status === 'completed') {
            setSummary(data.result);
            notify('Feature summary processed successfully', { type: 'success' });
        } else if (data.status === 'failed') {
            notify('Failed to process feature summary', { type: 'error' });
        }
    });

    const handleProcessRequest = async () => {
        if (!jiraKey.trim()) {
            notify('Please enter a JIRA key', { type: 'warning' });
            return;
        }

        setLoading(true);
        try {
            const result = await apiService.processFeatureRequest(jiraKey);
            setProcessingResult(result);
            notify('Feature request processed successfully', { type: 'success' });
        } catch (error) {
            console.error('Error:', error);
            notify(error.message || 'Failed to process feature request', { type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const CustomToolbar = () => (
        <Toolbar>
            <SaveButton
                label="Process Feature Request"
                onClick={handleProcessRequest}
            />
            {jiraIssueLoading && <CircularProgress size={24} style={{ marginLeft: 16 }} />}
        </Toolbar>
    );

    const handleFeatureSummary = async (prompt, setResult, promptId) => {
        setLoadingStates(prev => ({ ...prev, [promptId]: true }));
        const payload = {
            'variables': {'text': processingResult.data.description_llm},
            'prompt': prompt,
        };        
        
        try {
            const result = await apiService.getFeatureSummary(payload);
            setResult(result);
            setTaskId(result.task_id);
            setTaskApiPath('/api/issues/summary/tasks'); 
            notify('Feature summay processed successfully', { type: 'success' });
        } catch (error) {
            console.error('Error:', error);
            notify(error.message || 'Failed to process feature summary', { type: 'error' });
        } finally {
            setLoadingStates(prev => ({ ...prev, [prompt.id]: false }));
        }
    };

    return (
        <Box m={2}>
            <h1>Feature Request Processing Tool</h1>
            <SimpleForm toolbar={<CustomToolbar />}>
                <TextInput
                    source="jiraKey"
                    label="JIRA Key"
                    value={jiraKey}
                    onChange={(e) => setJiraKey(e.target.value)}
                    disabled={jiraIssueLoading}
                />
            </SimpleForm>

            {processingResult && ( 
            <Box mt={3}>
                <h3>Feature request details</h3>
                <Box mt={2}>
                    <Grid container spacing={2}>
                        <Grid item xs={6}>
                            <strong>Customer IDs:</strong> {processingResult.data.cid} 
                        </Grid>                      
                        <Grid item xs={6}>
                            <strong>Created Date:</strong> {new Date(processingResult.data.created_date).toLocaleString()}
                        </Grid>  
                        <Grid item xs={6}>
                            <strong>Priority:</strong> {processingResult.data.priority}
                        </Grid>  
                        <Grid item xs={6}>
                            <strong>Status:</strong> {processingResult.data.status}
                        </Grid>  
                        <Grid item xs={8}>
                            <Stack direction="row" spacing={2}>
                                <strong>Components:</strong>
                                {processingResult.data.components.map((component, index) => (
                                        <div key={index}>{component}</div>
                                    ))}
                                
                            </Stack>
                        </Grid>  
                    </Grid>
                    <hr />
                    <div>
                        <strong>Summary:</strong> {processingResult.data.summary}
                    </div>
                    <div>
                        <strong>Description:</strong> {processingResult.data.description}
                    </div>
                    <div>                           
                        <strong>Comments:</strong>
                        <Button onClick={() => setCommentsOpen(!commentsOpen)}>
                            {commentsOpen ? 'Hide Comments' : 'Show Comments'}
                        </Button>
                        <Collapse in={commentsOpen}>
                                {processingResult.data.comments.map((comment, index) => (
                                    <Box key={index} mt={1}>
                                        <div><strong>Author:</strong> {comment.author}</div>
                                        <div><strong>Body:</strong> {comment.body}</div>
                                        <div><strong>Created:</strong> {new Date(comment.created).toLocaleString()}</div>
                                    </Box>
                                ))}
                        </Collapse>
                    </div>
                </Box>
                {llm_default_prompts.map((prompt, index) => (
                    <SimpleForm key={index} defaultValues={{ [`llm_prompts_${prompt.id}`]: prompt.prompt }} toolbar={null}>
                        <Grid container spacing={2}>
                            <Stack direction="row" alignItems="center" spacing={1}>
                                <h3>{prompt.name}</h3>
                                <IconButton
                                        size="small"
                                        onClick={() => setPromptsVisible(prev => ({
                                            ...prev,
                                            [prompt.id]: !prev[prompt.id]
                                        }))}
                                    >
                                        {promptsVisible[prompt.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                                </IconButton>
                            </Stack>
                            <Grid item xs={10}>
                                <Collapse in={promptsVisible[prompt.id]}>
                                    <TextInput
                                        source={`llm_prompts_${prompt.id}`}
                                        label={prompt.name}
                                        value={prompt.prompt}
                                        onChange={(e) => {
                                            setLlmPrompts(prevPrompts => 
                                                prevPrompts.map(p => 
                                                    p.id === prompt.id 
                                                        ? { ...p, prompt: e.target.value }
                                                        : p
                                                )
                                            );
                                        }}
                                        fullWidth
                                        multiline
                                    />
                                 </Collapse>
                            </Grid>
                            <Grid item xs={12}>
                                <Button
                                    onClick={() => handleFeatureSummary(
                                        llmPrompts.find(p => p.id === prompt.id).prompt,
                                        prompt.id === 'get_summary' ? setSummary : setValueProposition
                                    )}
                                    variant="contained"
                                    color="primary"
                                    sx={{ mt: 2, mb: 2 }}
                                    disabled={loadingStates[prompt.id]}
                                    startIcon={loadingStates[prompt.id] && <CircularProgress size={20} color="inherit" />}
                                >
                                    {loadingStates[prompt.id] 
                                        ? 'Processing...' 
                                        : (index === 0 ? 'Process Summary' : 'Generate Value Proposition')
                                    }
                                </Button>
                                <Box>
                                    <Markdown remarkPlugins={[remarkGfm]}>
                                        {index === 0 ? featureSummary.summary : valueProposition.summary}
                                    </Markdown>
                                </Box>
                            </Grid>
                        </Grid>
                    </SimpleForm>
                ))}
            </Box>
            )}
        </Box>
    );
};

export default FeatureRequest;