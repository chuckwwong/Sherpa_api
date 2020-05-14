import React, { Component } from 'react';
import { BrowserRouter, Route, Switch, useHistory } from 'react-router-dom';

import Home from './components/Home'
import Session from './components/Session'

import './App.css';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      history: useHistory
    }
  }
  
  componentDidMount() {
    // not sure if i need this
    console.log("App Component",this.state);
  }  

  render() {
    return (
        <div>
          <h1>
            SHERPA
          </h1>

          <BrowserRouter>
            <div>
              <Switch>
                <Route path="/" component={Home} exact/>
                <Route path="/session/:session_name" component={Session}/>
              </Switch>
            </div>
          </BrowserRouter>
        </div>
      );
  }
}

export default App;
