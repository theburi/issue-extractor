import React from 'react';
import { List, Datagrid, TextField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, NumberInput } from 'react-admin';
import { ProjectCreate } from './ProjectCreate';


// List View
export const ProjectsList = () => (
    <List>
        <Datagrid rowClick="edit">
            <TextField source="id" label="ID" />
            <TextField source="name" label="Project Name" />
            <EditButton />
            <DeleteButton />
        </Datagrid>
    </List>
);

// Edit View
export const ProjectsEdit = () => (
    <Edit>
        <h2 >Project  </h2>
        <SimpleForm>
            <TextInput source="name" label="Project Name" fullWidth />
            <TextInput source="jira_source" label="Jira Source" fullWidth />
            <NumberInput source='prompts.version' label='Prompt Version' fullWidth />
            <TextInput
                source="prompts.problem_extraction"
                label="Problem Extraction"
                fullWidth
                multiline
            />
            <TextInput
                source="prompts.problem_type"
                label="Problem Type"
                fullWidth
                multiline
            />
            <TextInput
                source="prompts.problem_type_classification"
                label="Problem Type Classification"
                fullWidth
                multiline
            />
            <TextInput
                source="prompts.generate_cluster_summary"
                label="Generate Cluster Summary"
                fullWidth
                multiline
            />

        </SimpleForm>
    </Edit>
);

// Create View
export const ProjectsCreate = () => (
    <ProjectCreate />
);