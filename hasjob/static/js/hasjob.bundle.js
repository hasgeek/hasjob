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
	    __webpack_require__(3),
	    __webpack_require__(8),

	  ], __WEBPACK_AMD_DEFINE_RESULT__ = function (React, ReactDOM, JobSnippet, commonFunctions, $) {

	    var Hasjob = React.createClass({displayName: "Hasjob",
	      getInitialState: function () {
	        return {
	          jobsList: [],
	          lastDate: '',
	        }
	      },
	      loadMorePosts: function () {
	        var postData = {};
	        var successCallback = function (data) {
	          var posts = data.grouped;
	          var monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
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
	      updateJobList: function(index){
	        var jobsList = JSON.parse(JSON.stringify(this.state.jobsList));
	        var flattenedJobs = [];
	        for(var i=0; i<jobsList[index].posts.length; i++){
	          flattenedJobs[i] = {
	            posts:[jobsList[index].posts[i]]
	          };
	        }
	        jobsList.splice(index, 1); //deletes the nested grouped jobs at the specified index
	        for(var i=0; i<flattenedJobs.length; i++){ //appends the jobs starting from that index
	          jobsList.splice(index+i, 0, flattenedJobs[i])
	        }
	        this.setState({
	          jobsList: jobsList
	        });
	      },
	      componentDidMount: function () {
	        var that = this;
	        that.loadMorePosts();
	        $("#loadmore").appear().on('appear', function (event, element) {
	          that.loadMorePosts();
	        });
	      },
	      render: function () {
	        var that = this;
	        var jobSnippets = this.state.jobsList.map(function (jobDetails, iterator) {
	          return React.createElement(JobSnippet, {options: jobDetails, key: "snippet"+iterator, index: iterator, updateJobList: that.updateJobList})
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
	    __webpack_require__(7)
	  ], __WEBPACK_AMD_DEFINE_RESULT__ = function (React, ReactDOM, $, commonFunctions) {

	    var JobSnippet = React.createClass({displayName: "JobSnippet",
	      starPost: function(event){
	        event.preventDefault();
	        var element = event.currentTarget;
	        var jobId = element.getAttribute('data-id');
	        var csrfToken = $("meta[name='csrf-token']").attr('content');
	        var postData = {
	          csrf_token: csrfToken
	        };
	        var successCallback = function(data){
	          element.className = element.className.replace(/fa-spin/g,'');
	          if(data.is_starred === true){
	            element.className = element.className.replace('fa-star-o','fa-star');
	          }else{
	            element.className = element.className.replace('fa-star','fa-star-o');
	          }
	        }
	        element.className += ' fa-spin';
	        commonFunctions.makeAjaxPost('/star/'+jobId, postData, successCallback);
	      },
	      expandGroup: function(event){
	        event.preventDefault();
	        this.props.updateJobList(this.props.index);
	        //commonFunctions.expandJobGroup(ReactDOM.findDOMNode(this));
	      },
	      render: function () {
	        var options = this.props.options;
	        var noOfPosts = options.posts.length;
	        var that = this;

	        if(noOfPosts === 1) {
	          var post = options.posts[0];
	          var ids = options.posts[0].url.split('/');
	          var iconClass;
	          if(post.starred === true){
	            iconClass = 'fa-star'
	          }else{
	            iconClass = 'fa-star-o'
	          }

	          return(
	            React.createElement("li", {className: "col-xs-12 col-md-3 col-sm-4 animated shake"}, " ", /*added animated shake for transition effect */

	              React.createElement("a", {className: "stickie", href: post.url, "data-href": post.url, rel: "bookmark"}, 
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
	                  React.createElement("i", {className: "fa pstar "+iconClass, "data-id": ids[2], onClick: that.starPost})
	                )
	              )
	            )
	          )
	        } else if(noOfPosts > 1) {
	          var nestedPosts = [];
	          var id = options.posts[0].url.split('/');
	          var iconClass;
	          if(options.posts[0].starred === true){
	            iconClass = 'fa-star'
	          }else{
	            iconClass = 'fa-star-o'
	          }

	          for(var i = 1; i < noOfPosts; i++) {
	            var ids = options.posts[i].url.split('/');

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

	                React.createElement("span", {className: "annotation bottom-left"}, 
	                  React.createElement("i", {className: "fa fa-star-o pstar", "data-id": ids[2], onClick: that.starPost})
	                )
	              )
	            )
	          }

	          return(
	            React.createElement("li", {className: "grouped col-xs-12 col-md-3 col-sm-4", onClick: that.expandGroup}, 

	              React.createElement("a", {className: "stickie", href: "javascript:void(0)", "data-href": options.posts[0].url, rel: "bookmark"}, 
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
	                  React.createElement("i", {className: "fa pstar "+iconClass, "data-id": id[2], onClick: that.starPost})
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
	    exports,
	    __webpack_require__(3)
	  ], __WEBPACK_AMD_DEFINE_RESULT__ = function (exports, $) {
	    exports.expandJobGroup = function(groupedElement){
	      var outerTemplate = document.createElement('li');
	      var innerTemplate = document.createElement('a');
	      var node, outer, inner;

	      outerTemplate.setAttribute('class', 'col-xs-12 col-md-3 col-sm-4 animated shake');
	      innerTemplate.setAttribute('class', 'stickie');
	      innerTemplate.setAttribute('rel', 'bookmark');

	      var group = groupedElement;
	      var parent=group.parentNode;

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
	    };

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
	        data: postData,
	        success: successCallback,
	        error: function (httpRequest, status, error) {
	          console.log(error);
	        }
	      });
	    };
	  }.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__))


/***/ }
]);