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

# Function to classify gaze directions
def classify_gaze_direction(gaze_direction):
    if 'Right' in gaze_direction or 'Left' in gaze_direction:
        return 'off_road_gaze'
    elif 'UP' in gaze_direction or 'DOWN' in gaze_direction:
        return 'dashboard_check'
    else:
        return 'road_focus'

# Function to classify gaze duration
def classify_gaze_duration(duration, threshold):
    if threshold is None:
        return 1  # Always positive if no threshold
    elif duration < threshold:
        return 1  # Positive
    elif duration == threshold:
        return 0  # Neutral
    else:
        return -1  # Negative

def calculate_engagement_score(gaze_data):
    score = 0
    max_possible_score = len(gaze_data['gaze_direction']) * 1  # Each direction is considered for scoring
    if max_possible_score == 0:
        return 0  # Prevent division by zero
    
    for gaze_direction in gaze_data['gaze_direction']:
        criteria_key = classify_gaze_direction(gaze_direction)
        criteria = ENGAGEMENT_CRITERIA.get(criteria_key)
        if criteria:
            duration = 1  # Assume each gaze direction corresponds to a unit duration
            result = classify_gaze_duration(duration, criteria['threshold'])
            score += result

    # Normalize the score to be within the range of 0 to 100
    engagement_percentage = ((score + max_possible_score) / (2 * max_possible_score)) * 100
    return engagement_percentage

def calculate_engagement_percentage(score, max_possible_score):
    if max_possible_score == 0:
        return 0  # Prevent division by zero
    return (score / max_possible_score) * 100
