import React from 'react';
import { Admin, Resource } from 'react-admin';
import simpleRestProvider from 'ra-data-simple-rest';
import Dashboard from './components/Dashboard';
import { AnalysisList, ReportList } from './components/Lists';
import Config from './pages/Config';
import './App.css';

const dataProvider = simpleRestProvider('/api'); // Update to relative path

const App = () => {
    return (
        <Admin dashboard={Dashboard} dataProvider={dataProvider}>
            <Resource name="analysis" list={AnalysisList} />
            <Resource name="reports" list={ReportList} />
            <Resource name="config" list={Config} />
        </Admin>
    );
};

export default App;