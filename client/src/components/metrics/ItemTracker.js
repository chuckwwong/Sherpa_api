import React, {Component} from 'react';
import Button from 'react-bootstrap/Button';
import {OverlayTrigger, Tooltip} from 'react-bootstrap';

// Class keeps track of either links, flows, or switches

/*
  props:
    - name: Name of items listed
    - items: items to keep track of
    - items_ch: items that are selected
    - itemType: either considered, flow, links, or switches
    - listType: either select one, or select multiple
    - handleItemCheck: function passed from parent to keep track of selected items
*/
class ItemTracker extends Component {

    listItems = () => {
      if (this.props.itemType === "links") {
        return (
          <div>
            {this.props.items.map((item,index) =>(
              <div>
                <label key={item}>
                  <input
                    type={this.props.listType}
                    checked={!!this.props.items_ch[item]}
                    onChange={event => this.props.handleItemCheck(item,event)}
                  />
                  {item}
                </label>
              </div>
            ))}
          </div>
        );
      } else {
        // listing out object types
        return Object.entries(this.props.items).map(([key,value]) => 
          <div>
            <label key={key}>
              <input
                type={this.props.listType}
                checked={!!this.props.items_ch[key]}
                onChange={event => this.props.handleItemCheck(key,event)}
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
              {/*
                this.props.itemType === "neigh" &&
                <>Hops:</>
              }
              {
                this.props.itemType=== "neigh" &&
                <input
                  type="number"
                  disabled={!this.props.items_ch[key]}
                  min={0}
                  //max={this.props.flows}
                  value={this.props.hops[key]}
                  onChange={this.handleHopsCheck}
                />
              */}
            </label>
          </div>
         );
      }
    }

    dispTooltip = (value) => {
      if (this.props.itemType === "flow") {
        return (
          <div>
            <div>
            nw_dst:
            {value.nw_dst}
            </div>
            <div>
            Ingress Port:
            {value.ingress_port}
            </div>
            <div>
              Visited:
              {value.visited.map((item,index) =>(
                <div key={index}>
                  {item}
                </div>
              ))}
            </div>
          </div>
        );
      } else if (this.props.itemType === "switch" || this.props.itemType === "neigh") {
        return (
          <div>
            Neighbor:
            {value.map((item,index) =>(
              <div key={index}>
                {item}
              </div>
            ))}
          </div>
        );
      }
    }

    render() {
        return(
          <div className="listParent">
            {this.props.name}:
            <div className="list">
              {this.listItems()}
            </div>
          </div>
        );
    }
}

export default ItemTracker;