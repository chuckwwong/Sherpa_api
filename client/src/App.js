import React, { Component } from 'react';
import { BrowserRouter, Route, Switch, useHistory } from 'react-router-dom';

import Home from './components/Home'
import Session from './components/Session'

import './App.css';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      history: useHistory,
      session_name: undefined,
      flows: undefined,
      links: undefined
    }
  }
  
  componentDidMount() {
    // not sure if i need this
    console.log("App Component",this.state);
  }  

  getUploadResp = (session,flows,links) => {
    this.setState({
      session_name: session,
      flows: flows,
      links: links
    });
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
                <Route path="/" component={() => <Home 
                  uploadResp={this.getUploadResp}
                  history={this.state.history}/>} exact/>
                <Route path="/session/:session_name" component={()=><Session 
                  session_name={this.state.session_name}
                  flows={this.state.flows}
                  links={this.state.links}
                  history={this.state.history}/>}/>
              </Switch>
            </div>
          </BrowserRouter>
        </div>
      );
  }
}

export default App;
