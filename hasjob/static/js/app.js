//window.Hasjob initialized in layout.html

Hasjob.Util = {
  updateGA: function(){
    /*
      Resets the path in the tracker object and updates GA with the current path.
      To be called after updating the URL with pushState or replaceState.
      Reference: https://developers.google.com/analytics/devguides/collection/analyticsjs/single-page-applications
    */
    if (window.ga) {
      var path = window.location.href.split(window.location.host)[1];
      window.ga('set', 'page', path);
      window.ga('send', 'pageview');
    }
  }
};

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
    $('#main-content').on('click', '#stickie-area li.grouped', function(e){
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

window.Hasjob.StickieList = {
  init: function(){
    var stickielist = this;
  },
  loadmore: function(config){
    var stickielist = this;

    var shouldLoad = function(){
      return (
        stickielist.loadmoreRactive.get('enable') &&
        !stickielist.loadmoreRactive.get('loading')
      );
    };

    var load = function(){
      if (shouldLoad()){
        stickielist.loadmoreRactive.set('loading', true);
        $.ajax(stickielist.loadmoreRactive.get('url'), {
          success: function(data) {
            $('ul#stickie-area').append(data.trim());
            stickielist.loadmoreRactive.set('loading', false);
            stickielist.loadmoreRactive.set('error', false);
          },
          error: function() {
            stickielist.loadmoreRactive.set('error', true);
            stickielist.loadmoreRactive.set('loading', false);
          }
        });
      }
    };

    if (!config.enable) {
      // Hide template
      if (this.hasOwnProperty('loadmoreRactive')){
        this.loadmoreRactive.set('enable', config.enable);
      }
    } else {
      if (!config.paginated) {
        // Initial render
        stickielist.loadmoreRactive = new Ractive({
          el: 'loadmore',
          template: '#loadmore-ractive',
          data: {
            error: false,
            loading: false,
            url: config.url,
            enable: config.enable
          }
        });

        stickielist.loadmoreRactive.on('forceload', function(event) {
          load();
        });

        $("#loadmore").appear().on('appear', function(event, element) {
          load();
        });
      } else {
        // Update rendered template
        this.loadmoreRactive.set('url', config.url);
      }
    }
  },
  refresh: function(){
    // progress indicator
    NProgress.configure({ showSpinner: false });
    NProgress.start();
    var filterParams = window.Hasjob.Filters.toParam();
    var searchUrl = window.Hasjob.Config.baseURL;
    if (filterParams.length) {
      var searchUrl = window.Hasjob.Config.baseURL + '?' + window.Hasjob.Filters.toParam();
    }
    $.ajax(searchUrl, {
      method: 'POST',
      headers: {
        'X-PJAX': true
      },
      success: function(data) {
        $('#main-content').html(data);
        window.Hasjob.Filters.refresh();
        NProgress.done();
      }
    });
    history.replaceState({reloadOnPop: true}, '', window.location.href);
    history.pushState({reloadOnPop: true}, '', searchUrl);
    window.Hasjob.Util.updateGA();
  }
};

window.Hasjob.Filters = {
  toParam: function(){
    var sortedFilterParams = this.formatFilterParams($('#js-job-filters').serializeArray());
    if (sortedFilterParams.length) {
      return $.param(sortedFilterParams);
    } else {
      return '';
    }
  },
  init: function(){
    var filters = this;
    var keywordTimeout;

    filters.ractive = new Ractive({
      el: 'job-filters-ractive-template',
      template: '#filters-ractive',
      data: {
        jobLocations: window.Hasjob.Config.jobLocationFilters,
        jobTypes: window.Hasjob.Config.jobTypeFilters,
        jobCategories: window.Hasjob.Config.jobCategoryFilters,
        selectedLocations: window.Hasjob.Config.selectedLocations,
        selectedTypes: window.Hasjob.Config.selectedTypes,
        selectedCategories: window.Hasjob.Config.selectedCategories,
        selectedQuery: window.Hasjob.Config.selectedQuery,
        selectedEquity: window.Hasjob.Config.selectedEquity
      }
    });
    filters.filterDropdownClosed = true;

    $('.hg-site-nav-toggle').find('i').removeClass('fa-bars').addClass('fa-search');
    $('#hg-sitenav').on('shown.bs.collapse', function() {
      $('.hg-site-nav-toggle').find('i').removeClass('fa-search').addClass('fa-close');
    });
    $('#hg-sitenav').on('hidden.bs.collapse', function() {
      $('.hg-site-nav-toggle').find('i').removeClass('fa-close').addClass('fa-search');
    });

    //remove white spaces keyword input value
    $('#job-filters-keywords').on('change',function(){
      $(this).val($(this).val().trim());
    });

    $('.js-handle-filter-change').on('change', function(e){
      window.Hasjob.StickieList.refresh();
    });

    $('.js-handle-keyword-update').on('keyup', function(){
      window.clearTimeout(keywordTimeout);
      keywordTimeout = window.setTimeout(window.Hasjob.StickieList.refresh, 500);
    });

    $('#job-filters-location').multiselect({
      nonSelectedText: 'Location',
      numberDisplayed: 1,
      buttonWidth: '100%',
      enableFiltering: true,
      enableCaseInsensitiveFiltering: true,
      templates: {
        filter: '<li><div class="input-group input-group-sm"><div class="input-group-addon"><i class="fa fa-search"></i></div><input type="text" class="form-control" id="job-filter-location-search" placeholder="Search">',
        filterClearBtn: '<div class="input-group-addon job-filter-location-search-clear"><i class="fa fa-times"></i></div></div></li>'
      },
      optionClass: function(element) {
        if ($(element).hasClass('unavailable')) {
          return 'unavailable';
        }
      },
      onDropdownShow: function(event, ui) {
        // stop header filter rollup when dropdown is open
        filters.filterDropdownClosed = false;
      },
      onDropdownHide: function(event, ui) {
        filters.filterDropdownClosed = true;
      }
    });

    // clear location search on clicking the clear control
    $('.job-filter-location-search-clear').click(function(e){
      $('#job-filter-location-search').val('');
    });

    $('#job-filters-type').multiselect({
      nonSelectedText: 'Job Type',
      numberDisplayed: 1,
      buttonWidth: '100%',
      optionClass: function(element) {
        if ($(element).hasClass('unavailable')) {
          return 'unavailable';
        }
      },
      onDropdownShow: function(event, ui) {
        // stop header filter rollup when dropdown is open
        filters.filterDropdownClosed = false;
      },
      onDropdownHide: function(event, ui) {
        filters.filterDropdownClosed = true;
      }
    });

    $('#job-filters-category').multiselect({
      nonSelectedText: 'Job Category',
      numberDisplayed: 1,
      buttonWidth: '100%',
      optionClass: function(element) {
        if ($(element).hasClass('unavailable')) {
          return 'unavailable';
        }
      },
      onDropdownShow: function(event, ui) {
        // stop header filter rollup when dropdown is open
        filters.filterDropdownClosed = false;
      },
      onDropdownHide: function(event, ui) {
        filters.filterDropdownClosed = true;
      }
    });

    $('#job-filters-pay').on('shown.bs.dropdown', function() {
      // stop header filter rollup when dropdown is open
      filters.filterDropdownClosed = false;
    });

    $('#job-filters-pay').on('hidden.bs.dropdown', function() {
      filters.filterDropdownClosed = true;
    });

    // Done button for filters on mobile
    $('#js-mobile-filter-done').click(function(event) {
      event.preventDefault();
      $('#hg-sitenav').collapse('toggle');
      $('body').removeClass('nav-open');
    });

    //On pressing ESC, close the filter dropdown if menu is open.
    $(document).keydown(function(event) {
      if (event.keyCode === 27 && $('#hg-sitenav').hasClass('in')) {
        event.preventDefault();
        $('#hg-sitenav').collapse('toggle');
        $('body').removeClass('nav-open');
      }
    });
  },
  formatFilterParams: function(formParams){
    var sortedFilterParams = [];
    var currencyVal = '';
    for (var fpIndex=0; fpIndex < formParams.length; fpIndex++) {
      // set value to empty string if currency is n/a
      if (formParams[fpIndex].name === 'currency') {
        if (formParams[fpIndex].value.toLowerCase() === 'na') {
          formParams[fpIndex].value = "";
        }
        currencyVal = formParams[fpIndex].value;
      }
      // format pmin and pmax based on currency value
      if (formParams[fpIndex].name === 'pmin' || formParams[fpIndex].name === 'pmax') {
        if (currencyVal === '') {
          formParams[fpIndex].value = '';
        } else {
          formParams[fpIndex].value = Hasjob.PaySlider.toNumeric(formParams[fpIndex].value);
        }
      }
      // remove empty values
      if (formParams[fpIndex].value !== '') {
        sortedFilterParams.push(formParams[fpIndex]);
      }
    }
    return sortedFilterParams;
  },
  refresh: function() {
    this.ractive.set({
      jobLocations: window.Hasjob.Config.jobLocationFilters,
      jobTypes: window.Hasjob.Config.jobTypeFilters,
      jobCategories: window.Hasjob.Config.jobCategoryFilters,
      selectedLocations: window.Hasjob.Config.selectedLocations,
      selectedTypes: window.Hasjob.Config.selectedTypes,
      selectedCategories: window.Hasjob.Config.selectedCategories,
      selectedQuery: window.Hasjob.Config.selectedQuery,
      selectedEquity: window.Hasjob.Config.equity
    }).then(function() {
      $('#job-filters-location').multiselect('rebuild');
      $('#job-filters-type').multiselect('rebuild');
      $('#job-filters-category').multiselect('rebuild');
    });
  }
};

window.Hasjob.PaySlider = function(options){
  this.selector = options.selector;
  this.slider = null;
  this.start = options.start,
  this.end = options.end;
  this.minField = options.minField;
  this.maxField = options.maxField;
  this.init();
};

window.Hasjob.Currency = {};

window.Hasjob.Currency.indian_rupee_encoder = function(value) {
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

window.Hasjob.Currency.prefix = function(currency){
  var currencyMap = {
    'default': '¤',
    'inr': '₹',
    'usd': '$',
    'sgd': 'S$',
    'aud': 'A$',
    'eur': '€',
    'gbp': '£'
  };
  if (currency === undefined || currency.toLowerCase() == 'na') {
    return currencyMap['default'];
  } else {
    return currencyMap[currency.toLowerCase()];
  }
};

window.Hasjob.Currency.isRupee = function(currency) {
  return currency.toLowerCase() === 'inr';
};

window.Hasjob.Currency.wNumbFormat = function(currency) {
  var prefix = '¤',
      thousand = ',',
      encoder = null,
      format = null;

  if (currency && window.Hasjob.Currency.isRupee(currency)) {
    encoder = Hasjob.Currency.indian_rupee_encoder;
  }

  prefix = Hasjob.Currency.prefix(currency);

  if (encoder === null) {
    format = window.wNumb({
      decimals: 0,
      thousand: thousand,
      prefix: prefix,
    });
  } else {
    format = window.wNumb({
      decimals: 0,
      thousand: thousand,
      prefix: prefix,
      edit: encoder
    });
  }
  return format;
};

window.Hasjob.Currency.formatTo = function(currency, value) {
  return window.Hasjob.Currency.wNumbFormat(currency).to(value);
};

window.Hasjob.Currency.formatFrom = function(currency, value) {
  return window.Hasjob.Currency.wNumbFormat(currency).from(value);
};

window.Hasjob.PaySlider.toNumeric = function(str){
  return str.slice(1).replace(/,/g, '');
};

window.Hasjob.PaySlider.prototype.init = function(){
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
    format: window.wNumb({
      decimals: 0,
      thousand: ',',
      prefix: '¤'
    })
  });
  this.slider.Link('lower').to($(this.minField));
  this.slider.Link('upper').to($(this.maxField));
  return this;
};

window.Hasjob.PaySlider.prototype.resetSlider = function(currency) {
  var start = Hasjob.PaySlider.toNumeric(this.slider.val()[0]),
      end = Hasjob.PaySlider.toNumeric(this.slider.val()[1]);

  this.slider.noUiSlider({
    start: [start, end],
    format: Hasjob.Currency.wNumbFormat(currency)
  }, true);

  this.slider.Link('lower').to($(this.minField));
  this.slider.Link('upper').to($(this.maxField));
};


$(function() {
  Ractive.DEBUG = false;

  $(window).on("popstate", function (event) {
    if (event.originalEvent.state && event.originalEvent.state.reloadOnPop) {
      location.reload(true);
    } else {
      return false;
    }
  });

  window.Hasjob.Filters.init();

  var scrollheight = $('#hgnav').height() - $('#hg-sitenav').height();
  $(window).scroll(function() {
    if($(window).width() > 767 && window.Hasjob.Filters.filterDropdownClosed) {
      if ($(this).scrollTop() > scrollheight) {
        $('.header-section').slideUp();
      }
      else{
        $('.header-section').slideDown();
      }
    }
  });

  window.Hasjob.JobPost.handleGroupClick();
  $('.pstar').off().click(window.Hasjob.JobPost.handleStarClick);

  var getCurrencyVal = function() {
    return $("input[type='radio'][name='currency']:checked").val();
  };

  var setPayTextField = function(){
    var currencyLabel = 'Pay';
    var equityLabel = '';
    var payFieldLabel;

    if ($('#job-filters-equity').is(':checked')) {
      equityLabel += ' + ' + '%';
    }
    if (getCurrencyVal().toLowerCase() === 'na'){
      currencyLabel = 'Pay';
    } else {
      currencyLabel = $('#job-filters-pmin').val() + ' - ' + $('#job-filters-pmax').val();
    }
    if (currencyLabel === 'Pay' && equityLabel !== '') {
      payFieldLabel = 'Equity (%)';
    } else {
      payFieldLabel = currencyLabel + equityLabel;
    }
    $('#job-filters-pay-text').html(payFieldLabel);
  };

  $('#job-filters-equity').on('change', function(){
    setPayTextField();
  });

  // set initial value for the currency radio button
  var presetCurrency = (Hasjob.PayFilterParameters && Hasjob.PayFilterParameters.currency) || 'NA';
  $.each($("input[type='radio'][name='currency']"), function(index, currencyRadio){
    if ($(currencyRadio).val() === presetCurrency) {
      $(currencyRadio).attr('checked', 'checked');
    }
  });

  $("input[type='radio'][name='currency']").on('change',function(){
    setPaySliderVisibility();
    paySlider.resetSlider(getCurrencyVal());
    setPayTextField();
  });

  // prevent the pay filter dropdown from hiding on click
  $('ul.pay-filter-dropdown').click(function(e) {
    e.stopPropagation();
  });

  var setPaySliderVisibility = function(){
    if (getCurrencyVal().toLowerCase() === 'na') {
      $('.pay-filter-slider').slideUp();
    } else {
      $('.pay-filter-slider').slideDown();
    }
  };

  var paySlider = new Hasjob.PaySlider({
    start: (Hasjob.PayFilterParameters && Hasjob.PayFilterParameters.pmin) || 0,
    end: (Hasjob.PayFilterParameters && Hasjob.PayFilterParameters.pmax) || 10000000,
    selector: '#pay-slider',
    minField: '#job-filters-pmin',
    maxField: '#job-filters-pmax'
  });

  $('#pay-slider').on('slide', function(){
    setPayTextField();
  });

  $('#pay-slider').on('change', function(){
    window.Hasjob.StickieList.refresh();
  });

  setPaySliderVisibility();
  paySlider.resetSlider(getCurrencyVal());
  setPayTextField();
});
