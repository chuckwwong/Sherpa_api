import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
import Button from 'react-bootstrap/Button';

import ItemTracker from './ItemTracker';

class CustomSherpa extends Component {
  constructor(props){
    super(props);
    this.state = {
      eval_name: '',
      flows: {},
      links: [],
      flows_ch: {},
      links_ch: {},
      output_f: undefined
    };

    this.handleFlowCheck = this.handleFlowCheck.bind(this);
    this.handleLinksCheck = this.handleLinksCheck.bind(this);
  }

  componentDidMount() {
    let {session_name} = this.props.match.params;
    console.log(session_name);
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

  handleName = event => {
    const target = event.target;
    this.setState({
      [target.name]: target.value,
    });
  }

  handleLinksCheck(item,event) {
    const {links_ch} = this.state;
    links_ch[item] = event.target.checked;
    this.setState({
      links_ch
    });
  }

  handleFlowCheck(key,event) {
    const {flows_ch} = this.state;
    flows_ch[key] = event.target.checked;
    this.setState({
      flows_ch
    });
  }

  runExp = () => {
    // use selected flows and links and run exp and return output
    let myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    let flows = Object.entries(this.state.flows_ch).filter(([key,value]) =>
      value
    ).map(([key,value])=>
      key
    );
    let links = Object.entries(this.state.links_ch).filter(([key,value]) =>
      value
    ).map(([key,value])=>
      key
    );
    let json = JSON.stringify({flows,links});

    let requestOptions = {
      method: 'POST',
      body: json,
      headers: myHeaders,
      redirect: 'follow'
    };
    let {session_name} = this.props.match.params;
    fetch(`http://localhost:5000/sherpa?session_name=${session_name}&eval_name=${this.state.eval_name}`,requestOptions)
    .then(rsp => rsp.blob())
    .then(blob => {
      let a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.setAttribute("download", this.state.eval_name+"_out.json");
      a.click();
    }).catch(error => console.log('error', error));
  }

  render() {
    return (
      <div>
        <h3>Custom Sherpa Metrics</h3>
        <p>
          Custom Sherpa Metric Instructions: This option allows you
          to interface with the sherpa engine directly. Select all 
          important flows and links to fail.
        </p>
        <div>
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
          {/*Display list of all flows and links*/}
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
        <Button onClick={this.runExp}>Run</Button>
      </div>
    );
  }
}

export default withRouter(CustomSherpa);