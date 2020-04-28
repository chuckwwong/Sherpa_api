import React, {Component} from 'react';

class ListSelect extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    const {flows,links} = this.props;

    return (
      <div>
        <div>
          Flow list goes here
        </div>
        <div>
          Link list goes here
        </div>
      </div>
    );
  }
}

export default ListSelect;