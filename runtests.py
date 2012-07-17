#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
from os import environ
import nose

environ['HASJOB_ENV'] = 'testing'
nose.main()
