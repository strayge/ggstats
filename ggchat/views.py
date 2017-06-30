from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    output = 'index.html'
    return HttpResponse(output)
