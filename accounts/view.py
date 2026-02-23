from django.shortcuts import render


def index(request):
    return render(request, 'deadlines.html', context=dict(text='Hello world'))