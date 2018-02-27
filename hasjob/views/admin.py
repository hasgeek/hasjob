# -*- coding: utf-8 -*-

from coaster.utils import classmethodproperty
from coaster.views import ClassView


class AdminView(ClassView):
    """Base class for all tabbed admin views"""

    @classmethodproperty
    def tabs(cls):
        views = ((name, getattr(cls, name)) for name in cls.__views__)
        tabviews = sorted((view.data.get('index', 0), name, view) for name, view, in views if view.data.get('tab'))
        return ((name, view.data['title'], view) for index, name, view in tabviews)

    @property
    def current_tab(self):
        return self.current_handler.name
