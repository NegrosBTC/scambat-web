from django.contrib import admin
from .models import Profile, ScamReport

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'cyberpoints', 'location']
    search_fields = ['user__username', 'user__email']
    list_filter = ['location']

@admin.register(ScamReport)
class ScamReportAdmin(admin.ModelAdmin):
    list_display = ['reported_by', 'url', 'points_earned', 'verification_status', 'created_at']
    list_filter = ['verification_status', 'is_blocked_by_reporter', 'created_at']
    search_fields = ['url', 'reason', 'reported_by__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Info', {
            'fields': ('reported_by', 'url', 'reason', 'element_text')
        }),
        ('AI Analysis', {
            'fields': ('ai_analysis', 'confidence_score', 'scam_type')
        }),
        ('Status', {
            'fields': ('verification_status', 'verified_by', 'verified_at', 'points_earned')
        }),
        ('Blocking', {
            'fields': ('is_blocked_by_reporter', 'visit_attempts_after_report', 'last_visited')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )