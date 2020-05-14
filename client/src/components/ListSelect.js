import React, {Component} from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

class ListSelect extends Component {
  constructor(props) {
    super(props);
    this.state = {
      sessions: [],
      name: '',

    }
  }

  componentDidMount() {
    // need to call get loaded sessions
    fetch('http://localhost:5000/sessions',{method:"GET"}).then(rsp => rsp.json()).then(data => {
      console.log("session",data);
      this.setState({
        sessions: data.sessions
      });
      console.log("session r",this.state.sessions);
    }).catch(error => console.log('error', error));
  }

  deleteSession = () => {

  }

  loadSession = () => {
    // given selected session name, call get request
    // get session name and pass props
    fetch(`http://localhost:5000/load?session_name=${this.state.name}`)
    .then(rsp => rsp.json())
    .then(data => {
      console.log(data);
      if (data.success) {
        this.setState({
          success: true,
          session: data.session
        });
      } else {
        this.setState({
          error: data.message
        });
      }
    }).catch(error => console.log('error', error));
    // redirect to session page
    const {history} = this.props;
    if (this.state.success) {
      history.push(`/session/${this.state.session}`);
    }
  }

  listSessions = () => {
    return (
      <div>
        {this.state.sessions.map((item,index) => (
          <label id={item}>
            {item}
          </label>
        ))}
      </div>
    );
  }

  render() {
    //const {} = this.props;

    // move load modal from home here
    return (
      <Modal id="loadModal"
        show={this.props.show}
        onHide={this.props.onHide}
      >
        <Modal.Header closeButton>
          <Modal.Title id="contained-modal-title-vcenter">
            Load Experiment Sessions
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {/* Function to list out all sessions, and let user select one*/}
          {this.listSessions()}
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={this.deleteSession}>Delete</Button>
          <Button onClick={this.loadSession}>Load</Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

export default ListSelect;