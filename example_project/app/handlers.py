import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .signals import notification_requested, order_confirmed, user_profile_created

logger = logging.getLogger(__name__)

User = get_user_model()


def on_profile_created_log(sender, **kwargs):
    """Plain function receiver — no dispatch_uid, no sender filter."""
    logger.info("user_profile_created signal received (log handler)")


def on_profile_created_welcome(sender, **kwargs):
    """Second receiver on the same signal"""
    logger.info("user_profile_created signal received (welcome handler)")


@receiver(order_confirmed)
def on_order_confirmed(sender, **kwargs):
    """Receiver wired via @receiver decorator."""
    logger.info("order_confirmed signal received")


def on_notification_email(sender, **kwargs):
    """Email notification handler."""
    logger.info("notification_requested: sending email")


def on_notification_push(sender, **kwargs):
    """Push notification handler."""
    logger.info("notification_requested: sending push notification")


def on_notification_sms(sender, **kwargs):
    """SMS notification handler."""
    logger.info("notification_requested: sending SMS")


def on_user_saved(sender, instance, created, **kwargs):
    """
    Receiver on Django's built-in post_save, filtered to the User model.
    Demonstrates sender-specific registration in the panel.
    """
    if created:
        logger.info("New user created: %s", instance.username)


@receiver(post_save)
def on_any_user_saved(sender, instance, created, **kwargs):
    if created:
        logger.info("Any user saved: %s", instance.username)


def connect_all():
    """
    Wire all receivers to their signals.
    Called from AppConfig.ready() to ensure signals are connected once
    the app registry is fully populated.
    """
    user_profile_created.connect(on_profile_created_log)
    user_profile_created.connect(
        on_profile_created_welcome,
        dispatch_uid="app.handlers.on_profile_created_welcome",
    )

    notification_requested.connect(on_notification_email)
    notification_requested.connect(on_notification_push)
    notification_requested.connect(on_notification_sms)

    post_save.connect(on_user_saved, sender=User)
