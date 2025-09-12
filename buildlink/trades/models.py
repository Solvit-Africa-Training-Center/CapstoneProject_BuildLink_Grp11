from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

class Trade(models.Model):
    class ChooseTrade(models.TextChoices):
        PLUMBER = 'plumber', _('Plumber')
        ELECTRICIAN = 'electrician', _('Electrician')
        CARPENTER = 'carpenter', _('Carpenter')
        PAINTER = 'painter', _('Painter')
        MASON = 'mason', _('Mason')
        ROOFER = 'roofer',_('Roofer')
        OTHER = 'other', _('Other')
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class WorkerTrade(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ This dynamically links to the custom User model
        on_delete=models.CASCADE,
        related_name="worker_trades"
    )
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name="workers")

    class Meta:
        unique_together = ('user', 'trade')

    def __str__(self):
        return f"{self.user.username} - {self.trade.name}"


# Create your models here.
