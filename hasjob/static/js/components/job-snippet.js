define(
	[
		'react',
		'reactDom',
		'jquery',
	], function(React, ReactDOM, $){

		var JobSnippet = React.createClass({

			componentDidMount: function(){
				// console.log('component rendered');
				// var monthNames = ['Jan', 'Feb', 'Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
				// 	date = [], parsedDate = [];

				// date[0] = new Date(ReactDOM.findDOMNode(this).children[0].children[1].innerHTML);
				// parsedDate[0] = monthNames[date[0].getMonth()] + " " + date[0].getDate();

				// ReactDOM.findDOMNode(this).children[0].children[1].innerHTML = parsedDate[0];

				// var noOfChildren = ReactDOM.findDOMNode(this).children.length;

				// if(noOfChildren > 0){
				// 	for(var i = 1; i< noOfChildren; i++){
				// 		date[i] = new Date(ReactDOM.findDOMNode(this).children[i].children[1].innerHTML);
				// 		parsedDate[i] = monthNames[date[i].getMonth()] + " " + date[i].getDate();

				// 		ReactDOM.findDOMNode(this).children[i].children[1].innerHTML = parsedDate[i];
				// 	}
				// }
			},
			
			render: function(){
				var style={
					marginBottom: '30px',
					verticalAlign: 'top'
				},
				options = this.props.options,
				noOfPosts = options.posts.length;
				
				if(noOfPosts === 1){
					var post = options.posts[0];
					return (
						<li className="col-xs-12 col-md-3 col-sm-4" style={style}>

						    <a className="stickie" href={options.url} rel="bookmark">
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
						      
						        <i className="fa fa-star-o pstar" data-id="kued5"></i>
						      </span>
						    </a>
						</li>
					)
				}else if(noOfPosts > 1){
					var nestedPosts = [];


					for(var i = 1; i<noOfPosts; i++){

						nestedPosts.push(
							<div className="stickie grouped under" data-href={options.posts[i].url} key={"snippet"+i}>
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
							  
							    {/*<i className="fa fa-star-o pstar" data-id="kvkl8"></i*/}
							    </span>
							</div>

						)	
					}


					return (
						<li className="grouped col-xs-12 col-md-3 col-sm-4" style={style}>

						    <a className="stickie" href={options.posts[0].url} rel="bookmark">
						        <span className="annotation top-left">{options.posts[0].location}</span>
						        <span className="annotation top-right">{options.posts[0].date}</span>
						        <span className="headline">{options.posts[0].headline}</span>
						        <span className="count">
						        	<span title="Listed › Viewed › Opened form › Applied">
						        		{options.posts[0].viewcounts.listed+" > "+options.posts[0].viewcounts.viewed+" > "+options.posts[0].viewcounts.opened+" > "+options.posts[0].viewcounts.applied}
						        	</span> . {options.posts[0].pay}</span>
						        <span className="annotation bottom-right">{options.posts[0].company_name}</span>
						        <span className="annotation bottom-left">
						      
						        <i className="fa fa-star-o pstar" data-id="kued5"></i>
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