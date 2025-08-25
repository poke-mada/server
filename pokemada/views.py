from django.http import Http404
from django.shortcuts import render

from event_api.models import MastersProfile


def overlay(request, streamer_name):
    profile: MastersProfile = MastersProfile.objects.filter(
        user__username__iexact=streamer_name,
    ).exclude(user__masters_profile__profile_type=MastersProfile.ADMIN).first()

    if not profile:
        raise Http404("Profile not found")

    if profile.profile_type == MastersProfile.COACH:
        profile = profile.coached

    coach: MastersProfile = profile.main_coach
    coach_name = 'Sin coach'
    if coach:
        coach_name = coach.user.username

    if profile.is_pro:
        return render(request, 'pro_overlay.html', {
            'streamer_name': profile.user.username
        })

    return render(request, 'coach_overlay.html', {
        'coach_name': coach_name,
        'streamer_name': profile.user.username
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
        coach_name = coach.user.username

    if profile.is_pro:
        return render(request, 'pro_showdown_overlay.html', {
            'streamer_name': profile.user.username
        })

    return render(request, 'coach_showdown_overlay.html', {
        'coach_name': coach_name,
        'streamer_name': profile.user.username
    })
