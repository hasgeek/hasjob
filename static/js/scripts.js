function radioHighlight(radioName, highlightClass) {
    var selector = "input[name='" + radioName + "']";
    $(selector + ":checked").parent().addClass(highlightClass);
    var handler = function() {
        $(selector).parent().removeClass(highlightClass);
        $(selector + ":checked").parent().addClass(highlightClass);
    };
    $(selector).change(handler);
    $(selector).click(handler);
}

// ROT13 link handler
$(function() {
  $("a.rot13").each(function() {
    if ($(this).attr('data-href')) {
      var decoded = $(this).attr('data-href').replace(/[a-zA-Z]/g, function(c) {
        return String.fromCharCode((c<="Z"?90:122)>=(c=c.charCodeAt(0)+13)?c:c-26);
        });
      $(this).attr('href', decoded);
      $(this).removeAttr('data-href');
      $(this).removeClass('rot13');
    };
  });
});
