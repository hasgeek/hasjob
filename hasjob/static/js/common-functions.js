define(
  [
    'exports',
    'jquery'
  ],
  function (exports, $) {
    exports.expandJobGroup = function(groupedElement){
      var outerTemplate = document.createElement('li');
      var innerTemplate = document.createElement('a');
      var node, outer, inner;

      outerTemplate.setAttribute('class', 'col-xs-12 col-md-3 col-sm-4 animated shake');
      innerTemplate.setAttribute('class', 'stickie');
      innerTemplate.setAttribute('rel', 'bookmark');

      var group = groupedElement;
      var parent=group.parentNode;

      for (var i = 0; i < group.children.length; i++) {
        node = group.children[i];
        outer = outerTemplate.cloneNode(false);
        inner = innerTemplate.cloneNode(false);
        inner.setAttribute('href', node.getAttribute('data-href'));
        while (node.firstChild) {
          inner.appendChild(node.firstChild);
        }
        outer.appendChild(inner);
        parent.insertBefore(outer, group);
      }
      parent.removeChild(group);
    };

    exports.makeAjaxGet = function (url, successCallback) {
      $.ajax({
        url: url,
        type: 'GET',
        data: postData,
        success: successCallback,
        error: function (httpRequest, status, error) {
          console.log(error);
        }
      });
    };

    exports.makeAjaxPost = function (url, postData, successCallback) {
      $.ajax({
        url: url,
        type: 'POST',
        dataType: 'json',
        data: postData,
        success: successCallback,
        error: function (httpRequest, status, error) {
          console.log(error);
        }
      });
    };
  }
)
