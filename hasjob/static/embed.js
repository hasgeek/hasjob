(function() {
  var containerDiv = document.getElementById('hasjob');
  var link = containerDiv.getAttribute('data-href');
  link = link.substr(-1) !== '/' ? link : link.substr(0, link.length-1);
  var jobPostLimit = containerDiv.getAttribute('data-jobpost-limit');
  var iframeSrc = link + '/?embed=1&limit=' + jobPostLimit;
  var hasjobIframe = document.createElement('iframe');
  hasjobIframe.setAttribute('id', 'hasjob-embed');
  hasjobIframe.setAttribute('src', iframeSrc);
  hasjobIframe.setAttribute('width', '100%');
  hasjobIframe.setAttribute('height', '500px');
  hasjobIframe.setAttribute('frameborder', '0');
  hasjobIframe.setAttribute('scrolling', 'no');
  containerDiv.appendChild(hasjobIframe);
  var handleMessage = function(event) {
    if(event.origin == link) {
      var message = JSON.parse(event.data);
      if(message.context == "iframe.resize") {
        hasjobIframe.setAttribute('height', message.height);
      }
    }
  }
  window.addEventListener('message', handleMessage, false);
})(); 
