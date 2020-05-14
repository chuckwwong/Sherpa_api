import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
import Button from 'react-bootstrap/Button';

class CriticalFlows extends Component {
  constructor(props){
    super(props);
    this.state = {
      eval_name: '',
      flows: {},
      flows_s: [],
      lambda: 1,
      link_f: true,
      switch_f: false,
      output_f: undefined
    };

  }

  componentDidMount() {
    console.log("Critical Flow", this.props);
  }

  handleName = event => {
    const target = event.target;
    this.setState({
      [target.name]: target.value,
    });
  }

  runFlows = () => {
    // run backend
  }

  render() {
    return (
      <div>
        <h3>Critical Flows Metrics</h3>
        <p>
          Critical Flows Metric Instructions: Select all critical flows
          and see which flows are impacted by possible link or switch failures
          given a failure rate of lambda.
        </p>
        {/* Evaluation Name goes here*/}
        <form>
          <label>
            Evaluation Name:
            <input
              type="text"
              name="eval_name"
              value={this.state.eval_name}
              onChange={this.handleName}
            />
          </label>
        </form>
        {/* List all flows in network here */}
        {/* Option to set lambda */}
        {/* Option to select switch or link failure */}
        <Button onClick={this.runFlows}>Run</Button>
      </div>
    );
  }
}

export default withRouter(CriticalFlows);