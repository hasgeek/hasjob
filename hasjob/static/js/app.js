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
          starlink.removeClass('fa-star-o').addClass('fa-star').parent().find('.pstar-caption').html("Bookmarked");
        } else {
          starlink.removeClass('fa-star').addClass('fa-star-o').parent().find('.pstar-caption').html("Bookmark this");
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

Hasjob.PaySlider = function(options){
  this.selector = options.selector;
  this.slider = null;
  this.start = options.start,
  this.end = options.end;
  this.minField = options.minField;
  this.maxField = options.maxField;
  this.init();
}

Hasjob.PaySlider.indian_rupee_encoder = function(value) {
  value = value.toString();
  value = value.replace(/[^0-9.]/g, '');  // Remove non-digits, assume . for decimals
  var afterPoint = '';
  if (value.indexOf('.') > 0)
    afterPoint = value.substring(value.indexOf('.'), value.length);
  value = Math.floor(value);
  value = value.toString();
  var lastThree = value.substring(value.length - 3);
  var otherNumbers = value.substring(0, value.length - 3);
  if (otherNumbers !== '')
      lastThree = ',' + lastThree;
  var res = '₹' + otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + lastThree + afterPoint;
  return res;
};

Hasjob.PaySlider.prefix = function(currency){
  var currencyMap = {
    'na': '¤',
    'inr': '₹',
    'usd': '$',
    'sgd': '$',
    'eur': '€',
    'gbp': '£'
  };
  return currencyMap[currency.toLowerCase()];
};

Hasjob.PaySlider.toNumeric = function(str){
  return str.slice(1).replace(/,/g, '');
}

Hasjob.PaySlider.prototype.init = function(){
  this.slider = $(this.selector).noUiSlider({
    start: [this.start, this.end],
    step: 1,
    connect: true,
    behaviour: "tap",
    range: {
      'min': [0, 5000],
      '5%':  [100000, 10000],
      '80%': [1000000, 50000],
      '90%': [2000000, 100000],
      'max': [10000000, 1000000],
    },
    format: wNumb({
      decimals: 0,
      thousand: ',',
      prefix: '¤'
    })
  });
  this.slider.Link('lower').to($(this.minField));
  this.slider.Link('upper').to($(this.maxField));
  return this;
};

Hasjob.PaySlider.prototype.resetSlider = function(currency) {
  var start = Hasjob.PaySlider.toNumeric(this.slider.val()[0]),
      end = Hasjob.PaySlider.toNumeric(this.slider.val()[1]),
      prefix = '¤',
      thousand = ',',
      encoder = null;

  if (currency === 'INR') {
    encoder = Hasjob.PaySlider.indian_rupee_encoder;
  };

  prefix = Hasjob.PaySlider.prefix(currency);

  if (encoder === null) {
    this.slider.noUiSlider({
      start: [this.start, this.end],
      format: wNumb({
        decimals: 0,
        thousand: thousand,
        prefix: prefix,
      })
    }, true);
  } else {
    this.slider.noUiSlider({
      start: [this.start, this.end],
      format: wNumb({
        decimals: 0,
        thousand: thousand,
        prefix: prefix,
        edit: encoder
      })
    }, true);
  };
  this.slider.Link('lower').to($(this.minField));
  this.slider.Link('upper').to($(this.maxField));
};

window.Hasjob.Util = {
  getQueryParam: function(variable) {
    // Source: https://css-tricks.com/snippets/javascript/get-url-variables/
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i=0;i<vars.length;i++) {
     var pair = vars[i].split("=");
     if(pair[0] == variable){return pair[1];}
   }
   return(false);
 }
};

$(function() {
  window.Hasjob.JobPost.handleGroupClick();
  $(".pstar").off().click(window.Hasjob.JobPost.handleStarClick);
});
