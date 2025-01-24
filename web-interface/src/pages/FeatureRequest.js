import { TextInput, SimpleForm, SaveButton, Toolbar, useNotify } from 'react-admin';
import { Box, Grid, Stack, CircularProgress } from '@mui/material';
import { useState } from 'react';
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
};
const llm_default_prompts = { 
    get_summary: "You are an expert at analyzing customer issues. Identify the key problems described in the text below.\n {text}",
    refusal_message: "Hello XXX,Thanks for your feature suggestion. After careful consideration, we've decided it doesn't align with our current product direction for reasons such as the described use case being too customer-specific.[... Please explain a little bit what the high level direction is and why it does not fit... The clearer we are here the better the customer experience.]Feel free to reach out through the ticket or your CSM if you have more questions.We can additionally involve Consulting if required.Appreciate your understanding.Best,[Your Name][Your Title/Position]"
}

const FeatureRequest = () => {
    const [jiraKey, setJiraKey] = useState('');
    const [processingResult, setProcessingResult] = useState(null);
    const [jiraIssueLoading, setLoading] = useState(false);
    const [featureSummary, setSummary] = useState('');
    const [commentsOpen, setCommentsOpen] = useState(false);
    const [valueProposition, setValueProposition] = useState('');
    const [llm_prompts_get_summary, setLlmPromptGetSummary] = useState(llm_default_prompts.get_summary);
    const notify = useNotify();
    


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
                // disabled={loading || !jiraKey.trim()}
            />
            {jiraIssueLoading && <CircularProgress size={24} style={{ marginLeft: 16 }} />}
        </Toolbar>
    );

    const handleFeatureSummary = async (prompt, setResult) => {
        const payload = {
            'variables': {'text': processingResult.data.description_llm},
            'prompt': prompt,
        };        
        
        try {
            const result = await apiService.getFeatureSummary(payload);
            setResult(result);
            notify('Feature summay processed successfully', { type: 'success' });
        } catch (error) {
            console.error('Error:', error);
            notify(error.message || 'Failed to process feature summary', { type: 'error' });
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
                <SimpleForm defaultValues={{ llm_prompts_get_summary: llm_default_prompts.get_summary }}>                
                <Grid container>
                    <Grid item xs={3}> <h3>Feature Request Summary</h3> </Grid>
                    <Grid item xs={9}>                         
                            <TextInput
                                source="llm_prompts_get_summary"                        
                                label="Value Proposition"
                                value={llm_prompts_get_summary}
                                onChange={(e) => setLlmPromptGetSummary(e.target.value)}
                                fullWidth multiline
                            />
                    </Grid>
                    <Button onClick={() =>
                        handleFeatureSummary(
                            'You are an expert at analyzing customer issues. Identify the key problems described in the text below.\n {text}',
                            setSummary
                        )}
                     variant="contained" color="primary">
                        Process Summary
                    </Button>
                    <Box>           
                    <Markdown remarkPlugins={[remarkGfm]}>{featureSummary.summary}</Markdown>
                    </Box>
                </Grid> 
                
                </SimpleForm>
                <Box>
                    <h3>Feature Request Value Proposition</h3>
                    <Button onClick={() =>
                        handleFeatureSummary(
                            llm_prompts_get_summary,
                            setValueProposition
                        )}
                     variant="contained" color="primary">
                        Generate Value Proposition
                    </Button>
                    <Box>           
                    <h3>Feature Summary</h3>
                    <Markdown remarkPlugins={[remarkGfm]}>
                        {valueProposition.summary}
                    </Markdown>
                    </Box>
                </Box> 
            </Box>
            )}
        </Box>
    );
};

export default FeatureRequest;