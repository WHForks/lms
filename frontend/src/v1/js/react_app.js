import React from 'react';
import ReactDOM from 'react-dom';

import { showComponentError } from 'utils';
import AlumniList from "./screens/AlumniList/index";
import AlumniPromote from "./screens/AlumniPromote/index";
import AssignmentsCheckQueue from "./screens/AssignmentsCheckQueue/index";
import CitySelect from "./screens/CitySelect/index";
import StudentIdEdit from "./screens/StudentIdEdit/index";

const components = {
  AlumniList,
  AlumniPromote,
  AssignmentsCheckQueue,
  CitySelect,
  StudentIdEdit,
};

export function renderComponent(el) {
  let componentName = el.dataset["component"];
  const component = components[componentName];

  if (!component) {
    showComponentError(new Error(`Unknown React component: ${componentName}`));
    return;
  }

  const runRender = () => {
    let props = {
      initialState: {},
    };
    let init = el.dataset["init"];
    if (init !== null) {
      let data = JSON.parse(init);
      if (data.props !== undefined) {
        Object.keys(data.props).map((k) => {
          props[k] = data.props[k];
        });
        delete data.props;
      }
      props.initialState = data.state || {};
    }
    let Component = component.default || component;
    ReactDOM.render(React.createElement(Component, props), el);
  };

  // Preserve polyfill hook if present on the component
  if (Object.prototype.hasOwnProperty.call(component, "polyfills")) {
    Promise.all(component.polyfills)
      .then(runRender)
      .catch((error) => showComponentError(error));
  } else {
    runRender();
  }
}
