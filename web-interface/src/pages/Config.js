import React, { useState, useEffect } from 'react';
import { TextInput, SimpleForm, required, NumberInput, ArrayInput, SimpleFormIterator } from 'react-admin';
import api from '../services/api';

const Config = () => {
    const [config, setConfig] = useState({});

    useEffect(() => {
        api.get('/config')
            .then(response => setConfig(response.data))
            .catch(error => console.error('API Error:', error));
    }, []);

    const handleSave = (data) => {
        api.post('/config', data)
            .then(response => alert(`Configuration saved successfully: ${response.data.message}`)) // Assuming 'response.data.message' exists
            .catch(error => console.error(error));
    };

    return (
        <SimpleForm onSubmit={handleSave}>
            <h2>MongoDB Section </h2>
            <TextInput source="mongodb.uri" label="MongoDB URI" defaultValue={config.mongodb?.uri} validate={required()} fullWidth />
            <TextInput source="mongodb.database" label="MongoDB Database" defaultValue={config.mongodb?.database} validate={required()} fullWidth />
            <TextInput source="mongodb.raw_collection" label="Raw Collection" defaultValue={config.mongodb?.raw_collection} fullWidth />
            <TextInput source="mongodb.processed_collection" label="Processed Collection" defaultValue={config.mongodb?.processed_collection} fullWidth />
            <TextInput source="mongodb.results_collection" label="Results Collection" defaultValue={config.mongodb?.results_collection} fullWidth />

            <h2>LLM Section</h2>
            <TextInput source="llm.model_name" label="LLM Model Name" defaultValue={config.llm?.model_name} validate={required()} fullWidth />
            <NumberInput source="llm.temperature" label="LLM Temperature" defaultValue={config.llm?.temperature} fullWidth />
            <NumberInput source="llm.max_tokens" label="LLM Max Tokens" defaultValue={config.llm?.max_tokens} fullWidth />

            <h2> Clustering Section </h2>
            <TextInput source="clustering.algorithm" label="Clustering Algorithm" defaultValue={config.clustering?.algorithm} fullWidth />
            <NumberInput source="clustering.max_clusters" label="Max Clusters" defaultValue={config.clustering?.max_clusters} fullWidth />

            <h2>Embeddings Section</h2>
            <TextInput source="embeddings.model_name" label="Embeddings Model Name" defaultValue={config.embeddings?.model_name} fullWidth />

            <h2>Issue Extractor Section</h2>
            <ArrayInput source="issue-extractor.config" label="Extractor Config">
                <SimpleFormIterator>
                    <TextInput />
                </SimpleFormIterator>
            </ArrayInput>
            <ArrayInput source="issue-extractor.data" label="Extractor Data">
                <SimpleFormIterator>
                    <TextInput />
                </SimpleFormIterator>
            </ArrayInput>
            <TextInput source="issue-extractor.jira_source" label="Jira Source" defaultValue={config['issue-extractor']?.jira_source} fullWidth />
            <ArrayInput source="issue-extractor.src" label="Source Files">
                <SimpleFormIterator>
                    <TextInput />
                </SimpleFormIterator>
            </ArrayInput>
            <ArrayInput source="issue-extractor.templates" label="Templates">
                <SimpleFormIterator>
                    <TextInput />
                </SimpleFormIterator>
            </ArrayInput>

            <h2>Paths Section</h2>
            <TextInput source="paths.taxonomy" label="Taxonomy Path" defaultValue={config.paths?.taxonomy} fullWidth />
            <TextInput source="paths.templates" label="Templates Path" defaultValue={config.paths?.templates} fullWidth />

            <h2>Prompts Section</h2>
            <TextInput source="prompts.generate_cluster_summary" label="Cluster Summary Prompt" defaultValue={config.prompts?.generate_cluster_summary} multiline fullWidth/>
            <TextInput source="prompts.problem_extraction" label="Problem Extraction Prompt" defaultValue={config.prompts?.problem_extraction} multiline fullWidth/>
            <TextInput source="prompts.problem_type" label="Problem Type Prompt" defaultValue={config.prompts?.problem_type} multiline fullWidth/>
            <TextInput source="prompts.problem_type_classification" label="Problem Type Classification Prompt" defaultValue={config.prompts?.problem_type_classification} multiline fullWidth/>
            <NumberInput source="prompts.version" label="Prompt Version" defaultValue={config.prompts?.version} fullWidth />

            <h2>Reports Section</h2>
            <TextInput source="reports.output_dir" label="Report Output Directory" defaultValue={config.reports?.output_dir} fullWidth />
            <TextInput source="reports.report_filename" label="Report Filename" defaultValue={config.reports?.report_filename} fullWidth />
            <TextInput source="reports.template_dir" label="Template Directory" defaultValue={config.reports?.template_dir} fullWidth />

            <h2>Vector Store Section</h2>
            <TextInput source="vector_store.persist_directory" label="Persist Directory" defaultValue={config.vector_store?.persist_directory} fullWidth />
            <NumberInput source="vector_store.similarity_threshold" label="Similarity Threshold" defaultValue={config.vector_store?.similarity_threshold} fullWidth />
        </SimpleForm>
    );
};

export default Config;