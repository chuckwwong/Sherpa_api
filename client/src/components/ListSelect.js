import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
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
    }).catch(error => console.log('error', error));
  }

  handleRadio = event => {
    const target = event.target;
    console.log(target.value);
    this.setState({
      name: target.value
    });
  }

  loadSession = async () => {
    await fetch(`http://localhost:5000/load?session_name=${this.state.name}`)
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
      <div className="radio">
        {this.state.sessions.map((item,index) => (
          <div>
            <label>
              <input
                type="radio"
                value={item}
                checked={this.state.name === item}
                onChange={this.handleRadio}
              />
              {item}
            </label>
          </div>
        ))}
      </div>
    );
  }

  render() {
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
          <p>
            Select one of the previously created sessions to load.
          </p>
          {/* Function to list out all sessions, and let user select one*/}
          {this.listSessions()}
        </Modal.Body>
        <Modal.Footer>
          <Button disabled={this.state.name === ''} onClick={this.loadSession}>Load</Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

export default withRouter(ListSelect);