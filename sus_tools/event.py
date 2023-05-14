from .score import *
import json


def eventdump(lines):
    score = Score()
    events = []

    for line in lines:
        for obj in score.parse_line(Line(line)):
            if isinstance(obj, Event):
                eventData = {
                    "bar": obj.bar,
                    "bpm": obj.bpm
                }
                events.append(eventData)

    musicData = {
        "events": events
    }
    return musicData