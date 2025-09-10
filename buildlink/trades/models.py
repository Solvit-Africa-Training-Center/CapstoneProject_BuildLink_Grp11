from django.conf import settings
from django.db import models

class Trade(models.Model):
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
