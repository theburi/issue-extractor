import React from 'react';
import Header from './Header';
import Footer from './Footer';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Home from '../pages/Home';
import Analysis from '../pages/Analysis';
import Report from '../pages/Report';
import './App.css';

const App = () => {
    return (
        <Router>
            <div className="app">
                <Header />
                <main>
                    <Switch>
                        <Route path="/" exact component={Home} />
                        <Route path="/analysis" component={Analysis} />
                        <Route path="/report" component={Report} />
                    </Switch>
                </main>
                <Footer />
            </div>
        </Router>
    );
};

export default App;