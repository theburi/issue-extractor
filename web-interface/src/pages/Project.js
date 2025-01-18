import React from 'react';
import { List, Datagrid, TextField, EditButton, DeleteButton, Edit, SimpleForm, TextInput } from 'react-admin';
import ProjectDetails from './ProjectDetails'; // Import project details
import { ProjectCreate } from './ProjectCreate';
// import ProjectReports from './ProjectReports'; 

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
            <TextInput source="name" label="Project Name" fullWidth/>
            <TextInput source="jira_source" label="Jira Source" fullWidth/>
            <ProjectDetails />
            {/* <ProjectReports />   */}
        </SimpleForm>
    </Edit>
);

// Create View
export const ProjectsCreate = () => (
 <ProjectCreate />
);