import React, { useState, useEffect } from 'react';
import { Create, SimpleForm, TextInput } from 'react-admin';
import { fetchUtils } from 'react-admin';

const apiUrl = '/api/config'; // Adjust the endpoint as needed

export const ProjectCreate = () => {
    const [jiraSource, setJiraSource] = useState('');

    useEffect(() => {
        // Fetch jira_source options from the config API
        const fetchJiraSources = async () => {
            try {
                const httpClient = fetchUtils.fetchJson;
                const { json } = await httpClient(apiUrl);         
                if (json) {
                    console.log(json["issue-extractor"].jira_source);                                       
                    setJiraSource(json["issue-extractor"]); // Assuming API returns jira_sources array
                }
            } catch (error) {
                console.error('Error fetching jira_sources:', error);
            }
        };
        fetchJiraSources();
    }, []);

    return (
        <Create>
            <SimpleForm>
                <TextInput source="name" label="Project Name" fullWidth />
                <TextInput source="jira_source" label="Jira Source" defaultValue={jiraSource.jira_source} fullWidth />
            </SimpleForm>
        </Create>
    );
};