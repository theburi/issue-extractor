import React from 'react';
import { Admin, Resource } from 'react-admin';
import simpleRestProvider from 'ra-data-simple-rest';
import Dashboard from './components/Dashboard';
import Config from './pages/Config';
import { ProjectsList, ProjectsEdit, ProjectsCreate } from './pages/Project';
import './App.css';

const dataProvider = simpleRestProvider('/api'); // Update to relative path

const App = () => {
    return (
        <Admin dashboard={Dashboard} dataProvider={dataProvider}>
            <Resource name="projects" list={ProjectsList} edit={ProjectsEdit} create={ProjectsCreate} />            
            <Resource name="config" list={Config} />
        </Admin>
    );
};

export default App;