import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

const clearCookies = () => {
    document.cookie.split(";").forEach((c) => {
        document.cookie = c
            .replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
};

clearCookies(); // Clear cookies before rendering the app

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);