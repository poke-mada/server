from django.shortcuts import render


def coach_overlay(request):
    return render(request, 'coach_overlay.html')


def pro_overlay(request):
    return render(request, 'pro_overlay.html')
