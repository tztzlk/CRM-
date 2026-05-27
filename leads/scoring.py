from django.utils import timezone


class LeadScorer:
    """Rule-based lead scoring engine. Scores 0-100 across 5 weighted factors."""

    SOURCE_SCORES = {
        'referral': 25,
        'website': 20,
        'ads': 15,
        'social': 10,
        'other': 5,
    }

    def calculate(self, lead) -> tuple:
        """Return (total_score, breakdown_dict). Does not write to DB."""
        breakdown = {}

        # Factor 1: Source of lead (max 25)
        source_score = self.SOURCE_SCORES.get(lead.source, 5)
        breakdown['source'] = {
            'label': 'Источник лида',
            'score': source_score,
            'max': 25,
            'detail': lead.get_source_display(),
        }

        # Factor 2: Time waiting since creation (max 25)
        if lead.created_at:
            hours_waiting = (timezone.now() - lead.created_at).total_seconds() / 3600
            if hours_waiting < 0.5:
                time_score, time_detail = 25, 'менее 30 минут'
            elif hours_waiting < 2:
                time_score, time_detail = 20, 'менее 2 часов'
            elif hours_waiting < 24:
                time_score, time_detail = 10, 'менее 24 часов'
            else:
                time_score, time_detail = 0, f'{int(hours_waiting)} ч без реакции'
        else:
            time_score, time_detail = 0, 'неизвестно'
        breakdown['time'] = {
            'label': 'Время ожидания',
            'score': time_score,
            'max': 25,
            'detail': time_detail,
        }

        # Factor 3: Client activity (interactions count, max 20)
        interactions_count = lead.interactions.count()
        if interactions_count >= 3:
            activity_score = 20
        elif interactions_count == 2:
            activity_score = 15
        elif interactions_count == 1:
            activity_score = 8
        else:
            activity_score = 0
        breakdown['activity'] = {
            'label': 'Активность клиента',
            'score': activity_score,
            'max': 20,
            'detail': f'{interactions_count} взаимодействий',
        }

        # Factor 4: Potential deal size (max 15)
        amount = float(lead.estimated_amount or 0)
        if amount > 500_000:
            deal_score, deal_detail = 15, 'свыше 500 000 ₽'
        elif amount > 200_000:
            deal_score, deal_detail = 10, 'свыше 200 000 ₽'
        elif amount > 50_000:
            deal_score, deal_detail = 5, 'свыше 50 000 ₽'
        elif amount > 0:
            deal_score, deal_detail = 2, f'{amount:,.0f} ₽'.replace(',', ' ')
        else:
            deal_score, deal_detail = 0, 'не указана'
        breakdown['deal_size'] = {
            'label': 'Размер сделки',
            'score': deal_score,
            'max': 15,
            'detail': deal_detail,
        }

        # Factor 5: Client response speed (max 15)
        if lead.response_speed_hours is not None:
            if lead.response_speed_hours < 1:
                response_score, response_detail = 15, 'менее 1 часа'
            elif lead.response_speed_hours < 24:
                response_score, response_detail = 10, 'менее 24 часов'
            else:
                response_score, response_detail = 3, 'более 24 часов'
        else:
            response_score, response_detail = 5, 'нет данных'
        breakdown['response_speed'] = {
            'label': 'Скорость ответа клиента',
            'score': response_score,
            'max': 15,
            'detail': response_detail,
        }

        total = sum(f['score'] for f in breakdown.values())
        total = min(100, max(0, total))
        return total, breakdown

    @staticmethod
    def get_priority(score: int) -> str:
        if score >= 75:
            return 'hot'
        elif score >= 40:
            return 'warm'
        return 'cold'

    @staticmethod
    def build_recommendation(lead, breakdown: dict) -> str:
        """Generate a human-readable AI recommendation text."""
        parts = []

        source_score = breakdown.get('source', {}).get('score', 0)
        if source_score >= 20:
            parts.append(f'Клиент пришёл по {lead.get_source_display().lower()}')

        activity_score = breakdown.get('activity', {}).get('score', 0)
        if activity_score >= 15:
            parts.append('проявляет высокую активность')
        elif activity_score >= 8:
            parts.append('есть первый контакт')

        response_score = breakdown.get('response_speed', {}).get('score', 0)
        if response_score >= 10:
            parts.append('быстро отвечает на сообщения')
        elif response_score <= 3:
            parts.append('медленно отвечает')

        deal_score = breakdown.get('deal_size', {}).get('score', 0)
        if deal_score >= 10:
            parts.append('крупная потенциальная сделка')

        warnings = []
        if breakdown.get('time', {}).get('score', 0) == 0:
            warnings.append('Лид ожидает более 24 часов — риск потери высокий.')
        if breakdown.get('activity', {}).get('score', 0) == 0:
            warnings.append('Нет взаимодействий с клиентом.')

        priority = lead.priority
        if priority == 'hot':
            action = 'Рекомендуем позвонить немедленно (в течение 15 минут).'
        elif priority == 'warm':
            action = 'Рекомендуем связаться в течение 2 часов.'
        else:
            action = 'Запланируйте контакт на сегодня-завтра.'

        intro = (', '.join(parts) + ' — высокая вероятность закрытия. ' if parts else '')
        warning_text = ' '.join(warnings) + ' ' if warnings else ''
        return f'{intro}{warning_text}{action}'.strip()

    def update_lead(self, lead, reason: str = 'data_change'):
        """Recalculate score, update lead fields, write to LeadScoreLog. Returns (score, breakdown)."""
        from .models import LeadScoreLog

        old_score = lead.score
        new_score, breakdown = self.calculate(lead)
        priority = self.get_priority(new_score)

        lead.score = new_score
        lead.priority = priority
        lead.score_updated_at = timezone.now()
        lead.save(update_fields=['score', 'priority', 'score_updated_at'])

        if old_score != new_score:
            LeadScoreLog.objects.create(
                lead=lead,
                score_before=old_score,
                score_after=new_score,
                reason=reason,
            )
        return new_score, breakdown
