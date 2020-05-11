import React, {Component} from 'react';
import {withRouter, useParams} from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import {OverlayTrigger, Tooltip} from 'react-bootstrap';

import ListSelect from './ListSelect';

class Session extends Component {
  constructor(props){
    super(props);
    this.state = {
      eval_name: '',
      flows: this.props.flows,
      links: this.props.links,
      flows_s: [],
      links_s: [],
      flows_ch: {},
      links_ch: {},
      output_f: undefined
    };
    //this.handleName = this.handleName.bind(this);
    //this.runExp = this.runExp.bind(this);
    this.listLinks = this.listLinks.bind(this);
    this.listFlows = this.listFlows.bind(this);
    this.handleFlowCheck = this.handleFlowCheck.bind(this);
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

  listLinks() {
    return (
      <div>
        {this.state.links.map((item,index) => (
          <label>
            <input
              type="checkbox"
              checked={!!this.state.links_ch[item]}
              onChange={event => this.handleLinksCheck(item,event)}
              key={index} 
            />
            {item}
          </label>
        ))}
      </div>
    );
  }

  dispTooltip(value) {
    return (
      <div>
        Visited:
        {value.visited.map((item,index) =>(
          <div key={index}>
            {item}
          </div>
        ))}
      </div>
    );
  }

  handleFlowCheck(key,event) {
    const {flows_ch} = this.state;
    flows_ch[key] = event.target.checked;
    this.setState({
      flows_ch
    });
  }

  listFlows() {
    const {flows} = this.state;
    return Object.entries(flows).map(([key, value]) =>
      <div> 
        <label>
          <input
            type="checkbox"
            checked={!!this.state.flows_ch[key]}
            onChange={event => this.handleFlowCheck(key, event)}
          />
          {key}
          <OverlayTrigger
            placement="top"
            overlay={
              <Tooltip>
                {this.dispTooltip(value)}
              </Tooltip>
            }
          >
            <Button variant="secondary">?</Button>
          </OverlayTrigger>
        </label>
      </div>
    );
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
    fetch(`http://localhost:5000/run?session_name=${session_name}&eval_name=${this.state.eval_name}`,requestOptions)
    .then(rsp => rsp.blob())
    .then(blob => {
      let a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.setAttribute("download", this.state.eval_name+"_out.json");
      a.click();
    }).catch(error => console.log('error', error));
  }

  render() {
    if (!this.state.flows || !this.state.links) {
      return (
        <div>
          Loading...
        </div>
      );
    }
    const {history} = this.props;
    return (
      <div>
        <Button onClick={() => history.goBack()}>
          Back
        </Button>
        <h1>Session</h1>
        <p>Experiment Setup Instructions</p>
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
          {this.listFlows()}
          {this.listLinks()}
        </div>
        <Button onClick={this.runExp}>
          Run
        </Button>
      </div>
    );
  }
}


export default withRouter(Session);