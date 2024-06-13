# engagement_score.py

# Define thresholds
POSITIVE_THRESHOLD = 2  # seconds
NEGATIVE_THRESHOLD = 2  # seconds

# Define engagement criteria
ENGAGEMENT_CRITERIA = {
    'road_focus': {'positive': True, 'threshold': None},
    'mirror_check': {'positive': True, 'threshold': POSITIVE_THRESHOLD},
    'dashboard_check': {'positive': True, 'threshold': POSITIVE_THRESHOLD},
    'off_road_gaze': {'positive': False, 'threshold': NEGATIVE_THRESHOLD},
    'prolonged_check': {'positive': False, 'threshold': NEGATIVE_THRESHOLD},
    'closed_eyes': {'positive': False, 'threshold': 0}
}

def classify_positive_gaze(duration, threshold):
    if threshold is None:
        return 1  # Always positive if no threshold
    elif duration < threshold:
        return 1  # Positive
    elif duration == threshold:
        return 0  # Neutral
    else:
        return -1  # Negative

def classify_negative_gaze(duration, threshold):
    if duration > threshold:
        return -1  # Negative
    elif duration == threshold:
        return -1 if threshold > 0 else 0  # Edge case: 0 seconds for `closed_eyes`
    else:
        return 1  # Positive

def classify_closed_eyes(duration):
    if duration > 0:
        return -1  # Negative
    else:
        return 0  # Neutral if eyes are not closed at all

def calculate_engagement_score(gaze_data):
    score = 0
    for point, durations in gaze_data.items():
        if not isinstance(durations, list):
            durations = [durations]
        criteria = ENGAGEMENT_CRITERIA.get(point)
        if criteria:
            for duration in durations:
                if point == 'closed_eyes':
                    result = classify_closed_eyes(duration)
                elif criteria['positive']:
                    result = classify_positive_gaze(duration, criteria['threshold'])
                else:
                    result = classify_negative_gaze(duration, criteria['threshold'])
                score += result
    return score

def calculate_engagement_percentage(score, total_time):
    if total_time == 0:
        return 0  # Avoid division by zero
    if (score / total_time) <= 0:
        engagement_percentage = 0
    if (score / total_time) > 0:
        engagement_percentage = 100 - (score / total_time) * 100
    
    return engagement_percentage
