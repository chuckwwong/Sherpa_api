import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';

class Home extends Component {
  constructor(props) {
    super(props);
    this.state = {
      show_up: false,
      show_ld: false,
      success: false,
      sessions: {},
      name: '',
      mh: '0',
      error: '',
      topo_file: undefined,
      rule_file: undefined,
      node_file: undefined,
      session: undefined,
      flows: undefined,
      links: undefined,
    };
    this.showUpload = this.showUpload.bind(this);
    this.hideUpload = this.hideUpload.bind(this);
    this.showLoad = this.showLoad.bind(this);
    this.hideLoad = this.hideLoad.bind(this);
    this.createSession = this.createSession.bind(this);
    this.loadSession = this.loadSession.bind(this);
    this.handleUploadChange = this.handleUploadChange.bind(this);
  }

  showUpload = () => {
    this.setState({show_up: true});
  }

  hideUpload = () => {
    this.setState({show_up: false});
  }

  showLoad = () => {
    // need to call get loaded sessions
    fetch('http://localhost:5000/sessions',{method:"GET"}).then(rsp => rsp.json()).then(data => {
      console.log("session",data);
      this.setState({
        sessions: this.data
      });
    }).catch(error => console.log('error', error));

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
          session: data.session,
          flows: data.flows,
          links: data.links 
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
    // TODO: THIS IS BAD, use history to pass props instead
    this.props.uploadResp(this.state.session,this.state.flows,this.state.links);
    console.log(this.state);
    // redirect to session page
    const {history} = this.props;
    if (this.state.success){
      history.push(`/session/${this.state.session}`)
    };
  }

  loadSession = () => {
    // given selected session name, call get request
    // get flows and links and session name and pass props
    fetch(`http://localhost:5000/load?session_name=${this.state.name}`)
    .then(rsp => rsp.json())
    .then(data => {
      console.log(data);
      if (data.success) {
        this.setState({
          success: true,
          session: data.session,
          flows: data.flows,
          links: data.links 
        });
      }
    }).catch(error => console.log('error', error));
    this.props.uploadResp(this.state.session,this.state.flows,this.state.links);
    // redirect to session page
    const {history} = this.props;
    if (this.state.success) history.push("/session");
  }

  render() {
    return (
      <div>
        <h2>Not Sure If I Need a Header</h2>
        <p>Probably will put instructions right here</p>
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
            <p>
              Basic Upload Instructions
              {this.state.error}
            </p>
            {/* Error message handling goes here*/}
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

        <Modal id="loadModal"
          show={this.state.show_ld}
          onHide={this.hideLoad}
        >
          <Modal.Header closeButton>
            <Modal.Title id="contained-modal-title-vcenter">
              Load Experiment Sessions
            </Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <p>
              Listing out previous sessions will go here
            </p>
          </Modal.Body>
          <Modal.Footer>
            <Button>Delete</Button>
            <Button onClick={this.loadSession}>Load</Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  }
}


export default withRouter(Home);