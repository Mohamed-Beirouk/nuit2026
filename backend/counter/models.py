from django.db import models


class Counter(models.Model):
    """Single row (pk=1) holding the last number handed out. Starts at 0."""

    value = models.PositiveIntegerField(default=0)


class Claim(models.Model):
    name = models.CharField(max_length=80)
    number = models.PositiveIntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} {self.name}"
