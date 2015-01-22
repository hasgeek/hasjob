$(function() {
  var handleGroupClick = function(){
    // replaces the group with individual stickies when clicked
    $('#stickie-area li.grouped').one('click', function(e){
      e.preventDefault();
      var group = $(this);
      $($.map(group.children(), function(node){
        return "<li class='col-xs-12 col-md-3 col-sm-4 animated shake'>" +
                 "<a class='stickie' href="+$(node).data('href')+" rel='bookmark'>" + $(node).html() + "</a> \
               </li>";
        }).join(""))
      .insertBefore(group);
      $(group).remove();
    });
  };
  handleGroupClick();
});
