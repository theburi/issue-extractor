import React, { useEffect, useState } from 'react';
import axios from 'axios';

const Projects = () => {
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState('');
    const [newProject, setNewProject] = useState('');

    useEffect(() => {
        const fetchProjects = async () => {
            try {
                const response = await axios.get('/api/projects');
                setProjects(response.data);
            } catch (error) {
                console.error('Error fetching projects:', error);
            }
        };
        fetchProjects();
    }, []);

    const handleProjectChange = (event) => {
        setSelectedProject(event.target.value);
    };

    const handleNewProjectChange = (event) => {
        setNewProject(event.target.value);
    };

    const handleNewProjectSubmit = async (event) => {
        event.preventDefault();
        try {
            const response = await axios.post('/api/projects', { name: newProject });
            setProjects([...projects, response.data]);
            setNewProject('');
        } catch (error) {
            console.error('Error creating new project:', error);
        }
    };

    return (
        <div>
            <h1>Projects</h1>
            <div>
                <label>
                    Select Project:
                    <select value={selectedProject} onChange={handleProjectChange}>
                        <option value="">Select a project</option>
                        {projects.map((project) => (
                            <option key={project._id} value={project.name}>
                                {project.name}
                            </option>
                        ))}
                    </select>
                </label>
            </div>
            <div>
                <form onSubmit={handleNewProjectSubmit}>
                    <label>
                        Create New Project:
                        <input type="text" value={newProject} onChange={handleNewProjectChange} />
                    </label>
                    <button type="submit">Create</button>
                </form>
            </div>
        </div>
    );
};

export default Projects;