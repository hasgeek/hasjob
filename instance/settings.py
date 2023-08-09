import re

#: Words banned in the title and their error messages
BANNED_WORDS = [
    [
        ['awesome'],
        'We’ve had a bit too much awesome around here lately. Got another adjective?',
    ],
    [
        ['rockstar', 'rock star', 'rock-star'],
        'You are not rich enough to hire a rockstar. Got another adjective?',
    ],
    [
        ['superstar', 'super star'],
        'Everyone around here is a superstar. The term is redundant.',
    ],
    [
        ['kickass', 'kick ass', 'kick-ass', 'kicka$$', 'kick-a$$', 'kick a$$'],
        'We don’t condone kicking asses around here. Got another adjective?',
    ],
    [['ninja'], 'Ninjas kill people. We can’t allow that. Got another adjective?'],
    [
        ['urgent', 'immediate', 'emergency'],
        'Sorry, we can’t help with urgent or immediate requirements. Geeks don’t grow on trees',
    ],
    [['passionate'], 'Passion is implicit. Why even ask? Try another adjective?'],
    [['amazing'], 'Everybody’s amazing around here. The adjective is redundant.'],
    [
        ['fodu'],
        'We don’t know what you mean, but that sounds like a dirty word. Got another adjective?',
    ],
    [
        ['sick'],
        'Need an ambulance? Call 102, 108, 112 or 1298. One of those should work.',
    ],
    [['killer'], 'Murder is illegal. Don’t make us call the cops.'],
    [
        ['iit', 'iitian', 'iit-ian', 'iim', 'bits', 'bitsian'],
        'Q: How do you know someone is from IIT/IIM/BITS? A: They remind you all the time. Don’t be that person.',
    ],
]
#: URLs we don't accept, with accompanying error messages
INVALID_URLS = [
    (
        [
            re.compile(r'.*\.recruiterbox\.com/jobs'),
            re.compile(r'hire\.jobvite\.com/'),
            re.compile(r'bullhornreach\.com/job/'),
            re.compile(r'linkedin\.com/jobs'),
            re.compile(r'freelancer\.com'),
            re.compile(r'hirist\.com/j/'),
            re.compile(r'iimjobs\.com/j/'),
            re.compile(r'.*\.workable.com/jobs'),
        ],
        "Candidates must apply via Hasjob",
    )
]
