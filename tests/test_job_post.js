var system = require('system');

var host = 'http://hasjob.travis.local:5001'; //presumably 127.0.0.1
var test_username = system.env.TEST_USERNAME; // Dummy user's username that's create on startup
var test_password = system.env.TEST_PASSWORD; // Dummy user's password that's create on startup

casper.options.waitTimeout = 60000;
casper.options.stepTimeout = 60000;

// Baseframe resources not needed for now
casper.on('resource.requested', function (requestData, request) {
  if (requestData.url.indexOf('_baseframe') > -1) {
    casper.log('Skipped: ' + requestData.url, 'info');
    request.abort();
  }
});

// Log remote console messages (useful for debugging)
// casper.on("remote.message", function(message) {
//   this.echo("remote console.log: " + message);
// });

casper.test.begin('Hasjob Post A Job Flow', 13, function suite(test) {
  casper.start(host, function () {
    test.assertHttpStatus(200);
  });

  casper.thenOpen(host + '/new', function () {
    test.assertHttpStatus(200);
    test.assertUrlMatch(/login/, 'Redirected to lastuser login');

    casper.evaluate(
      function (username, password) {
        document.querySelector('#username').value = username;
        document.querySelector('#password').value = password;
        document.querySelector('#passwordlogin').submit();
      },
      test_username,
      test_password,
    );
  });

  casper.thenOpen(host + '/new', function () {
    test.assertHttpStatus(200);
    test.assertUrlMatch(/new/, 'Logged in successfully');

    casper.evaluate(function () {
      document.querySelector('#job_headline').value = 'Testing job post';
      document.querySelector('#job_type-0').checked = true;
      document.querySelector('#job_category-2').checked = true;
      document.querySelector('#job_location').value = 'Bangalore';
      document.querySelector('#job_description').value =
        'This job required people, mostly';
      document.querySelector('#job_pay_type-1').checked = true;
      document.querySelector('#job_pay_currency-1').checked = true;
      document.querySelector('#job_pay_cash_min').value = '300000';
      document.querySelector('#job_pay_cash_max').value = '500000';
      document.querySelector('#job_how_to_apply').value =
        'What is the answer to Life, the Universe and Everything?';
      document.querySelector('#company_name').value = 'Acme Corp';
      document.querySelector('#company_url').value = 'http://mailinator.com/';
      document.querySelector('#poster_email').value = 'travishasjob@mailinator.com';
      document.querySelector('#newjob').submit();
    });
  });

  casper.waitForUrl(/view/, function () {
    test.assertHttpStatus(200);
    test.assertUrlMatch(/view/, 'Job posted, now to review');
    test.assertSelectorHasText('div.page-header>h2', 'Review this post');
    casper.evaluate(function () {
      document.querySelector('input[value="This looks good, confirm it"]').click();
    });
  });

  casper.then(function () {
    test.assertHttpStatus(200);
    test.assertUrlMatch(/confirm/, 'Job reviewed, now to confirm');
    test.assertSelectorHasText('div.page-header>h1', 'Terms of service');

    casper.evaluate(function () {
      document.querySelector('#terms_accepted').checked = true;
      document.querySelector('form.form-horizontal').submit();
    });
  });

  casper.waitForUrl(/confirm/, function () {
    test.assertHttpStatus(200);
    test.assertSelectorHasText('div.page-header>h1', 'One last step…');
    console.log('Email sent. Now what?');
  });

  casper.run(function () {
    test.done();
  });
});
