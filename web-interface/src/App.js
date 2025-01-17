import React from 'react';
import { Admin, Resource } from 'react-admin';
import simpleRestProvider from 'ra-data-simple-rest';
import Dashboard from './components/Dashboard';
import { AnalysisList, ReportList } from './components/Lists';
import './App.css';

const dataProvider = simpleRestProvider('http://localhost:5000/api');

const App = () => {
    return (
        <Admin dashboard={Dashboard} dataProvider={dataProvider}>
            <Resource name="analysis" list={AnalysisList} />
            <Resource name="reports" list={ReportList} />
        </Admin>
    );
};

export default App;