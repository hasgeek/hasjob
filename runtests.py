#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
import os
import nose

os.environ['HASJOB_ENV'] = "test"
nose.main()
