import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
import Button from 'react-bootstrap/Button';

import ItemTracker from './../ItemTracker';

/*
  props:
    - flows: flows in current topology
    - links: links of current topology
    - eval_name: not sure if this should be passed in
    - lambda: failure rate
    - time: number of time epochs
    - tolerance: tolerance for estimating failure rate
*/
class CritNeighMetric extends Component {
  constructor(props){
    super(props);

    this.state = {
      eval_name: '',
      flows: {},
      switches: {},
      switches_ch: {},
      hops: 0,
      lambda: undefined,
      time: 1,
      tolerance: undefined,
      output_f: undefined
    }
  }

  componentDidMount() {
    console.log("Critical Neigh", this.props);
    let {session_name} = this.props.match.params;
    // call fetch
    fetch(`http://localhost:5000/load?session_name=${session_name}`)
    .then(rsp => rsp.json())
    .then(data => {
      console.log(data);
      if (data.success) {
        this.setState({
          success: data.success,
          flows: data.flows,
          switches: data.switches
        });
      }
    }).catch(error => console.log('error', error));
  }

  handleSwitchCheck = (item,event) => {
    const {switches_ch} = this.state;
    switches_ch[item] = event.target.checked;
    this.setState({
      switches_ch
    });
  }

  handleFormChange = event => {
    const target = event.target;
    let value;
    //console.log(target.value);
    if (target.name === "time" || target.name === "hops"){
      value = parseInt(target.value);
    } else if (target.name === "lambda" || target.name === "tolerance") {
      value = parseFloat(target.value);
    } else {
      value = target.value;
    }
    this.setState({
      [target.name]: value,
    });
  }

  runSwitch = () => {
    let myHeaders = new Headers();
    myHeaders.append("Content-Type","application/json")

    let switches = Object.entries(this.state.switches_ch).filter(([key,value]) =>
      value
    ).map(([key,value]) =>
      key
    );
    // Create the body of the request
    let json = JSON.stringify({
      switches,
      "failure_rate": this.state.lambda,
      "time": this.state.time,
      "tolerance": this.state.tolerance,
      "hops": this.state.hops
    });

    let requestOptions = {
      method: 'POST',
      body: json,
      headers: myHeaders,
      redirect: 'follow'
    };
    let {session_name} = this.props.match.params;
    fetch(`http://localhost:5000/critf_neigh?session_name=${session_name}&eval_name=${this.state.eval_name}`,requestOptions)
    .then(rsp => rsp.blob())
    .then(blob => {
      let a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.setAttribute("download",this.state.eval_name+"_out.json");
      a.click();
    }).catch(error => console.log('error',error));
  }

  render() {
    return (
      <div>
        <h3>Critical Flows Metrics</h3>
        <p>
          Critical Flows Metric Instructions: Select all critical flows
          and see which flows are impacted by possible link or switch failures
          given a failure rate of lambda and tolerance level (both of which are decimal
          values).
        </p>
        <h4>Impact of Switch Neighborhood Failure</h4>
        <p>
          Select a single source switch to fail, which will be the center of the neighborhood of switches to fail.
          The value of the neighborhood hops indicates how wide the neighborhood of failure spreads from the source switch.
          Given the selected source switch to fail, we can find the probability that the connectivity of all flows
          is lost as a result of the neighborhood of switch failing when the controller is disconnected from the
          network for a period of time specified by the user.
        </p>
        {/* Evaluation Name goes here*/}
        <form>
          <label>
            Evaluation Name:
            <input
              type="text"
              name="eval_name"
              value={this.state.eval_name}
              onChange={this.handleFormChange}
            />
          </label>
          {/* Option to set lambda */}
          <label>
            Failure Rate:
            <input
              type="number"
              name="lambda"
              max={1}
              min={0}
              step={0.0001}
              placeholder='0.4'
              required={true}
              value={this.state.lambda}
              onChange={this.handleFormChange}
            />
          </label>
          {/* Option to set Time Epochs used */}
          <label>
            Time Epochs:
            <input
              type="number"
              name="time"
              value={this.state.time}
              min={0}
              onChange={this.handleFormChange}
            />
          </label>
          {/* Option to set the tolerance level*/}
          <label>
            Tolerance:
            <input
              type="number"
              name="tolerance"
              max={1}
              min={0}
              placeholder='0.25'
              step={0.0001}
              value={this.state.tolerance}
              onChange={this.handleFormChange}
            />
          </label>
          <label>
            Hops:
            <input
              type="number"
              name="hops"
              min={0}
              value={this.state.hops}
              onChange={this.handleFormChange}
            />
          </label>
        </form>
        {/* Display list of all switches*/}
        <div className="trackerContainer">
          <ItemTracker
            name={"Switches"}
            items={this.state.switches}
            items_ch={this.state.switches_ch}
            hops={this.state.hops}
            itemType={"neigh"}
            listType={"checkbox"}

            handleItemCheck={this.handleSwitchCheck}
          />
        </div>
        <Button onClick={this.runSwitch}>Run</Button>
      </div>
    );
  }
}

export default withRouter(CritNeighMetric);