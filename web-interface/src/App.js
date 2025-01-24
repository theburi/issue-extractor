import React from 'react';
import { Admin, Resource, CustomRoutes } from 'react-admin';
import { Route } from "react-router-dom";
import simpleRestProvider from 'ra-data-simple-rest';
import Dashboard from './components/Dashboard';
import Config from './pages/Config';
import { ProjectsList, ProjectsEdit, ProjectsCreate } from './pages/Project';
import './App.css';
import Processing from './pages/Processing';
import FeatureRequest from './pages/FeatureRequest';
import CustomMenu from './components/CustomMenu';

const dataProvider = simpleRestProvider('/api'); // Update to relative path

const App = () => {
    return (
        <Admin dashboard={Dashboard} dataProvider={dataProvider} menu={CustomMenu}>
            <Resource name="projects" list={ProjectsList} edit={ProjectsEdit} create={ProjectsCreate} />            
            <Resource name="config" list={Config} />
            <CustomRoutes>
                <Route name="processing" path="/processing" element={<Processing />} />
                <Route name="featurerequest" path="/feature" element={<FeatureRequest />} />
            </CustomRoutes>
        </Admin>
    );
};

export default App;