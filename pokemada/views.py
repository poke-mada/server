from django.http import Http404
from django.shortcuts import render

from event_api.models import Streamer, MastersProfile


def overlay(request, streamer_name):
    profile: MastersProfile = MastersProfile.objects.filter(
        user__username__iexact=streamer_name,
        user__masters_profile__profile_type=MastersProfile.TRAINER
    ).first()

    if not profile:
        raise Http404("Profile not found")

    coach: MastersProfile = profile.coaches.filter(user__is_active=True).first()
    coach_name = 'Sin coach'
    if coach:
        coach_name = coach.user.streamer_profile.name

    if profile.is_pro:
        return render(request, 'pro_overlay.html', {
            'streamer_name': profile.streamer_name
        })

    return render(request, 'coach_overlay.html', {
        'coach_name': coach_name,
        'streamer_name': profile.streamer_name
    })


def showdown(request, streamer_name):
    profile: MastersProfile = MastersProfile.objects.filter(
        user__username__iexact=streamer_name,
        user__masters_profile__profile_type=MastersProfile.TRAINER
    ).first()

    if not profile:
        raise Http404("Profile not found")

    coach: MastersProfile = profile.coaches.filter(user__is_active=True).first()
    coach_name = 'Sin coach'
    if coach:
        coach_name = coach.user.streamer_profile.name

    if profile.is_pro:
        return render(request, 'pro_showdown_overlay.html', {
            'streamer_name': profile.streamer_name
        })

    return render(request, 'coach_showdown_overlay.html', {
        'coach_name': coach_name,
        'streamer_name': profile.streamer_name
    })
