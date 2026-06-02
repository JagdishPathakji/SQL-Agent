# Intent Classifier Configuration Settings

# Confidence score below this value triggers requires_clarification = True
INTENT_CONFIDENCE_THRESHOLD = 0.60

# Maximum number of recent messages to send to the LLM context
MAX_HISTORY_MESSAGES = 5

# Enable the hardcoded pre-LLM security scanning layer
ENABLE_SECURITY_FILTER = True

# Enable strict interception and blocking of database schema/catalog structures
ENABLE_SCHEMA_BLOCKING = True
