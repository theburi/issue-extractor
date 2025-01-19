import React, { useState, useEffect } from 'react';
import { Create, SimpleForm, TextInput, NumberInput } from 'react-admin';
import { fetchUtils } from 'react-admin';

const apiUrl = '/api/config'; // Adjust the endpoint as needed

export const ProjectCreate = () => {
    const [configFile, setJiraSource] = useState({});

    useEffect(() => {
        // Fetch jira_source options from the config API
        const fetchJiraSources = async () => {
            try {
                const httpClient = fetchUtils.fetchJson;
                const { json } = await httpClient(apiUrl);         
                if (json) {
                    console.log(json);                                       
                    setJiraSource(json); // Assuming API returns jira_sources array
                }
            } catch (error) {
                console.error('Error fetching jira_sources:', error);
            }
        };
        fetchJiraSources();
    }, []);

    if (!configFile) {
        return <div>Loading...</div>;
    }
    const jiraSource = configFile['issue-extractor']?.jira_source;
    const prompts = configFile['prompts'] || {};

    return (
        <Create>
            <SimpleForm>
                <TextInput source="name" label="Project Name" fullWidth />
                <TextInput source="jira_source" 
                    label="Jira Source" 
                    defaultValue={jiraSource}
                    fullWidth />
                <NumberInput source='prompts.version' label='Prompt Version' defaultValue={prompts.version} fullWidth/>
                <TextInput source='prompts.problem_extraction' label='Problem Extraction' defaultValue={prompts.problem_extraction} fullWidth multiline/>
                <TextInput
                    source="prompts.problem_type"
                    label="Problem Type"
                    defaultValue={prompts.problem_type}
                    fullWidth
                    multiline
                />
                <TextInput
                    source="prompts.problem_type_classification"
                    label="Problem Type Classification"
                    defaultValue={prompts.problem_type_classification}
                    fullWidth
                    multiline
                />
                <TextInput
                    source="prompts.generate_cluster_summary"
                    label="Generate Cluster Summary"
                    defaultValue={prompts.generate_cluster_summary}
                    fullWidth
                    multiline
                />
            </SimpleForm>
        </Create>
    );
};