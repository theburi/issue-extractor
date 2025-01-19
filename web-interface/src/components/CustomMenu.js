import React from 'react';
import { Menu } from 'react-admin';
import { MenuItemLink } from 'react-admin';
import { Settings } from '@mui/icons-material';

const CustomMenu = () => (
    <Menu>
        {/* Default Dashboard */}
        <Menu.DashboardItem />

        {/* Resources */}
        <Menu.ResourceItem name="projects" />
        <Menu.ResourceItem name="config" />

        {/* Custom Route */}
        <MenuItemLink
            to="/processing"
            primaryText="Processing"
            leftIcon={<Settings />}
        />
    </Menu>
);

export default CustomMenu;