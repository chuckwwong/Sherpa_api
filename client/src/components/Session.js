import React, {Component} from 'react';
import {withRouter} from 'react-router-dom';
import Button from 'react-bootstrap/Button';

import ListSelect from './ListSelect';

class Session extends Component {
  constructor(props){
    super(props);
    this.state = {
      eval_name: '',
      flows_s: {},
      links_s: [],
      output_f: undefined
    };
    this.handleName = this.handleName.bind(this);
    this.runExp = this.runExp.bind(this);
  }

  componentDidMount() {

  }

  handleName = event => {
    const target = event.target;
    this.setState({
      [target.name]: target.value,
    });
  }

  runExp = () => {
    // use selected flows and links and run exp and return output
  }

  render() {
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
          <ListSelect
            flows={this.props.flows}
            links={this.props.links}
          />
        </div>
        <Button onClick={this.runExp}>
          Run
        </Button>
      </div>
    );
  }
}


export default withRouter(Session);