define(
  [
    'react',
    'reactDom',
    './job-snippet',
    '../common-functions',
    'jquery',
    'jqueryAppear',

  ],
  function (React, ReactDOM, JobSnippet, commonFunctions, $) {

    var Hasjob = React.createClass({
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
          return <JobSnippet options={jobDetails} key={"snippet"+iterator} index={iterator} updateJobList={that.updateJobList}/>
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
