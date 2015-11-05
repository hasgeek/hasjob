define(
  [
    'react',
    'reactDom',
    'jquery',
    '../common-functions'
  ],
  function (React, ReactDOM, $, commonFunctions) {

    var JobSnippet = React.createClass({
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
            <li className="col-xs-12 col-md-3 col-sm-4 animated shake"> {/*added animated shake for transition effect */}

              <a className="stickie" href={post.url} data-href={post.url} rel="bookmark">
                <span className="annotation top-left">{post.location}</span>
                <span className="annotation top-right">
                  {post.date}
                </span>
                <span className="headline">{post.headline}</span>
                <span className="count">
                  <span title="Listed › Viewed › Opened form › Applied">
                    {post.viewcounts.listed+" > "+post.viewcounts.viewed+" > "+post.viewcounts.opened+" > "+post.viewcounts.applied}
                  </span> . {post.pay}</span>
                <span className="annotation bottom-right">{post.company_name}</span>

                <span className="annotation bottom-left">                 
                  <i className={"fa pstar "+iconClass} data-id={ids[2]} onClick={that.starPost}></i>
                </span>
              </a>
            </li>
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
              <div className="stickie grouped under" data-href={options.posts[i].url} key={ "snippet"+i}>
                <span className="annotation top-left">{options.posts[i].location}</span>
                <span className="annotation top-right">
                  {options.posts[i].date}
                </span>
                <span className="headline">{options.posts[i].headline}</span>
                <span className="count">
                  <span title="Listed › Viewed › Opened form › Applied">
                    {options.posts[i].viewcounts.listed+" > "+options.posts[i].viewcounts.viewed+" > "+options.posts[i].viewcounts.opened+" > "+options.posts[i].viewcounts.applied}
                  </span> · {options.posts[i].pay}
                </span>

                <span className="annotation bottom-right">
                  {options.posts[i].company_name}
                </span>

                <span className="annotation bottom-left">
                  <i className="fa fa-star-o pstar" data-id={ids[2]}  onClick={that.starPost}></i>
                </span>
              </div>
            )
          }

          return(
            <li className="grouped col-xs-12 col-md-3 col-sm-4" onClick={that.expandGroup}>

              <a className="stickie" href={"javascript:void(0)"} data-href={options.posts[0].url} rel="bookmark">
                <span className="annotation top-left">{options.posts[0].location}</span>
                <span className="annotation top-right">{options.posts[0].date}</span>
                <span className="headline">{options.posts[0].headline}</span>
                <span className="count">
                  <span title="Listed › Viewed › Opened form › Applied">
                    {options.posts[0].viewcounts.listed+" > "+options.posts[0].viewcounts.viewed+" > "+options.posts[0].viewcounts.opened+" > "+options.posts[0].viewcounts.applied}
                  </span> . {options.posts[0].pay}
                </span>
                <span className="annotation bottom-right">{options.posts[0].company_name}</span>

                <span className="annotation bottom-left">
                  <i className={"fa pstar "+iconClass} data-id={id[2]}  onClick={that.starPost}></i>
                </span>
              </a>
              {nestedPosts}
            </li>
          )
        }
      }
    });

    return JobSnippet
  }
)
