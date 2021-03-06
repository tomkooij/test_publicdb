from django.http import HttpResponse

import calendar
from datetime import datetime, date
import json
from random import randint

import numpy as np
import operator

from ..histograms.models import Configuration
from ..analysissessions.models import (AnalyzedCoincidence, AnalysisSession,
                                       Student)


def get_coincidence(request):
    """Return a coincidence for jSparc client"""

    session_title = request.GET.get('session_title', None)
    session_pin = request.GET.get('session_pin', None)
    student_name = request.GET.get('student_name', None)

    if session_title.lower() == 'example':
        today = date.today()
        coincidences = AnalyzedCoincidence.objects.filter(
            session__ends__gt=today)
        count = coincidences.count()
        if not count:
            return error_json(404, 'No coincidences available.')
        random_index = randint(0, count - 1)
        coincidence = coincidences[random_index]
        events = get_events(coincidence)
        response = data_json(coincidence, events)
        return response

    try:
        session = AnalysisSession.objects.get(title=session_title)
        if session.pin != session_pin:
            return error_json(401, 'Wrong pin for this session.')
    except AnalysisSession.DoesNotExist:
        return error_json(404, 'No session with that title.')
    except ValueError:
        raise
    else:
        if not session.in_progress():
            return error_json(404, "The requested session has not started yet "
                                   "or is already expired.")

    if not student_name:
        student = Student.objects.get(session=session,
                                      name='Test student')
    else:
        student, is_created = Student.objects.get_or_create(session=session,
                                                            name=student_name)

    coincidences = AnalyzedCoincidence.objects.filter(session=session)
    try:
        coincidence = coincidences.filter(student=student,
                                          is_analyzed=False)[0]
    except IndexError:
        try:
            coincidence = coincidences.filter(student=None,
                                              is_analyzed=False)[0]
            coincidence.student = student
            coincidence.save()
        except IndexError:
            return error_json(404, "No unanalysed coincidences available, "
                                   "request a new session.")

    events = get_events(coincidence)
    response = data_json(coincidence, events)
    return response


def get_events(coincidence):
    """Get events that belong to this coincidence"""
    events = []
    for event in coincidence.coincidence.events.all():
        try:
            config = (Configuration.objects
                                   .filter(source__station=event.station,
                                           source__date__lte=event.date)
                                   .exclude(gps_latitude=0,
                                            gps_longitude=0).latest())
        except Configuration.DoesNotExist:
            continue

        timestamp = calendar.timegm(datetime.combine(event.date, event.time)
                                            .utctimetuple())
        event_dict = dict(timestamp=timestamp,
                          nanoseconds=event.nanoseconds,
                          number=event.station.number,
                          latitude=config.gps_latitude,
                          longitude=config.gps_longitude,
                          altitude=config.gps_altitude,
                          status='on',
                          detectors=len(event.traces),
                          traces=event.traces,
                          pulseheights=event.pulseheights,
                          integrals=event.integrals,
                          mips=[ph / 200. if ph > 0 else ph
                                for ph in event.pulseheights])
        events.append(event_dict)
    return events


def data_json(coincidence, events):
    """Construct json with data for jSparc to display"""
    data = dict(pk=coincidence.pk,
                timestamp=calendar.timegm(
                    datetime.combine(coincidence.coincidence.date,
                                     coincidence.coincidence.time)
                            .utctimetuple()),
                nanoseconds=coincidence.coincidence.nanoseconds,
                events=events)
    response = HttpResponse(json.dumps(data), content_type='application/json')
    response['Access-Control-Allow-Origin'] = '*'
    return response


def error_json(error_code, message):
    """Construct error response json for jSparc requests"""
    data = dict(message=message, code=error_code)
    response = HttpResponse(json.dumps(data), status=error_code,
                            content_type='application/json')
    response['Access-Control-Allow-Origin'] = '*'
    return response


def top_lijst(slug):
    coincidences = AnalyzedCoincidence.objects.filter(session__slug=slug,
                                                      is_analyzed=True)
    scores = []
    for s in Student.objects.all():
        error = []
        num_events = 0
        for ac in coincidences.filter(student=s):
            if ac.error_estimate:
                error.append(ac.error_estimate)
                num_events += 1
        if error:
            avg_error = np.average(error)
            wgh_error = avg_error / num_events
            min_error = min(error)
            scores.append({'name': s.name, 'avg_error': avg_error,
                           'wgh_error': wgh_error, 'min_error': min_error,
                           'num_events': num_events})

    return sorted(scores, key=operator.itemgetter('wgh_error'))


def result(request):
    """Process results from jSparc sessions"""
    session_title = request.GET['session_title']

    # If session is example, do not save result.
    if session_title.lower() == 'example':
        return test_result()

    pk = request.GET['pk']
    coincidence = AnalyzedCoincidence.objects.get(pk=pk)

    # If student is test student, do not save result.
    if coincidence.student.name.lower() == 'test student':
        return test_result()

    student_name = request.GET['student_name']
    latitude = request.GET['latitude']
    longitude = request.GET['longitude']
    log_energy = request.GET['logEnergy']
    error_estimate = request.GET['error']

    assert coincidence.session.title.lower() == session_title.lower()
    assert coincidence.student.name.lower() == student_name.lower()

    coincidence.core_position_x = longitude
    coincidence.core_position_y = latitude
    coincidence.log_energy = log_energy
    coincidence.error_estimate = error_estimate
    coincidence.is_analyzed = True
    coincidence.theta = 0
    coincidence.phi = 0
    coincidence.save()

    ranking = top_lijst(coincidence.session.slug)
    try:
        rank = [x['name'] for x in ranking].index(student_name) + 1
    except ValueError:
        rank = None
    msg = "OK [result stored]"
    response = HttpResponse(json.dumps(dict(msg=msg, rank=rank)),
                            content_type='application/json')
    response['Access-Control-Allow-Origin'] = '*'
    return response


def test_result():
    """Generate random ranking for test sessions"""
    msg = "Test session, result not stored"
    rank = randint(1, 10)
    response = HttpResponse(json.dumps(dict(msg=msg, rank=rank)),
                            content_type='application/json')
    response['Access-Control-Allow-Origin'] = '*'
    return response
