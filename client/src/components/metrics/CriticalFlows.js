import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
import Button from 'react-bootstrap/Button';

import ItemTracker from './ItemTracker';

class CriticalFlows extends Component {
  constructor(props){
    super(props);
    this.state = {
      eval_name: '',
      flows: {},
      links:[],
      flows_ch: {},
      links_ch: {},
      lambda: 0,
      time: 1,
      tolerance: 0,
      output_f: undefined
    };

  }

  componentDidMount() {
    console.log("Critical Flow", this.props);
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
          links: data.links
        });
      }
    }).catch(error => console.log('error', error));
  }

  handleFlowCheck = (key,event) => {
    const {flows_ch} = this.state;
    flows_ch[key] = event.target.checked;
    this.setState({
      flows_ch
    });
  }

  handleLinksCheck = (item,event) => {
    const {links_ch} = this.state;
    links_ch[item] = event.target.checked;
    this.setState({
      links_ch
    });
  }

  handleFormChange = event => {
    const target = event.target;
    let value;
    //console.log(target.value);
    if (target.name === "time"){
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

  runLink = () => {
    let myHeaders = new Headers();
    myHeaders.append("Content-Type","application/json")

    let flows = Object.entries(this.state.flows_ch).filter(([key,value]) =>
      value
    ).map(([key,value]) =>
      key
    );
    let links = Object.entries(this.state.links_ch).filter(([key,value]) =>
      value
    ).map(([key,value]) =>
      key
    );
    // Create the body of the request
    let json = JSON.stringify({
      flows,
      links,
      "failure_rate": this.state.lambda,
      "time": this.state.time,
      "tolerance": this.state.tolerance
    });

    let requestOptions = {
      method: 'POST',
      body: json,
      headers: myHeaders,
      redirect: 'follow'
    };
    let {session_name} = this.props.match.params;
    fetch(`http://localhost:5000/critf_link?session_name=${session_name}&eval_name=${this.state.eval_name}`,requestOptions)
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
        <h4>Impact of Link Failure</h4>
        <p>
          Select a set of links to fail to find the probability that the connectivity of the selected
          flow F is lost as a result of link failures when the controller is disconnected from the network
          for a period of time specified by the the user.
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
              value={this.state.tolerance}
              onChange={this.handleFormChange}
            />
          </label>
        </form>
        <div className="trackerContainer">
          {/* Display list of all flows and links*/}
          <ItemTracker
            name={"Flows"}
            items={this.state.flows}
            items_ch={this.state.flows_ch}
            itemType={"flow"}
            listType={"checkbox"}
            handleItemCheck={this.handleFlowCheck}
          />
          <ItemTracker
            name={"Links"}
            items={this.state.links}
            items_ch={this.state.links_ch}
            itemType={"links"}
            listType={"checkbox"}
            handleItemCheck={this.handleLinksCheck}
          />
        </div>
        <Button onClick={this.runLink}>Run</Button>
      </div>
    );
  }
}

export default withRouter(CriticalFlows);