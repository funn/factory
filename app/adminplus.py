from django.utils.text import capfirst
from django.contrib.admin import AdminSite


class AdminPlus(AdminSite):
    """Mixin for AdminSite to allow registering custom admin views."""

    index_template = 'admin/index.html'  # That was easy.

    def __init__(self, *args, **kwargs):
        self.custom_views = []
        super(AdminPlus, self).__init__(*args, **kwargs)

    def register_view(self, path, name=None, urlname=None, visible=True,
                      view=None, default_view=None):
        """Add a custom admin view. Can be used as a function or a decorator.

        * `path` is the path in the admin where the view will live, e.g.
            http://example.com/admin/somepath
        * `name` is an optional pretty name for the list of custom views. If
            empty, we'll guess based on view.__name__.
        * `urlname` is an optional parameter to be able to call the view with a
            redirect() or reverse()
        * `visible` is a boolean to set if the custom view should be visible in
            the admin dashboard or not.
        * `view` is any view function you can imagine.
        """
        if view is not None:
            self.custom_views.append((path, view, name, urlname, visible, default_view))
            return

        def decorator(fn):
            self.custom_views.append((path, fn, name, urlname, visible, default_view))
            return fn
        return decorator

    def get_urls(self):
        """Add our custom views to the admin urlconf."""
        urls = super(AdminPlus, self).get_urls()
        from django.conf.urls import patterns, url
        for path, view, name, urlname, visible, _ in self.custom_views:
            urls = patterns(
                '',
                url(r'^%s$' % path, self.admin_view(view), name=urlname),
            ) + urls
        return urls

    def index(self, request, extra_context=None):
        """Make sure our list of custom views is on the index page."""
        if not extra_context:
            extra_context = {}
        custom_list = []
        for _, view, name, urlname, visible, default_view in self.custom_views:
            if visible is True:
                if name:
                    custom_list.append((default_view, name))
                else:
                    custom_list.append((default_view, capfirst(view.__name__)))

        # Sort views alphabetically.
        custom_list.sort(key=lambda x: x[1])
        extra_context.update({
            'custom_list': custom_list
        })
        return super(AdminPlus, self).index(request, extra_context)


'''
Code above was taken from https://github.com/jsocol/django-adminplus and slightly modified ;)

Copyright (c) 2011, Mozilla Foundation
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of AdminPlus nor the names of its contributors may
       be used to endorse or promote products derived from this software
       without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
