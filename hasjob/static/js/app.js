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

$(function() {
  unrot13();
});
