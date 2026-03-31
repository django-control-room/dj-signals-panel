from django.dispatch import Signal

# Some custom signals for testing. Note that these signals
# are not sent within the app, we are not testing  the django
# signal sending functionality.

user_profile_created = Signal()

order_confirmed = Signal()

notification_requested = Signal()

report_generated = Signal()
