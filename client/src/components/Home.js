import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';

import ListSelect from './ListSelect';

class Home extends Component {
  constructor(props) {
    super(props);
    this.state = {
      show_up: false,
      show_ld: false,
      success: false,
      name: '',
      mh: '0',
      error: undefined,
      topo_file: undefined,
      rule_file: undefined,
      node_file: undefined,
      session: undefined
    };
    this.createSession = this.createSession.bind(this);
    this.handleUploadChange = this.handleUploadChange.bind(this);
  }

  showUpload = () => {
    this.setState({show_up: true});
  }

  hideUpload = () => {
    this.setState({show_up: false});
  }

  showLoad = () => {
    this.setState({show_ld: true});
  }

  hideLoad = () => {
    this.setState({show_ld: false});
  }

  handleUploadChange = event => {
    const target = event.target;
    const value = (target.type === 'file') ? target.files[0] : target.value;
    const name = target.name;

    this.setState({
      [name]: value
    });
  }

  createSession = async () => {
    // call post request to api 
    const formData = new FormData();
    formData.append("topology", this.state.topo_file,this.state.topo_file.name);
    formData.append("rules", this.state.rule_file,this.state.rule_file.name);
    formData.append("nodeIPs", this.state.node_file,this.state.node_file.name);

    let requestOptions = {
      method: 'POST',
      body: formData,
      redirect: 'follow'
    };
    await fetch(`http://localhost:5000/upload?name=${this.state.name}&mh=${this.state.mh}`,requestOptions)
    .then(rsp => rsp.json())
    .then(data => {
      console.log("upload",data);
      if (data.success) {
        this.setState({
          success: data.success,
          session: data.session
        });
      } else {
        this.setState({
          error: data.message
        });
      }
    }).catch(error => {
      // catching errors when backend fails
      console.log('error', error);
    });
    console.log(this.state);
    // redirect to session page
    const {history} = this.props;
    if (this.state.success){
      history.push(`/session/${this.state.session}`);
    }
  }

  render() {
    return (
      <div>
        <h2>Home</h2>
        <p>
          Get started by creating a new session with a network topology, or
          load in a previously created session.
        </p>
        <div>
          <Button onClick={this.showUpload}>
            Create Session
          </Button>
          <Button onClick={this.showLoad}>
            Load Session
          </Button>
        </div>

        {/* Modal Components */}
        <Modal id="uploadModal"
          show={this.state.show_up}
          onHide={this.hideUpload}
          size="lg"
          aria-labelledby="contained-modal-title-vcenter"
          centered
        >
          <Modal.Header closeButton>
            <Modal.Title id="contained-modal-title-vcenter">
              Upload New Sessions
            </Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {/* Error message handling goes here*/}
            {this.state.error && 
              <div style={{color:'red'}}>
                Error: {this.state.error}
              </div>
            }
            <form>
              <label>
                Session Name:
                <input 
                  type="text"
                  name="name"
                  value={this.state.name}
                  onChange={this.handleUploadChange}
              />
              </label>
              <label>
                Minimum Hops:
                <input 
                  type="text"
                  name="mh"
                  value={this.state.mh}
                  onChange={this.handleUploadChange}
              />
              </label>
              <label>
                Topology File:
                <input 
                  name="topo_file"
                  type="file"
                  multiple={false}
                  accept={".json"}
                  onChange={this.handleUploadChange}
                  />
              </label>
              <label>
                Flow Rules File:
                <input
                  name="rule_file"
                  type="file"
                  multiple={false}
                  accept={".json"}
                  onChange={this.handleUploadChange}
                />
              </label>
              <label>
                NodeIPs File:
                <input
                  name="node_file"
                  type="file"
                  multiple={false}
                  accept={".json"}
                  onChange={this.handleUploadChange}
                />
              </label>
            </form>
          </Modal.Body>
          <Modal.Footer>
            <Button onClick={this.createSession}>Create</Button>
          </Modal.Footer>
        </Modal>
        {/* This is the loading modal */}
        <ListSelect
          show={this.state.show_ld}
          onHide={this.hideLoad}
        />
      </div>
    );
  }
}


export default withRouter(Home);