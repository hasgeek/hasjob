(function() {
  var containerDivs = document.getElementsByClassName('hasjob-embed');
  var hostnames = [];
  var urlParserElem = document.createElement('a');
  for (var index = 0; index < containerDivs.length; index++) {
    var iframeSrc, iframeId, hasjobIframe;
    urlParserElem.href = containerDivs[index].getAttribute('data-href');
    hostnames.push(urlParserElem.origin);
    iframeId = containerDivs[index].getAttribute('data-iframe-id');
    if(!iframeId) {
      iframeId = 'hasjob-iframe-' + Math.random().toString(36).slice(3);
    }
    if(urlParserElem.search) {
      iframeSrc = urlParserElem + '&embed=1&limit=';
    } else {
      iframeSrc = urlParserElem.origin + '/?embed=1&limit=';
    }
    iframeSrc = iframeSrc + 
      containerDivs[index].getAttribute('data-jobpost-limit') + 
      '&iframeid=' + iframeId;
    hasjobIframe = document.createElement('iframe');
    setAttributes(hasjobIframe, {
      'id': iframeId,
      'src': iframeSrc,
      'width': '100%',
      'height': '500px',
      'frameborder': '0',
      'scrolling': 'no'
    });
    containerDivs[index].appendChild(hasjobIframe);
  }
  function setAttributes(element, attributes) {
    for(var name in attributes) {
      element.setAttribute(name, attributes[name]);
    }
  }
  function handleMessage(event) {
    if(hostnames.indexOf(event.origin) !== -1) {
      var message = JSON.parse(event.data);
      console.log('mess', message);
      if(message.context == "iframe.resize" && message.id) {
        document.getElementById(message.id).setAttribute('height', message.height);
      }
    }
  }
  window.addEventListener('message', handleMessage, false);
})(); 
