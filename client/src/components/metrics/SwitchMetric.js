import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
import Button from 'react-bootstrap/Button';

import ItemTracker from './ItemTracker';

class SwitchMetric extends Component {
  constructor(props){
    super(props);
    this.state = {
      eval_name: '',
      flows: {},
      flows_ch: {},
      switches: {},
      switches_ch: {},
      output_f: undefined
    };
    this.handleFlowCheck = this.handleFlowCheck.bind(this);
  }

  componentDidMount() {
    console.log("Switch Metric",this.props);
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

  handleName = event => {
    const target = event.target;
    this.setState({
      [target.name]: target.value,
    });
  }

  handleFlowCheck = (key,event) => {
    const {flows_ch} = this.state;
    flows_ch[key] = event.target.checked;
    this.setState({
      flows_ch
    });
  }

  handleSwitchCheck = (key,event) => {
    const {switches_ch} = this.state;
    switches_ch[key] = event.target.checked;
    this.setState({
      switches_ch
    })
  }

  runSwitch = () => {
    let myHeaders = new Headers();
    myHeaders.append("Content-Type","application/json")

    let flows = Object.entries(this.state.flows_ch).filter(([key,value]) =>
      value
    ).map(([key,value]) =>
      key
    );
    let switches = Object.entries(this.state.switches_ch).filter(([key,value]) =>
      value
    ).map(([key,value]) =>
      key
    );
    let json = JSON.stringify({flows,switches});

    let requestOptions = {
      method: 'POST',
      body: json,
      headers: myHeaders,
      redirect: 'follow'
    };
    let {session_name} = this.props.match.params;
    fetch(`http://localhost:5000/switch?session_name=${session_name}&eval_name=${this.state.eval_name}`,requestOptions)
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
        <h3>Switch Metrics</h3>
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
        <Button onClick={this.runSwitch}>Run</Button>
        <p>
          Switch Metric Instructions: Select switches
          and see which flows are impacted.
        </p>
        {/*List all flows switches in network here */}
        <ItemTracker
            name={"Flows"}
            items={this.state.flows}
            items_ch={this.state.flows_ch}
            itemType={"flow"}
            listType={"checkbox"}
            handleItemCheck={this.handleFlowCheck}
        />
        <ItemTracker
            name={"Switches"}
            items={this.state.switches}
            items_ch={this.state.switches_ch}
            itemType={"switch"}
            listType={"checkbox"}
            handleItemCheck={this.handleSwitchCheck}
        />
      </div>
    );
  }
}

export default withRouter(SwitchMetric);