from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    website = models.URLField(blank=True)
    cyberpoints = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class ScamReport(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('false_positive', 'False Positive'),
        ('duplicate', 'Duplicate'),
    ]
    
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scam_reports')
    url = models.URLField(max_length=500)
    element_text = models.TextField(blank=True)
    element_html = models.TextField(blank=True)
    reason = models.TextField()
    
    # AI Analysis
    ai_analysis = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)
    scam_type = models.CharField(max_length=100, blank=True)
    
    # Status
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending'
    )
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_reports'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Points and rewards
    points_earned = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Blocking feature fields
    is_blocked_by_reporter = models.BooleanField(default=True)
    last_visited = models.DateTimeField(null=True, blank=True)
    visit_attempts_after_report = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reported_by', '-created_at']),
            models.Index(fields=['url', 'reported_by']),
        ]
    
    def __str__(self):
        return f"Scam Report: {self.url[:50]} by {self.reported_by.username}"

class PointsHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_history')
    points = models.IntegerField()
    source = models.CharField(max_length=20, choices=[
        ('game', 'Game'),
        ('report', 'Scam Report')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# Automatically create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()