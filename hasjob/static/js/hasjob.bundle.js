webpackJsonp([0],[
/* 0 */
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [
	    __webpack_require__(1),
	    __webpack_require__(2),
	    __webpack_require__(3),
	    __webpack_require__(5)
	  ], __WEBPACK_AMD_DEFINE_RESULT__ = function (React, ReactDOM, $, Hasjob) {
	    ReactDOM.render(React.createElement(Hasjob, null), document.getElementById('main-content')); //root
	  }.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__))


/***/ },
/* 1 */,
/* 2 */,
/* 3 */,
/* 4 */,
/* 5 */
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [
	    __webpack_require__(1),
	    __webpack_require__(2),
	    __webpack_require__(6),
	    __webpack_require__(7),
	    __webpack_require__(8),
	    __webpack_require__(3),
	    __webpack_require__(9),

	  ], __WEBPACK_AMD_DEFINE_RESULT__ = function (React, ReactDOM, JobSnippet, HeaderBar, commonFunctions, $) {

	    var Hasjob = React.createClass({displayName: "Hasjob",
	      getInitialState: function () {
	        return {
	          jobsList: [],
	          lastDate: '',
	        }
	      },

	      loadMorePosts: function () {

	        var postData = {},

	          successCallback = function (data) {

	            var posts = data.grouped,
	              monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

	            for(var i = 0; i < posts.length; i++) { //To convert dates into a readable format
	              for(var j = 0; j < posts[i].posts.length; j++) {
	                posts[i].posts[j].date = new Date(posts[i].posts[j].date);
	                posts[i].posts[j].date = monthNames[posts[i].posts[j].date.getMonth()] + " " + posts[i].posts[j].date.getDate();
	              }
	            }

	            this.setState({
	              jobsList: posts,
	              lastDate: data.loadmore
	            });

	          }.bind(this);

	        commonFunctions.makeAjaxPost('/', postData, successCallback);
	      },

	      componentDidMount: function () {
	        var that = this;
	        that.loadMorePosts();

	        $("#loadmore").appear().on('appear', function (event, element) {
	          that.loadMorePosts();
	        });
	      },

	      render: function () {

	        var jobSnippets = this.state.jobsList.map(function (jobDetails, iterator) {
	          return React.createElement(JobSnippet, {options: jobDetails, key: "snippet"+iterator})
	        });

	        return(
	          React.createElement("div", null, 
	            React.createElement("ul", {className: "row", id: "stickie-area"}, 
	              jobSnippets
	            ), 

	            React.createElement("form", {id: "loadmore", method: "GET", dataAppearTopffOset: "600"}, 
	              React.createElement("button", {className: "btn btn-default btn-lg", type: "submit", name: "startdate"}, 
	                "Load more…"
	              )
	            )
	          )
	        )
	      }

	    });

	    return Hasjob
	  }.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));


/***/ },
/* 6 */
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [
	    __webpack_require__(1),
	    __webpack_require__(2),
	    __webpack_require__(3),
	  ], __WEBPACK_AMD_DEFINE_RESULT__ = function (React, ReactDOM, $) {

	    var JobSnippet = React.createClass({displayName: "JobSnippet",

	      render: function () {
	        var style = {
	            marginBottom: '30px',
	            verticalAlign: 'top'
	          },
	          options = this.props.options,
	          noOfPosts = options.posts.length;

	        if(noOfPosts === 1) {
	          var post = options.posts[0];
	          return(
	            React.createElement("li", {className: "col-xs-12 col-md-3 col-sm-4", style: style}, 

	              React.createElement("a", {className: "stickie", href: options.url, rel: "bookmark"}, 
	                React.createElement("span", {className: "annotation top-left"}, post.location), 
	                React.createElement("span", {className: "annotation top-right"}, 
	                  post.date
	                ), 
	                React.createElement("span", {className: "headline"}, post.headline), 
	                React.createElement("span", {className: "count"}, 
	                  React.createElement("span", {title: "Listed › Viewed › Opened form › Applied"}, 
	                    post.viewcounts.listed+" > "+post.viewcounts.viewed+" > "+post.viewcounts.opened+" > "+post.viewcounts.applied
	                  ), " . ", post.pay), 
	                React.createElement("span", {className: "annotation bottom-right"}, post.company_name), 
	                React.createElement("span", {className: "annotation bottom-left"}, 
	                              
	                  React.createElement("i", {className: "fa fa-star-o pstar", "data-id": "kued5"})
	                )
	              )
	            )
	          )
	        } else if(noOfPosts > 1) {
	          var nestedPosts = [];

	          for(var i = 1; i < noOfPosts; i++) {

	            nestedPosts.push(
	              React.createElement("div", {className: "stickie grouped under", "data-href": options.posts[i].url, key:  "snippet"+i}, 
	                React.createElement("span", {className: "annotation top-left"}, options.posts[i].location), 
	                React.createElement("span", {className: "annotation top-right"}, 
	                  options.posts[i].date
	                ), 
	                React.createElement("span", {className: "headline"}, options.posts[i].headline), 
	                React.createElement("span", {className: "count"}, 
	                  React.createElement("span", {title: "Listed › Viewed › Opened form › Applied"}, 
	                    options.posts[i].viewcounts.listed+" > "+options.posts[i].viewcounts.viewed+" > "+options.posts[i].viewcounts.opened+" > "+options.posts[i].viewcounts.applied
	                  ), " · ", options.posts[i].pay
	                ), 

	                React.createElement("span", {className: "annotation bottom-right"}, 
	                  options.posts[i].company_name
	                ), 

	                React.createElement("span", {className: "annotation bottom-left"}
	                /*<i className="fa fa-star-o pstar" data-id="kvkl8"></i*/
	                )
	              )
	            )
	          }

	          return(
	            React.createElement("li", {className: "grouped col-xs-12 col-md-3 col-sm-4", style: style}, 

	              React.createElement("a", {className: "stickie", href: options.posts[0].url, rel: "bookmark"}, 
	                React.createElement("span", {className: "annotation top-left"}, options.posts[0].location), 
	                React.createElement("span", {className: "annotation top-right"}, options.posts[0].date), 
	                React.createElement("span", {className: "headline"}, options.posts[0].headline), 
	                React.createElement("span", {className: "count"}, 
	                  React.createElement("span", {title: "Listed › Viewed › Opened form › Applied"}, 
	                    options.posts[0].viewcounts.listed+" > "+options.posts[0].viewcounts.viewed+" > "+options.posts[0].viewcounts.opened+" > "+options.posts[0].viewcounts.applied
	                  ), " . ", options.posts[0].pay
	                ), 
	                React.createElement("span", {className: "annotation bottom-right"}, options.posts[0].company_name), 
	                React.createElement("span", {className: "annotation bottom-left"}, 
	                  React.createElement("i", {className: "fa fa-star-o pstar", "data-id": "kued5"})
	                )
	              ), 
	              nestedPosts
	            )
	          )
	        }
	      }
	    });

	    return JobSnippet
	  }.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__))


/***/ },
/* 7 */
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [
	    __webpack_require__(1),
	    __webpack_require__(3),
	  ], __WEBPACK_AMD_DEFINE_RESULT__ = function (React, $) {
	    var HeaderBar = React.createClass({displayName: "HeaderBar",
	      componentDidMount: function () {
	        console.log('headerbar rendered');
	      },
	      render: function () {
	        var style1 = {
	            display: "block"
	          },
	          style2 = {
	            width: "100%",
	            overflow: "hidden",
	            textOverflow: "ellipsis"
	          },
	          style3 = {
	            width: "100%"
	          },
	          style4 = {
	            left: "0%"
	          },
	          style5 = {
	            left: "100%"
	          };

	        return(
	          React.createElement("header", null, 

	            React.createElement("nav", {className: "navbar navbar-default navbar-fixed-top", id: "hgnav", role: "navigation"}, 
	              React.createElement("div", {className: "container"}, 
	                React.createElement("div", {className: "navbar-header pull-left hg-header-app-nav"}, 

	                  React.createElement("div", {className: "page-header"}, 
	                    React.createElement("h1", null, React.createElement("a", {href: "https://hasjob.co"}, "Hasjob ", React.createElement("small", {className: "board-caption"}, "The HasGeek Job Board")))
	                  )

	                ), 
	                React.createElement("div", {className: "navbar-header pull-right hg-header-nav"}, 
	                  React.createElement("ul", {className: "nav pull-right"}, 
	                    React.createElement("li", {className: "dropdown pull-left"}, 

	                      React.createElement("button", {type: "button", "data-toggle": "dropdown", className: "dropdown-toggle", id: "hg-user-btn"}, 
	                        React.createElement("i", {className: "fa fa-user"})
	                      ), 
	                      React.createElement("ul", {className: "dropdown-menu pull-right"}, 
	                        React.createElement("li", null, 

	                          React.createElement("a", {href: "https://auth.hasgeek.com/profile", title: "Ashwin Hariharan (~ashwin01)"}, "Ashwin Hariharan")

	                        ), 
	                        React.createElement("li", null, React.createElement("a", {href: "https://hasjob.co/logout"}, "Logout"))
	                      )
	                    ), 

	                    React.createElement("li", {className: "dropdown pull-left"}, 
	                      React.createElement("button", {type: "button", "data-toggle": "collapse", "data-target": ".navbar-collapse", className: "menu-toggle hg-site-nav-toggle"}, 
	                        React.createElement("i", {className: "fa fa-search"})
	                      )
	                    ), 

	                    React.createElement("li", {className: "dropdown pull-right hg-nw-bar"}, 

	                      React.createElement("button", {type: "button", className: "dropdown-toggle", "data-toggle": "dropdown", role: "button", "aria-expanded": "false", id: "hg-app-drawer"}, 
	                        React.createElement("i", {className: "fa fa-th"})
	                      ), 
	                      React.createElement("ul", {className: "dropdown-menu block-dropdown", role: "menu"}, 
	                        React.createElement("li", null, 
	                          React.createElement("a", {href: "http://hasgeek.com/"}, 
	                            React.createElement("img", {src: "/static/img/hg-banner.png", alt: "..."}), 
	                            React.createElement("h6", null, "HasGeek")
	                          )
	                        ), 
	                        React.createElement("li", null, 
	                          React.createElement("a", {href: "https://talkfunnel.com/"}, 
	                            React.createElement("img", {src: "/static/img/hg_funnel.png", alt: "..."}), 
	                            React.createElement("h6", null, "Talkfunnel")
	                          )
	                        ), 
	                        React.createElement("li", null, 
	                          React.createElement("a", {href: "/static/img/Hasjob.html"}, 
	                            React.createElement("img", {src: "/static/img/logo-star.png", alt: "..."}), 
	                            React.createElement("h6", null, "Hasjob")
	                          )
	                        ), 
	                        React.createElement("li", null, 
	                          React.createElement("a", {href: "https://hasgeek.tv/"}, 
	                            React.createElement("img", {src: "/static/img/hg_hgtv.png", alt: "..."}), 
	                            React.createElement("h6", null, "HGTV")
	                          )
	                        )
	                      )

	                    )
	                  )
	                ), 

	                React.createElement("div", {className: "nav collapse navbar-collapse navbar-right hg-site-nav", id: "hg-sitenav"}, 

	                  React.createElement("div", {className: "header-section", id: "filter-dropdown", style: style1}, 
	                    React.createElement("form", {id: "job-filters", action: "https://hasjob.co/search", role: "form"}, 
	                      React.createElement("div", {className: "row"}, 
	                        React.createElement("div", {className: "filters filters-col1 location-filter col-xs-12 col-sm-4 col-md-3"}, 
	                          React.createElement("select", {id: "job-filters-location", name: "l", multiple: "multiple", className: "job-filters-select2 notselect hidden", placeholder: "Location", style: style1}, 
	                            React.createElement("option", {value: "anywhere", id: "job-filters-remote-check"}, "Anywhere/Remote"), 
	                            React.createElement("option", {value: "bangalore"}, "Bangalore, IN"), 
	                            React.createElement("option", {value: "mumbai"}, "Mumbai, IN"), 
	                            React.createElement("option", {value: "delhi"}, "Delhi, IN"), 
	                            React.createElement("option", {value: "chennai"}, "Chennai, IN"), 
	                            React.createElement("option", {value: "hyderabad"}, "Hyderabad, IN"), 
	                            React.createElement("option", {value: "pune"}, "Pune, IN"), 
	                            React.createElement("option", {value: "gurgaon"}, "Gurgaon, IN"), 
	                            React.createElement("option", {value: "noida"}, "Noida, IN"), 
	                            React.createElement("option", {value: "ahmedabad"}, "Ahmedabad, IN"), 
	                            React.createElement("option", {value: "goa"}, "Goa, IN (state)"), 
	                            React.createElement("option", {value: "jaipur"}, "Jaipur, IN"), 
	                            React.createElement("option", {value: "anderson2"}, "Anderson, SC, US"), 
	                            React.createElement("option", {value: "kolkata"}, "Kolkata, IN"), 
	                            React.createElement("option", {value: "jalandhar"}, "Jalandhar, IN"), 
	                            React.createElement("option", {value: "india"}, "India (country)"), 
	                            React.createElement("option", {value: "mysore"}, "Mysore, IN"), 
	                            React.createElement("option", {value: "west-region"}, "West Region, CM (state)"), 
	                            React.createElement("option", {value: "thiruvananthapuram"}, "Thiruvananthapuram, IN"), 
	                            React.createElement("option", {value: "coimbatore"}, "Coimbatore, IN"), 
	                            React.createElement("option", {value: "purwanchal"}, "Purwanchal, NP (state)"), 
	                            React.createElement("option", {value: "san-francisco2"}, "San Francisco, CA, US"), 
	                            React.createElement("option", {value: "berlin"}, "Berlin, DE"), 
	                            React.createElement("option", {value: "chandigarh2"}, "Chandigarh, IN"), 
	                            React.createElement("option", {value: "sudurland"}, "Sudurland, IS (state)"), 
	                            React.createElement("option", {value: "panaji"}, "Panaji, IN"), 
	                            React.createElement("option", {value: "punjab"}, "Punjab, IN (state)"), 
	                            React.createElement("option", {value: "mangalore"}, "Mangalore, IN"), 
	                            React.createElement("option", {value: "cochin"}, "Cochin, IN"), 
	                            React.createElement("option", {value: "tirupati"}, "Tirupati, IN"), 
	                            React.createElement("option", {value: "oman"}, "Oman (country)"), 
	                            React.createElement("option", {value: "ostan-e-mazandaran"}, "Ostan-e Mazandaran, IR (state)"), 
	                            React.createElement("option", {value: "shanghai"}, "Shanghai, CN"), 
	                            React.createElement("option", {value: "haora"}, "Haora, IN"), 
	                            React.createElement("option", {value: "udaipur3"}, "Udaipur, IN"), 
	                            React.createElement("option", {value: "london"}, "London, GB")
	                          ), 
	                          React.createElement("div", {className: "btn-group", style: style3}, 
	                            React.createElement("button", {type: "button", className: "multiselect dropdown-toggle btn btn-default", "data-toggle": "dropdown", title: "Location", style: style2}, React.createElement("span", {className: "multiselect-selected-text"}, "Location"), " ", React.createElement("b", {className: "caret"})), 
	                            React.createElement("ul", {className: "multiselect-container dropdown-menu"}, 
	                              React.createElement("li", {value: "0"}, 
	                                React.createElement("div", {className: "input-group input-group-sm"}, 
	                                  React.createElement("div", {className: "input-group-addon"}, React.createElement("i", {className: "fa fa-search"})), 
	                                  React.createElement("input", {type: "text", className: "form-control", id: "job-filter-location-search", placeholder: "Search"}), 
	                                  React.createElement("div", {className: "input-group-addon job-filter-location-search-clear"}, React.createElement("i", {className: "fa fa-times"}))
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "anywhere"}), " Anywhere/Remote")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "bangalore"}), " Bangalore, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "mumbai"}), " Mumbai, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "delhi"}), " Delhi, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "chennai"}), " Chennai, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "hyderabad"}), " Hyderabad, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "pune"}), " Pune, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "gurgaon"}), " Gurgaon, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "noida"}), " Noida, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "ahmedabad"}), " Ahmedabad, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "goa"}), " Goa, IN (state)")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "jaipur"}), " Jaipur, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "anderson2"}), " Anderson, SC, US")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "kolkata"}), " Kolkata, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "jalandhar"}), " Jalandhar, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "india"}), " India (country)")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "mysore"}), " Mysore, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "west-region"}), " West Region, CM (state)")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "thiruvananthapuram"}), " Thiruvananthapuram, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "coimbatore"}), " Coimbatore, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "purwanchal"}), " Purwanchal, NP (state)")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "san-francisco2"}), " San Francisco, CA, US")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "berlin"}), " Berlin, DE")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "chandigarh2"}), " Chandigarh, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "sudurland"}), " Sudurland, IS (state)")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "panaji"}), " Panaji, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "punjab"}), " Punjab, IN (state)")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "mangalore"}), " Mangalore, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "cochin"}), " Cochin, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "tirupati"}), " Tirupati, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "oman"}), " Oman (country)")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "ostan-e-mazandaran"}), " Ostan-e Mazandaran, IR (state)")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "shanghai"}), " Shanghai, CN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "haora"}), " Haora, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "udaipur3"}), " Udaipur, IN")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "london"}), " London, GB")
	                                )
	                              )
	                            )
	                          )
	                        ), 
	                        React.createElement("div", {className: "filters col-xs-12 col-sm-4 col-md-3"}, 
	                          React.createElement("select", {id: "job-filters-type", name: "t", multiple: "multiple", className: "job-filters-select2 notselect hidden", placeholder: "Job Type", style: style1}, 
	                            React.createElement("option", {value: "fulltime"}, "Full-time employment"), 
	                            React.createElement("option", {value: "contract"}, "Short-term contract"), 
	                            React.createElement("option", {value: "intern"}, "Internship"), 
	                            React.createElement("option", {value: "freelance"}, "Freelance or consulting"), 
	                            React.createElement("option", {value: "volunteer"}, "Volunteer contributor"), 
	                            React.createElement("option", {value: "partner"}, "Partner for a venture")
	                          ), 
	                          React.createElement("div", {className: "btn-group", style: style3}, 
	                            React.createElement("button", {type: "button", className: "multiselect dropdown-toggle btn btn-default", "data-toggle": "dropdown", title: "Job Type", style: style2}, React.createElement("span", {className: "multiselect-selected-text"}, "Job Type"), " ", React.createElement("b", {className: "caret"})), 
	                            React.createElement("ul", {className: "multiselect-container dropdown-menu"}, 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "fulltime"}), " Full-time employment")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "contract"}), " Short-term contract")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "intern"}), " Internship")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "freelance"}), " Freelance or consulting")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "volunteer"}), " Volunteer contributor")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "partner"}), " Partner for a venture")
	                                )
	                              )
	                            )
	                          )
	                        ), 
	                        React.createElement("div", {className: "filters col-xs-12 col-sm-4 col-md-3 category-filter"}, 
	                          React.createElement("select", {id: "job-filters-category", name: "c", multiple: "multiple", className: "job-filters-select2 notselect hidden", placeholder: "Job Category", style: style1}, 
	                            React.createElement("option", {value: "programming"}, "Programming"), 
	                            React.createElement("option", {value: "ux"}, "Interaction Design"), 
	                            React.createElement("option", {value: "design"}, "Graphic Design"), 
	                            React.createElement("option", {value: "electronics"}, "Electronics"), 
	                            React.createElement("option", {value: "testing"}, "Testing"), 
	                            React.createElement("option", {value: "sysadmin"}, "Systems Administration"), 
	                            React.createElement("option", {value: "business"}, "Business/Management"), 
	                            React.createElement("option", {value: "edit"}, "Writer/Editor"), 
	                            React.createElement("option", {value: "support"}, "Customer Support"), 
	                            React.createElement("option", {value: "mobile"}, "Mobile (iPhone, Android, other)"), 
	                            React.createElement("option", {value: "officeadmin"}, "Office Administration")
	                          ), 
	                          React.createElement("div", {className: "btn-group", style: style3}, 
	                            React.createElement("button", {type: "button", className: "multiselect dropdown-toggle btn btn-default", "data-toggle": "dropdown", title: "Job Category", style: style2}, React.createElement("span", {className: "multiselect-selected-text"}, "Job Category"), " ", React.createElement("b", {className: "caret"})), 
	                            React.createElement("ul", {className: "multiselect-container dropdown-menu"}, 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "programming"}), " Programming")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "ux"}), " Interaction Design")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "design"}), " Graphic Design")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "electronics"}), " Electronics")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "testing"}), " Testing")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "sysadmin"}), " Systems Administration")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "business"}), " Business/Management")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "edit"}), " Writer/Editor")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "support"}), " Customer Support")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "mobile"}), " Mobile (iPhone, Android, other)")
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("a", {tabindex: "0"}, 
	                                  React.createElement("label", {className: "checkbox"}, 
	                                    React.createElement("input", {type: "checkbox", value: "officeadmin"}), " Office Administration")
	                                )
	                              )
	                            )
	                          )
	                        ), 
	                        React.createElement("div", {className: "filters dropdown col-xs-12 col-sm-4 col-md-3"}, 
	                          React.createElement("div", {id: "job-filters-pay", className: "btn-group btn-block no-jshidden"}, 
	                            React.createElement("button", {type: "button", className: "btn btn-default dropdown-toggle btn-block", "data-toggle": "dropdown", "aria-expanded": "false"}, 
	                              React.createElement("span", {id: "job-filters-pay-text", className: "pay-field"}, "Pay"), 
	                              React.createElement("span", {className: "caret"})
	                            ), 
	                            React.createElement("ul", {className: "dropdown-menu pay-filter-dropdown", role: "menu", "aria-labelledby": "job-filters-pay"}, 
	                              React.createElement("li", {className: "clearfix"}, 
	                                React.createElement("div", {className: "currency-checkbox"}, 
	                                  React.createElement("input", {type: "radio", id: "job-filters-na", name: "currency", value: "NA", checked: "checked"}), 
	                                  React.createElement("label", {for: "job-filters-na"}, "Any")
	                                ), 
	                                React.createElement("div", {className: "currency-checkbox"}, 
	                                  React.createElement("input", {type: "radio", id: "job-filters-inr", name: "currency", value: "INR"}), 
	                                  React.createElement("label", {for: "job-filters-inr"}, "INR")
	                                ), 
	                                React.createElement("div", {className: "currency-checkbox"}, 
	                                  React.createElement("input", {type: "radio", id: "job-filters-usd", name: "currency", value: "USD"}), 
	                                  React.createElement("label", {for: "job-filters-usd"}, "USD")
	                                ), 
	                                React.createElement("div", {className: "currency-checkbox"}, 
	                                  React.createElement("input", {type: "radio", id: "job-filters-eur", name: "currency", value: "EUR"}), 
	                                  React.createElement("label", {for: "job-filters-eur"}, "EUR")
	                                )
	                              ), 
	                              React.createElement("li", {className: "pay-filter-slider", style: style1}, 
	                                React.createElement("div", null, 
	                                  React.createElement("input", {type: "hidden", name: "pmin", id: "job-filters-pmin", value: "¤0"}), 
	                                  React.createElement("input", {type: "hidden", name: "pmax", id: "job-filters-pmax", value: "¤10,000,000"}), 
	                                  React.createElement("div", {id: "pay-slider", className: "noUi-target noUi-ltr noUi-horizontal noUi-background"}, 
	                                    React.createElement("div", {className: "noUi-base"}, 
	                                      React.createElement("div", {className: "noUi-origin noUi-connect", style: style4}, 
	                                        React.createElement("div", {className: "noUi-handle noUi-handle-lower"})
	                                      ), 
	                                      React.createElement("div", {className: "noUi-origin noUi-background", style: style5}, 
	                                        React.createElement("div", {className: "noUi-handle noUi-handle-upper"})
	                                      )
	                                    )
	                                  )
	                                )
	                              ), 
	                              React.createElement("li", null, 
	                                React.createElement("label", {for: "job-filters-equity", className: "equity-label"}, 
	                                  React.createElement("input", {type: "checkbox", name: "equity", id: "job-filters-equity", value: "1"}), " Equity")
	                              )
	                            )
	                          )
	                        ), 
	                        React.createElement("div", {className: "filters col-xs-12 col-sm-4 col-md-3"}, 
	                          React.createElement("input", {id: "job-filters-keywords", className: "filter-select form-control", type: "text", placeholder: "Keywords", name: "q", value: ""})
	                        ), 
	                        React.createElement("div", {className: "submit-filters col-xs-4 col-sm-2 col-md-2"}, 
	                          React.createElement("button", {id: "job-filters-submit", type: "submit", className: "btn btn-default submit-btn"}, 
	                            React.createElement("span", null, React.createElement("i", {className: "fa fa-filter"}), "Filter")
	                          )
	                        ), 
	                        React.createElement("div", {className: "cancel-filters col-xs-4 visible-xs"}, 
	                          React.createElement("button", {id: "job-filters-cancel", className: "btn btn-default submit-btn"}, 
	                            React.createElement("span", null, React.createElement("i", {className: "fa fa-close"}), "Cancel")
	                          )
	                        )
	                      )
	                    )
	                  )

	                )

	              )
	            )

	          )
	        )
	      }
	    });

	    return HeaderBar;
	  }.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__))


/***/ },
/* 8 */
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [
	    exports,
	    __webpack_require__(3)
	  ], __WEBPACK_AMD_DEFINE_RESULT__ = function (exports, $) {
	    exports.makeAjaxGet = function (url, successCallback) {
	      $.ajax({
	        url: url,
	        type: 'GET',
	        data: postData,
	        success: successCallback,
	        error: function (httpRequest, status, error) {
	          console.log(error);
	        }
	      });
	    };

	    exports.makeAjaxPost = function (url, postData, successCallback) {
	      $.ajax({
	        url: url,
	        type: 'POST',
	        dataType: 'json',
	        //data: postData,
	        success: successCallback,
	        error: function (httpRequest, status, error) {
	          console.log(error);
	        }
	      });
	    };
	  }.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__))


/***/ }
]);