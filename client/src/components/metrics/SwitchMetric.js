import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
import Button from 'react-bootstrap/Button';

class SwitchMetric extends Component {
  constructor(props){
    super(props);
    this.state = {
      eval_name: '',
      switch: [],
      switch_s: [],
      output_f: undefined
    };

  }

  componentDidMount() {
    console.log("Switch Metric",this.props);
  }

  handleName = event => {
    const target = event.target;
    this.setState({
      [target.name]: target.value,
    });
  }

  runSwitch = () => {
    // run backend
  }

  render() {
    return (
      <div>
        <h3>Switch Metrics</h3>
        <p>
          Switch Metric Instructions: Select switches
          and see which flows are impacted.
        </p>
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
        {/*List all switches in network here */}
        <Button onClick={this.runSwitch}>Run</Button>
      </div>
    );
  }
}

export default withRouter(SwitchMetric);