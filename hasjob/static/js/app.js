function star_click(e) {
  var starlink = $(this);
  var csrf_token = $("meta[name='csrf-token']").attr('content');
  starlink.addClass('fa-spin');
  $.ajax('/star/' + $(this).data('id'), {
    type: 'POST',
    data: {
      csrf_token: csrf_token
    },
    dataType: 'json',
    complete: function() {
      starlink.removeClass('fa-spin');
      // TODO: Show error
    },
    success: function(data) {
      if (data.is_starred === true) {
        starlink.removeClass('fa-star-o').addClass('fa-star');
      } else {
        starlink.removeClass('fa-star').addClass('fa-star-o');
      };
    }
  });
  e.preventDefault();
  return false;
};

$(function() {
  var outerTemplate = document.createElement('li');
  outerTemplate.setAttribute('class', 'col-xs-12 col-md-3 col-sm-4 animated shake');
  var innerTemplate = document.createElement('a');
  innerTemplate.setAttribute('class', 'stickie');
  innerTemplate.setAttribute('rel', 'bookmark');

  var handleGroupClick = function(){
    // replaces the group with individual stickies when clicked
    $('#stickie-area').on('click', 'li.grouped', function(e){
      e.preventDefault();
      var group = this, parent=group.parentNode;

      for (var i = 0; i < group.children.length; i++) {
        var node = group.children[i];
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
      $(".pstar").off().click(star_click);
    });
  };
  handleGroupClick();
  $(".pstar").off().click(star_click);
});
