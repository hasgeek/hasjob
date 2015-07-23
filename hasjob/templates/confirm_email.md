Hello,

This is a confirmation email for the job you listed at {% if g.board -%} {{ g.board.title }} {%- else -%} {{ config['SITE_TITLE'] }} {%- endif %}.

**{{ post.headline|e }}**

[Click here to confirm your email address and publish the job][confirm]

[confirm]: {{ post.url_for('confirm-link', _external=true) }}

Save this email for the next 30 days while the post is active. Use these
links if you need to edit the post, or if the position has been filled
and you wish to close it:

* [Edit job post]({{ post.url_for('edit', _external=true) }})
* [Close job post]({{ post.url_for('close', _external=true) }})

{% if g.board and g.board.not_root %}[{{ g.board.title }}][board] is powered by Hasjob. {% endif -%}

[Hasjob][jb] is a service of [HasGeek][hg]. Write to us at
info@hasgeek.com if you have suggestions or questions on this service.

{% if g.board and g.board.not_root -%}
[board]: {{ g.board.url_for(_external=true) }}
{% endif -%}
[jb]: https://hasjob.co/
[hg]: https://hasgeek.com/

If you did not post a job, you may safely ignore this email.
