Hello,

This is a confirmation email for the job you listed at Hasjob.

**{{ post.headline|e }}**

[Click here to confirm your email address and publish the job][confirm]

[confirm]: {{ url_for('confirm_email', _external=True, hashid=post.hashid, key=post.email_verify_key) }}

Save this email for the next 30 days while the listing is active. Use these
links if you need to edit the listing, or if the position has been filled
and you wish to withdraw it:

* [Edit job listing]({{ url_for('editjob', _external=True, hashid=post.hashid, key=post.edit_key) }})
* [Withdraw job listing]({{ url_for('withdraw', _external=True, hashid=post.hashid, key=post.edit_key) }})

The [HasGeek Job Board][jb] is a service of [HasGeek][hg]. Write to us at
info@hasgeek.com if you have suggestions or questions on this service.

[jb]: https://jobs.hasgeek.com
[hg]: https://hasgeek.com

If you did not list a job, you may safely ignore this email and the listing
will be automatically removed.
