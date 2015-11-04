define(
  [
    'react',
    'reactDom',
    './job-snippet',
    './header-bar',
    '../common-functions',
    'jquery',
    'jqueryAppear',

  ],
  function (React, ReactDOM, JobSnippet, HeaderBar, commonFunctions, $) {

    var Hasjob = React.createClass({
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
          return <JobSnippet options={jobDetails} key={"snippet"+iterator}/>
        });

        return(

          <div>
            <ul className="row" id="stickie-area">
              {jobSnippets}
            </ul>

            <form id="loadmore" method="GET" dataAppearTopffOset="600">
              <button className="btn btn-default btn-lg" type="submit" name="startdate">
                Load more…
              </button>
            </form>
          </div>

        )
      }

    });

    return Hasjob
  }
);
