from __future__ import absolute_import

from django.conf.urls import url

from discussion import views

def return_200(request):
    from django.http import HttpResponse
    return HttpResponse('')

urlpatterns = [
    url(r'', return_200)
]
