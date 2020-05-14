import React, {Component} from 'react';
import {withRouter/*, useParams, NavLink, Switch, Route, BrowserRouter*/} from 'react-router-dom';
//import Button from 'react-bootstrap/Button';

class OtherMetrics extends Component {
  render() {
    return (
      <div>
        <h3>Other Metrics</h3>
        <p>
          Work In Progress. New Metrics will be added here.
        </p>
      </div>
    );
  }
}

export default withRouter(OtherMetrics);