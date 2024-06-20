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

def classify_gaze_direction(gaze_direction):
    if gaze_direction == 'road':
        return 'road_focus'
    elif gaze_direction in ['left_mirror', 'right_mirror']:
        return 'mirror_check'
    else:
        return 'off_road_gaze'

def calculate_engagement_score(prediction):
    score = 0
    max_possible_score = len(prediction) * 1  # Each direction is considered for scoring
    if max_possible_score == 0:
        return 0  # Prevent division by zero

    for gaze_direction in prediction:
        criteria_key = classify_gaze_direction(gaze_direction)
        criteria = ENGAGEMENT_CRITERIA.get(criteria_key)
        if criteria:
            duration = 1  # Assume each gaze direction corresponds to a unit duration
            result = classify_gaze_duration(duration, criteria['threshold'])
            score += result

    engagement_percentage = ((score + max_possible_score) / (2 * max_possible_score)) * 100
    return engagement_percentage

def classify_gaze_duration(duration, threshold):
    if threshold is None:
        return 1  # Always positive if no threshold
    elif duration < threshold:
        return 1  # Positive
    elif duration == threshold:
        return 0  # Neutral
    else:
        return -1  # Negative
