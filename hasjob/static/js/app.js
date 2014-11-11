// ROT13 link handler
function unrot13() {
  $("a.rot13").each(function() {
    if ($(this).attr('data-href')) {
      var decoded = $(this).attr('data-href').replace(/[a-zA-Z]/g, function(c) {
        return String.fromCharCode((c<="Z"?90:122)>=(c=c.charCodeAt(0)+13)?c:c-26);
      });
      $(this).attr('href', decoded);
      $(this).removeAttr('data-href');
      $(this).removeClass('rot13');
    }
  });
}

function handleGroupClick(){
  // replaces the group with individual stickies when clicked
  $('#stickie-area li.grouped').on('click', function(e){
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

$(function() {
  unrot13();
  handleGroupClick();
});
