//window.Hasjob initialized in layout.html

Hasjob.Util = {
  updateGA: function() {
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
  },
  createCustomEvent: function(eventName) {
    // Raise a custom event
    if (typeof(window.Event) === "function") {
      var customEvent = new Event(eventName);
    } else {
      // 'Event' constructor is not supported by IE
      var customEvent = document.createEvent('Event');
      customEvent.initEvent(eventName, true, true);
    }
    return customEvent;
  }
};

window.Hasjob.JobPost = {
  handleStarClick: function () {
    $('#main-content').on('click', '.pstar', function(e) {
      var starlink = $(this).find('i');
      var csrf_token = $('meta[name="csrf-token"]').attr('content');
      starlink.addClass('fa-spin');
      $.ajax('/star/' + starlink.data('id'), {
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
      return false;
    });
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
    });
  }
};

window.Hasjob.StickieList = {
  init: function(){
    window.dispatchEvent(Hasjob.Util.createCustomEvent('onStickiesInit'));
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
          method: 'POST',
          success: function(data) {
            $('ul#stickie-area').append(data.trim());
            stickielist.loadmoreRactive.set('loading', false);
            stickielist.loadmoreRactive.set('error', false);
            window.dispatchEvent(Hasjob.Util.createCustomEvent('onStickiesPagination'));
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
      searchUrl = window.Hasjob.Config.baseURL + '?' + window.Hasjob.Filters.toParam();
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
        window.dispatchEvent(Hasjob.Util.createCustomEvent('onStickiesRefresh'));
      }
    });
    history.replaceState({reloadOnPop: true}, '', window.location.href);
    history.pushState({reloadOnPop: true}, '', searchUrl);
    window.Hasjob.Util.updateGA();
  },
    /*
    Creates a linear colour gradient with canvas of width equal to maxValue. The canvas indicates a scale  from 0 to maxValue.
    Takes
     'funnelName' - conversion funnel's name.
     'maxValue' -  max value of conversion funnel across job posts of last 30 days
  */
  createGradientColourScale: function(funnelName, maxValue) {
    var canvas = document.createElement("canvas");
    canvas.id = funnelName;
    canvas.width = maxValue;
    canvas.height = 10;

    var context = canvas.getContext('2d');
    context.rect(0, 0, canvas.width, canvas.height);
    var grd = context.createLinearGradient(0, 0, canvas.width, canvas.height);

    grd.addColorStop(1, '#DF3499');
    grd.addColorStop(0.7, '#E05F26');
    grd.addColorStop(0.5, '#DF5C2A');
    grd.addColorStop(0.1, '#F1D564');
    grd.addColorStop(0, '#FFFFA2');

    context.fillStyle = grd;
    context.fill();
    //Store the canvas context and end colour of the conversion funnel, later to be used by window.Hasjob.Util.setFunnelColour for picking the colour for a conversion funnel value for a job post.
    window.Hasjob.Config[funnelName] = {};
    window.Hasjob.Config[funnelName].canvasContext = context;
    window.Hasjob.Config[funnelName].maxColour = '#DF3499';
  },
  /*
    Picks the colour for the value from the colour gradient canvas based on a scale of 0 to maxValue.
    Takes 'funnelName', value, elementId'
    'funnelName' - conversion funnel's name.
    'value' - conversion funnel value for the job post
    'elementId' - id attribute of the element of which background colour is to be set
  */
  setGradientColour: function(funnelName, value, elementId) {
    //rgba - RGBA values at a particular point in the canvas.
    var rgba = window.Hasjob.Config[funnelName].canvasContext.getImageData(value, 1, 1, 1).data;
    if (rgba[0] > 255 || rgba[1] > 255 || rgba[2] > 255) {
      // rgb value is invalid, hence return white
      colourHex ="#FFFFFF";
    } else if (rgba[0] == 0 && rgba[1] == 0 && rgba[2] == 0) {
      // value greater than maxValue hence return the last colour of the gradient
      colourHex = window.Hasjob.Config[funnelName].maxColour;
    } else {
      // Get the colour code in hex from RGB values returned by getImageData
      colourHex = "#" + (("000000" + (rgba[0] << 16) | (rgba[1] << 8) | rgba[2]).toString(16)).slice(-6);
    }
    // Set the background colour of the element
    var element = document.getElementById(elementId);
    element.classList.add("funnel-color-set");
    element.style.backgroundColor = colourHex;
  },
  renderGradientColour: function() {
    $('.js-funnel').each(function() {
      if(!$(this).hasClass("funnel-color-set")) {
        Hasjob.StickieList.setGradientColour($(this).data('funnel-name'), $(this).data('funnel-value'), $(this).attr('id'));
      }
    });
  },
  createGradientColour: function() {
    Hasjob.StickieList.createGradientColourScale('impressions', Hasjob.Config.MaxFunnelStat.max_impressions);
    Hasjob.StickieList.createGradientColourScale('views', Hasjob.Config.MaxFunnelStat.max_views);
    Hasjob.StickieList.createGradientColourScale('opens', Hasjob.Config.MaxFunnelStat.max_opens);
    Hasjob.StickieList.createGradientColourScale('applied', Hasjob.Config.MaxFunnelStat.max_applied);
  },
  funnelStatInit: function() {
    window.addEventListener('onStickiesInit', function (e) {
      if (window.Hasjob.Config.MaxFunnelStat) {
        Hasjob.StickieList.createGradientColour();
        Hasjob.StickieList.renderGradientColour();
      }
    }, false);

    window.addEventListener('onStickiesRefresh', function (e) {
      if (window.Hasjob.Config.MaxFunnelStat) {
        Hasjob.StickieList.renderGradientColour();
      }
    }, false);

    window.addEventListener('onStickiesPagination', function (e) {
      if (window.Hasjob.Config.MaxFunnelStat) {
        Hasjob.StickieList.renderGradientColour();
      }
    }, false);
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
  getCurrentState: function(){
    if (!Object.keys(window.Hasjob.Config.selectedFilters).length) {
      window.Hasjob.Config.selectedFilters = {
        selectedLocations: [],
        selectedTypes: [],
        selectedCategories: [],
        selectedQuery: '',
        selectedCurrency: '',
        pay: 0,
        equity: ''
      };
    }
    return {
      jobLocations: window.Hasjob.Config.allFilters.job_location_filters,
      jobTypes: window.Hasjob.Config.allFilters.job_type_filters,
      jobCategories: window.Hasjob.Config.allFilters.job_category_filters,
      jobsArchive: window.Hasjob.Config.selectedFilters.archive,
      selectedLocations: window.Hasjob.Config.selectedFilters.location_names,
      selectedTypes: window.Hasjob.Config.selectedFilters.types,
      selectedCategories: window.Hasjob.Config.selectedFilters.categories,
      selectedQuery: window.Hasjob.Config.selectedFilters.query_string,
      selectedCurrency: window.Hasjob.Config.selectedFilters.currency,
      pay: window.Hasjob.Config.selectedFilters.pay,
      equity: window.Hasjob.Config.selectedFilters.equity,
      isMobile: $(window).width() < 768
    };
  },
  init: function(){
    var filters = this;
    var keywordTimeout;
    var isFilterDropdownClosed = true;
    var filterMenuHeight = $('#hgnav').height() - $('#hg-sitenav').height();
    var pageScrollTimerId;

    filters.dropdownMenu = new Ractive({
      el: 'job-filters-ractive-template',
      template: '#filters-ractive',
      data: this.getCurrentState(),
      openOnMobile: function(event) {
        event.original.preventDefault();
        filters.dropdownMenu.set('show', true);
      },
      closeOnMobile: function(event) {
        if(event) {
          event.original.preventDefault();
        }
        filters.dropdownMenu.set('show', false);
      },
      complete: function() {
        $(window).resize(function() {
          if ($(window).width() < 768) {
            filters.dropdownMenu.set('isMobile', true);
          }
          else {
            filters.dropdownMenu.set('isMobile', false);
          }
        });

        //Close the dropdown menu when user clicks outside the menu
        $(document).on("click", function(event) {
          if ($("#js-job-filters") !== event.target && !$(event.target).parents('#filter-dropdown').length){
            filters.dropdownMenu.closeOnMobile();
          }
        });
      }
    });

    var pageScrollTimer = function() {
      return setInterval(function() {
        if (isFilterDropdownClosed) {
          if ($(window).scrollTop() > filterMenuHeight) {
            $('#hg-sitenav').slideUp();
          }
          else {
            $('#hg-sitenav').slideDown();
          }
        }
      }, 250);
    };

    //Initial pageScrollTimer being set.
    if ($(window).width() > 767) {
      pageScrollTimerId = pageScrollTimer();
    }

    $(window).resize(function() {
      if ($(window).width() < 768) {
        // Incase filters menu has been slided up on page scroll
        $('#hg-sitenav').show();
        if(pageScrollTimerId) {
          clearInterval(pageScrollTimerId);
          //pageScrollTimerId is set to 0 to indicate the timer has been stopped
          pageScrollTimerId = 0;
        }
      }
      else {
        filterMenuHeight = $('#hgnav').height() - $('#hg-sitenav').height();
        if(!pageScrollTimerId) {
          pageScrollTimerId = pageScrollTimer();
        }
      }
    });

    //remove white spaces keyword input value
    $('#job-filters-keywords').on('change',function(){
      $(this).val($(this).val().trim());
    });

    $('.js-handle-filter-change').on('change', function(e){
      window.Hasjob.StickieList.refresh();
    });

    var lastKeyword = '';
    $('.js-handle-keyword-update').on('keyup', function(){
      if ($(this).val() !== lastKeyword){
        window.clearTimeout(keywordTimeout);
        lastKeyword = $(this).val();
        keywordTimeout = window.setTimeout(window.Hasjob.StickieList.refresh, 1000);
      }
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
        isFilterDropdownClosed = false;
      },
      onDropdownHide: function(event, ui) {
        isFilterDropdownClosed = true;
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
        isFilterDropdownClosed = false;
      },
      onDropdownHide: function(event, ui) {
        isFilterDropdownClosed = true;
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
        isFilterDropdownClosed = false;
      },
      onDropdownHide: function(event, ui) {
        isFilterDropdownClosed = true;
      }
    });

    $('#job-filters-pay').on('shown.bs.dropdown', function() {
      // stop header filter rollup when dropdown is open
      isFilterDropdownClosed = false;
    });

    $('#job-filters-pay').on('hidden.bs.dropdown', function() {
      isFilterDropdownClosed = true;
    });

    //On pressing ESC, close the filters menu
    $(document).keydown(function(event) {
      if (event.keyCode === 27) {
        event.preventDefault();
        filters.dropdownMenu.closeOnMobile();
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
      // format pay based on currency value
      if (formParams[fpIndex].name === 'pay') {
        if (currencyVal === '') {
          formParams[fpIndex].value = '';
        } else {
          formParams[fpIndex].value = Hasjob.PaySlider.toNumeric(formParams[fpIndex].value);
          if (formParams[fpIndex].value === '0') {
            formParams[fpIndex].value = '';
          }
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
    // Capture initial cursor position in the keywords field
    var keywordsField = document.getElementById('job-filters-keywords');
    var initialKeywordPos = keywordsField.selectionEnd;

    // reset pre-selected values in filters
    this.dropdownMenu.set(this.getCurrentState()).then(function() {
      // Since the data may have changed, multiselect requires a rebuild
      $('#job-filters-location').multiselect('rebuild');
      $('#job-filters-type').multiselect('rebuild');
      $('#job-filters-category').multiselect('rebuild');

      // Set the cursor back to where it was before refresh
      keywordsField.selectionEnd = initialKeywordPos;
      $("html, body").animate({ scrollTop: 0 }, "slow");
    });
  }
};

window.Hasjob.PaySlider = function(options){
  this.selector = options.selector;
  this.slider = null;
  this.start = options.start;
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

window.Hasjob.PaySlider.range = function(currency){
  if (currency === 'INR') {
    return {
      'min': [0, 5000],
      '15%': [100000, 10000],
      '30%': [200000, 50000],
      '70%': [2000000, 100000],
      '85%': [10000000, 1000000],
      'max': [100000000]
    }
  } else {
    return {
      'min': [0, 5000],
      '2%': [200000, 50000],
      '10%': [1000000, 100000],
      'max': [10000000, 100000]
    }
  }
};

window.Hasjob.PaySlider.prototype.init = function(){
  this.slider = $(this.selector).noUiSlider({
    start: this.start,
    connect: (this.start.constructor === Array)?true:false,
    behaviour: 'tap',
    range: {
      'min': [0, 50000],
      '10%':  [1000000, 100000],
      'max': [10000000, 100000]
    },
    format: window.wNumb({
      decimals: 0,
      thousand: ',',
      prefix: '¤'
    })
  });
  this.slider.Link('lower').to($(this.minField));
  if (typeof this.maxField !== 'undefined') {
    this.slider.Link('upper').to($(this.maxField));
  };
  return this;
};

window.Hasjob.PaySlider.prototype.resetSlider = function(currency) {
  var startval = this.slider.val(), start;
  if (startval.constructor === Array) {
    start = [Hasjob.PaySlider.toNumeric(startval[0]), Hasjob.PaySlider.toNumeric(startval[1])];
  } else {
    start = Hasjob.PaySlider.toNumeric(startval);
  };

  this.slider.noUiSlider({
    start: start,
    connect: (start.constructor === Array)?true:false,
    range: Hasjob.PaySlider.range(currency),
    format: Hasjob.Currency.wNumbFormat(currency)
  }, true);

  this.slider.Link('lower').to($(this.minField));
  if (typeof this.maxField !== 'undefined') {
    this.slider.Link('upper').to($(this.maxField));
  };
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
  window.Hasjob.JobPost.handleStarClick();
  window.Hasjob.JobPost.handleGroupClick();
  window.Hasjob.StickieList.funnelStatInit();

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
      var payVal = Hasjob.PaySlider.toNumeric($('#job-filters-payval').val());
      if (payVal === '0') {
        currencyLabel = 'Pay ' + getCurrencyVal();
      } else {
        currencyLabel = $('#job-filters-payval').val() + ' per year';
      };
    }
    if (currencyLabel === 'Pay' && equityLabel !== '') {
      payFieldLabel = 'Equity (%)';
    } else {
      payFieldLabel = currencyLabel + equityLabel;
    }
    $('#job-filters-pay-text').html(payFieldLabel);
  };

  $('#job-filters-equity').on('change', function() {
    setPayTextField();
  });

  // set initial value for the currency radio button
  var presetCurrency = (window.Hasjob.Config && window.Hasjob.Config.selectedFilters.currency) || 'NA';
  $.each($("input[type='radio'][name='currency']"), function(index, currencyRadio){
    if ($(currencyRadio).val() === presetCurrency) {
      $(currencyRadio).attr('checked', 'checked');
    }
  });

  // preset equity
  if (window.Hasjob.Config && window.Hasjob.Config.selectedFilters.equity) {
    $("input[type='checkbox'][name='equity']").attr('checked', 'checked');
  }

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
    start: (window.Hasjob.Config && window.Hasjob.Config.selectedFilters.pay) || 0,
    selector: '#pay-slider',
    minField: '#job-filters-payval'
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
