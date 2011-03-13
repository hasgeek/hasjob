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
