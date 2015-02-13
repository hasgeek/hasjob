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
      console.log(data);
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
  var handleGroupClick = function(){
    // replaces the group with individual stickies when clicked
    $('#stickie-area').on('click', 'li.grouped', function(e){
      e.preventDefault();
      var group = $(this);
      $($.map(group.children(), function(node){
        return "<li class='col-xs-12 col-md-3 col-sm-4 animated shake'>" +
                 "<a class='stickie' href="+$(node).data('href')+" rel='bookmark'>" + $(node).html() + "</a> \
               </li>";
        }).join(""))
      .insertBefore(group);
      $(group).remove();
      $(".pstar").off().click(star_click);
    });
  };
  handleGroupClick();
  $(".pstar").off().click(star_click);
});
