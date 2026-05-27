from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='leads.Lead')
def recalculate_score_on_lead_save(sender, instance, created, **kwargs):
    update_fields = kwargs.get('update_fields')
    # Skip if only scoring fields were updated (prevents infinite recursion)
    if update_fields and set(update_fields) <= {'score', 'priority', 'score_updated_at', 'first_contact_at'}:
        return
    from .scoring import LeadScorer
    reason = 'new' if created else 'data_change'
    LeadScorer().update_lead(instance, reason=reason)


@receiver(post_save, sender='leads.LeadInteraction')
def recalculate_score_on_interaction(sender, instance, created, **kwargs):
    if not created:
        return
    from django.utils import timezone
    from .scoring import LeadScorer

    lead = instance.lead
    if lead.first_contact_at is None:
        lead.first_contact_at = timezone.now()
        lead.save(update_fields=['first_contact_at'])

    LeadScorer().update_lead(lead, reason='new_interaction')
