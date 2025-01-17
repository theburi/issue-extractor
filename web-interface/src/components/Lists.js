import React from 'react';
import { List, Datagrid, TextField } from 'react-admin';

export const AnalysisList = (props) => (
    <List {...props}>
        <Datagrid>
            <TextField source="id" />
            <TextField source="name" />
            <TextField source="description" />
        </Datagrid>
    </List>
);

export const ReportList = (props) => (
    <List {...props}>
        <Datagrid>
            <TextField source="id" />
            <TextField source="title" />
            <TextField source="status" />
        </Datagrid>
    </List>
);
