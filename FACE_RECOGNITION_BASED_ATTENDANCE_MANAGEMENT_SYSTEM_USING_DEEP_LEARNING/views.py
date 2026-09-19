

from django.shortcuts import render


def index(request):
    return render(request,'index.html')


def studentRegister(request):
    return render(request,'studentRegister.html')


def facultyLogin(request):
    return render(request,'facultyLogin.html')


def studentLogin(request):
    return render(request,'studentAttendence.html')
