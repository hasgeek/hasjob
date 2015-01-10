Hello,

This is a confirmation email for the job you listed at {% if g.board -%} {{ g.board.title }} {%- else -%} Hasjob {%- endif %}.

**{{ post.headline|e }}**

[Click here to confirm your email address and publish the job][confirm]

[confirm]: {{ url_for('confirm_email', _external=True, hashid=post.hashid, key=post.email_verify_key) }}

Save this email for the next 30 days while the post is active. Use these
links if you need to edit the post, or if the position has been filled
and you wish to withdraw it:

* [Edit job post]({{ url_for('editjob', _external=True, hashid=post.hashid) }})
* [Withdraw job post]({{ url_for('withdraw', _external=True, hashid=post.hashid) }})

{% if g.board %}[{{ g.board.title }}][board] is powered by Hasjob. {% endif -%}

[Hasjob][jb] is a service of [HasGeek][hg]. Write to us at
info@hasgeek.com if you have suggestions or questions on this service.

{% if g.board -%}
[board]: {{ g.board.url_for(_external=True) }}
{% endif -%}
[jb]: https://hasjob.co/
[hg]: https://hasgeek.com/

If you did not post a job, you may safely ignore this email.
