from django.shortcuts import render

from event_api.models import Streamer, MastersProfile


def coach_overlay(request, streamer_name):
    streamer = Streamer.objects.get(name=streamer_name)
    coach: MastersProfile = streamer.user.masters_profile.trainer.users.filter(
        profile_type=MastersProfile.COACH).first()
    coach_name = 'Sin coach'
    if coach:
        coach_name = coach.user.streamer_profile.name
    return render(request, 'coach_overlay.html', {
        'coach_name': coach_name,
        'streamer_name': streamer_name
    })


def pro_overlay(request, streamer_name):
    return render(request, 'pro_overlay.html', {
        'streamer_name': streamer_name
    })
