define(
  [
    'react',
    'jquery',
  ],
  function (React, $) {
    var HeaderBar = React.createClass({
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
          <header>

            <nav className="navbar navbar-default navbar-fixed-top" id="hgnav" role="navigation">
              <div className="container">
                <div className="navbar-header pull-left hg-header-app-nav">

                  <div className="page-header">
                    <h1><a href="https://hasjob.co">Hasjob <small className="board-caption">The HasGeek Job Board</small></a></h1>
                  </div>

                </div>
                <div className="navbar-header pull-right hg-header-nav">
                  <ul className="nav pull-right">
                    <li className="dropdown pull-left">

                      <button type="button" data-toggle="dropdown" className="dropdown-toggle" id="hg-user-btn">
                        <i className="fa fa-user"></i>
                      </button>
                      <ul className="dropdown-menu pull-right">
                        <li>

                          <a href="https://auth.hasgeek.com/profile" title="Ashwin Hariharan (~ashwin01)">Ashwin Hariharan</a>

                        </li>
                        <li><a href="https://hasjob.co/logout">Logout</a></li>
                      </ul>
                    </li>

                    <li className="dropdown pull-left">
                      <button type="button" data-toggle="collapse" data-target=".navbar-collapse" className="menu-toggle hg-site-nav-toggle">
                        <i className="fa fa-search"></i>
                      </button>
                    </li>

                    <li className="dropdown pull-right hg-nw-bar">

                      <button type="button" className="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false" id="hg-app-drawer">
                        <i className="fa fa-th"></i>
                      </button>
                      <ul className="dropdown-menu block-dropdown" role="menu">
                        <li>
                          <a href="http://hasgeek.com/">
                            <img src="/static/img/hg-banner.png" alt="..." />
                            <h6>HasGeek</h6>
                          </a>
                        </li>
                        <li>
                          <a href="https://talkfunnel.com/">
                            <img src="/static/img/hg_funnel.png" alt="..." />
                            <h6>Talkfunnel</h6>
                          </a>
                        </li>
                        <li>
                          <a href="/static/img/Hasjob.html">
                            <img src="/static/img/logo-star.png" alt="..." />
                            <h6>Hasjob</h6>
                          </a>
                        </li>
                        <li>
                          <a href="https://hasgeek.tv/">
                            <img src="/static/img/hg_hgtv.png" alt="..." />
                            <h6>HGTV</h6>
                          </a>
                        </li>
                      </ul>

                    </li>
                  </ul>
                </div>

                <div className="nav collapse navbar-collapse navbar-right hg-site-nav" id="hg-sitenav">

                  <div className="header-section" id="filter-dropdown" style={style1}>
                    <form id="job-filters" action="https://hasjob.co/search" role="form">
                      <div className="row">
                        <div className="filters filters-col1 location-filter col-xs-12 col-sm-4 col-md-3">
                          <select id="job-filters-location" name="l" multiple="multiple" className="job-filters-select2 notselect hidden" placeholder="Location" style={style1}>
                            <option value="anywhere" id="job-filters-remote-check">Anywhere/Remote</option>
                            <option value="bangalore">Bangalore, IN</option>
                            <option value="mumbai">Mumbai, IN</option>
                            <option value="delhi">Delhi, IN</option>
                            <option value="chennai">Chennai, IN</option>
                            <option value="hyderabad">Hyderabad, IN</option>
                            <option value="pune">Pune, IN</option>
                            <option value="gurgaon">Gurgaon, IN</option>
                            <option value="noida">Noida, IN</option>
                            <option value="ahmedabad">Ahmedabad, IN</option>
                            <option value="goa">Goa, IN (state)</option>
                            <option value="jaipur">Jaipur, IN</option>
                            <option value="anderson2">Anderson, SC, US</option>
                            <option value="kolkata">Kolkata, IN</option>
                            <option value="jalandhar">Jalandhar, IN</option>
                            <option value="india">India (country)</option>
                            <option value="mysore">Mysore, IN</option>
                            <option value="west-region">West Region, CM (state)</option>
                            <option value="thiruvananthapuram">Thiruvananthapuram, IN</option>
                            <option value="coimbatore">Coimbatore, IN</option>
                            <option value="purwanchal">Purwanchal, NP (state)</option>
                            <option value="san-francisco2">San Francisco, CA, US</option>
                            <option value="berlin">Berlin, DE</option>
                            <option value="chandigarh2">Chandigarh, IN</option>
                            <option value="sudurland">Sudurland, IS (state)</option>
                            <option value="panaji">Panaji, IN</option>
                            <option value="punjab">Punjab, IN (state)</option>
                            <option value="mangalore">Mangalore, IN</option>
                            <option value="cochin">Cochin, IN</option>
                            <option value="tirupati">Tirupati, IN</option>
                            <option value="oman">Oman (country)</option>
                            <option value="ostan-e-mazandaran">Ostan-e Mazandaran, IR (state)</option>
                            <option value="shanghai">Shanghai, CN</option>
                            <option value="haora">Haora, IN</option>
                            <option value="udaipur3">Udaipur, IN</option>
                            <option value="london">London, GB</option>
                          </select>
                          <div className="btn-group" style={style3}>
                            <button type="button" className="multiselect dropdown-toggle btn btn-default" data-toggle="dropdown" title="Location" style={style2}><span className="multiselect-selected-text">Location</span> <b className="caret"></b></button>
                            <ul className="multiselect-container dropdown-menu">
                              <li value="0">
                                <div className="input-group input-group-sm">
                                  <div className="input-group-addon"><i className="fa fa-search"></i></div>
                                  <input type="text" className="form-control" id="job-filter-location-search" placeholder="Search" />
                                  <div className="input-group-addon job-filter-location-search-clear"><i className="fa fa-times"></i></div>
                                </div>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="anywhere" /> Anywhere/Remote</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="bangalore" /> Bangalore, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="mumbai" /> Mumbai, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="delhi" /> Delhi, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="chennai" /> Chennai, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="hyderabad" /> Hyderabad, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="pune" /> Pune, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="gurgaon" /> Gurgaon, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="noida" /> Noida, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="ahmedabad" /> Ahmedabad, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="goa" /> Goa, IN (state)</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="jaipur" /> Jaipur, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="anderson2" /> Anderson, SC, US</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="kolkata" /> Kolkata, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="jalandhar" /> Jalandhar, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="india" /> India (country)</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="mysore" /> Mysore, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="west-region" /> West Region, CM (state)</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="thiruvananthapuram" /> Thiruvananthapuram, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="coimbatore" /> Coimbatore, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="purwanchal" /> Purwanchal, NP (state)</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="san-francisco2" /> San Francisco, CA, US</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="berlin" /> Berlin, DE</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="chandigarh2" /> Chandigarh, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="sudurland" /> Sudurland, IS (state)</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="panaji" /> Panaji, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="punjab" /> Punjab, IN (state)</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="mangalore" /> Mangalore, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="cochin" /> Cochin, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="tirupati" /> Tirupati, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="oman" /> Oman (country)</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="ostan-e-mazandaran" /> Ostan-e Mazandaran, IR (state)</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="shanghai" /> Shanghai, CN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="haora" /> Haora, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="udaipur3" /> Udaipur, IN</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="london" /> London, GB</label>
                                </a>
                              </li>
                            </ul>
                          </div>
                        </div>
                        <div className="filters col-xs-12 col-sm-4 col-md-3">
                          <select id="job-filters-type" name="t" multiple="multiple" className="job-filters-select2 notselect hidden" placeholder="Job Type" style={style1}>
                            <option value="fulltime">Full-time employment</option>
                            <option value="contract">Short-term contract</option>
                            <option value="intern">Internship</option>
                            <option value="freelance">Freelance or consulting</option>
                            <option value="volunteer">Volunteer contributor</option>
                            <option value="partner">Partner for a venture</option>
                          </select>
                          <div className="btn-group" style={style3}>
                            <button type="button" className="multiselect dropdown-toggle btn btn-default" data-toggle="dropdown" title="Job Type" style={style2}><span className="multiselect-selected-text">Job Type</span> <b className="caret"></b></button>
                            <ul className="multiselect-container dropdown-menu">
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="fulltime" /> Full-time employment</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="contract" /> Short-term contract</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="intern" /> Internship</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="freelance" /> Freelance or consulting</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="volunteer" /> Volunteer contributor</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="partner" /> Partner for a venture</label>
                                </a>
                              </li>
                            </ul>
                          </div>
                        </div>
                        <div className="filters col-xs-12 col-sm-4 col-md-3 category-filter">
                          <select id="job-filters-category" name="c" multiple="multiple" className="job-filters-select2 notselect hidden" placeholder="Job Category" style={style1}>
                            <option value="programming">Programming</option>
                            <option value="ux">Interaction Design</option>
                            <option value="design">Graphic Design</option>
                            <option value="electronics">Electronics</option>
                            <option value="testing">Testing</option>
                            <option value="sysadmin">Systems Administration</option>
                            <option value="business">Business/Management</option>
                            <option value="edit">Writer/Editor</option>
                            <option value="support">Customer Support</option>
                            <option value="mobile">Mobile (iPhone, Android, other)</option>
                            <option value="officeadmin">Office Administration</option>
                          </select>
                          <div className="btn-group" style={style3}>
                            <button type="button" className="multiselect dropdown-toggle btn btn-default" data-toggle="dropdown" title="Job Category" style={style2}><span className="multiselect-selected-text">Job Category</span> <b className="caret"></b></button>
                            <ul className="multiselect-container dropdown-menu">
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="programming" /> Programming</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="ux" /> Interaction Design</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="design" /> Graphic Design</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="electronics" /> Electronics</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="testing" /> Testing</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="sysadmin" /> Systems Administration</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="business" /> Business/Management</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="edit" /> Writer/Editor</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="support" /> Customer Support</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="mobile" /> Mobile (iPhone, Android, other)</label>
                                </a>
                              </li>
                              <li>
                                <a tabindex="0">
                                  <label className="checkbox">
                                    <input type="checkbox" value="officeadmin" /> Office Administration</label>
                                </a>
                              </li>
                            </ul>
                          </div>
                        </div>
                        <div className="filters dropdown col-xs-12 col-sm-4 col-md-3">
                          <div id="job-filters-pay" className="btn-group btn-block no-jshidden">
                            <button type="button" className="btn btn-default dropdown-toggle btn-block" data-toggle="dropdown" aria-expanded="false">
                              <span id="job-filters-pay-text" className="pay-field">Pay</span>
                              <span className="caret"></span>
                            </button>
                            <ul className="dropdown-menu pay-filter-dropdown" role="menu" aria-labelledby="job-filters-pay">
                              <li className="clearfix">
                                <div className="currency-checkbox">
                                  <input type="radio" id="job-filters-na" name="currency" value="NA" checked="checked" />
                                  <label for="job-filters-na">Any</label>
                                </div>
                                <div className="currency-checkbox">
                                  <input type="radio" id="job-filters-inr" name="currency" value="INR" />
                                  <label for="job-filters-inr">INR</label>
                                </div>
                                <div className="currency-checkbox">
                                  <input type="radio" id="job-filters-usd" name="currency" value="USD" />
                                  <label for="job-filters-usd">USD</label>
                                </div>
                                <div className="currency-checkbox">
                                  <input type="radio" id="job-filters-eur" name="currency" value="EUR" />
                                  <label for="job-filters-eur">EUR</label>
                                </div>
                              </li>
                              <li className="pay-filter-slider" style={style1}>
                                <div>
                                  <input type="hidden" name="pmin" id="job-filters-pmin" value="¤0" />
                                  <input type="hidden" name="pmax" id="job-filters-pmax" value="¤10,000,000" />
                                  <div id="pay-slider" className="noUi-target noUi-ltr noUi-horizontal noUi-background">
                                    <div className="noUi-base">
                                      <div className="noUi-origin noUi-connect" style={style4}>
                                        <div className="noUi-handle noUi-handle-lower"></div>
                                      </div>
                                      <div className="noUi-origin noUi-background" style={style5}>
                                        <div className="noUi-handle noUi-handle-upper"></div>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </li>
                              <li>
                                <label for="job-filters-equity" className="equity-label">
                                  <input type="checkbox" name="equity" id="job-filters-equity" value="1" /> Equity</label>
                              </li>
                            </ul>
                          </div>
                        </div>
                        <div className="filters col-xs-12 col-sm-4 col-md-3">
                          <input id="job-filters-keywords" className="filter-select form-control" type="text" placeholder="Keywords" name="q" value="" />
                        </div>
                        <div className="submit-filters col-xs-4 col-sm-2 col-md-2">
                          <button id="job-filters-submit" type="submit" className="btn btn-default submit-btn">
                            <span><i className="fa fa-filter"></i>Filter</span>
                          </button>
                        </div>
                        <div className="cancel-filters col-xs-4 visible-xs">
                          <button id="job-filters-cancel" className="btn btn-default submit-btn">
                            <span><i className="fa fa-close"></i>Cancel</span>
                          </button>
                        </div>
                      </div>
                    </form>
                  </div>

                </div>

              </div>
            </nav>

          </header>
        )
      }
    });

    return HeaderBar;
  }
)