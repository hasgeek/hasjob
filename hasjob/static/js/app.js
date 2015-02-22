window.Hasjob = {};

window.Hasjob.JobPost = {
  handleStarClick: function (e) {
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
      },
      success: function(data) {
        // FIXME: Move user-facing text somewhere i18n capable:
        if (data.is_starred === true) {
          starlink.removeClass('fa-star-o').addClass('fa-star').parent().find('.pstar-caption').html("Favourited");
        } else {
          starlink.removeClass('fa-star').addClass('fa-star-o').parent().find('.pstar-caption').html("Favourite this");
        }
      }
    });
    e.preventDefault();
    return false;
  },
  handleGroupClick: function(){
    var outerTemplate = document.createElement('li');
    var innerTemplate = document.createElement('a');
    var node, outer, inner;
    outerTemplate.setAttribute('class', 'col-xs-12 col-md-3 col-sm-4 animated shake');
    innerTemplate.setAttribute('class', 'stickie');
    innerTemplate.setAttribute('rel', 'bookmark');
    // replaces the group with individual stickies when clicked
    $('#stickie-area').on('click', 'li.grouped', function(e){
      e.preventDefault();
      var group = this, parent=group.parentNode;

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
      $(".pstar").off().click(window.Hasjob.JobPost.handleStarClick);
    });
  }
};

$(function() {
  window.Hasjob.JobPost.handleGroupClick();
  $(".pstar").off().click(window.Hasjob.JobPost.handleStarClick);
});
