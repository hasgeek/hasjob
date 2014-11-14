$(function() {
  var handleGroupClick = function(){
    // replaces the group with individual stickies when clicked
    $('#stickie-area li.grouped').one('click', function(e){
      e.preventDefault();
      var group = $(this);
      $.each(group.children(), function(index, node){
        if (($(node).prop('tagName') === 'A') && index === 0) {
          $(node).attr('href', $(node).data('href'));
        }
        else {
          group.after("<li class='col-xs-12 col-md-3 col-sm-4 animated shake'>" + "<a class='stickie' href="+$(node).data('href')+" rel='bookmark'>" + $(node).html() + "</a></li>");
          $(node).remove();
        }
      });
      group.addClass('animated shake');
      group.removeClass('grouped');
    });
  };
  handleGroupClick();
});
