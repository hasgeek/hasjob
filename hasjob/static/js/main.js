define(
  [
    'react',
    'reactDom',
    'jquery',
    './components/hasjob'
  ],
  function (React, ReactDOM, $, Hasjob) {
    ReactDOM.render(<Hasjob />, document.getElementById('main-content')); //root
  }
)
