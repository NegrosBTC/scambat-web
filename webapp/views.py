from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from urllib.parse import urlparse
import json
import time
import random
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from .forms import SignUpForm, UserUpdateForm, ProfileUpdateForm
from .ai.message_generator import ScamMessageGenerator
from .ai.explanation_analyzer import ExplanationAnalyzer
from .models import Profile, ScamReport, PointsHistory

# Initialize AI components
message_generator = None
explanation_analyzer = None

def get_ai_components():
    global message_generator, explanation_analyzer
    if message_generator is None:
        message_generator = ScamMessageGenerator()
    if explanation_analyzer is None:
        explanation_analyzer = ExplanationAnalyzer()
    return message_generator, explanation_analyzer

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'users/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'users/edit_profile.html', context)

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def game(request):
    return render(request, 'game/fraudhero.html')

class LeaderboardView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'leaderboard/leaderboard.html'
    context_object_name = 'leaders'
    paginate_by = 50
    login_url = 'login'

    def get_period_dates(self):
        now = timezone.now()
        if self.request.GET.get('period') == 'weekly':
            start_date = now - timedelta(days=now.weekday())
            return start_date, now
        elif self.request.GET.get('period') == 'monthly':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start_date, now
        return None, None

    def get_queryset(self):
        period = self.request.GET.get('period', 'all')
        
        if period in ['weekly', 'monthly']:
            start_date, _ = self.get_period_dates()
            
            # Get points from Scam Reports for this period
            scam_points = ScamReport.objects.filter(
                created_at__gte=start_date
            ).values('reported_by').annotate(
                points=Sum('points_earned')
            )
            
            # Get points from the game (assuming you have a model or way to track game points)
            game_points = PointsHistory.objects.filter(
                created_at__gte=start_date,
                source='game'
            ).values('user').annotate(
                points=Sum('points')
            )
            
            # Create a dictionary to store total points per user
            points_dict = {}
            
            # Add scam points to dictionary
            for entry in scam_points:
                user_id = entry['reported_by']
                points_dict[user_id] = points_dict.get(user_id, 0) + entry['points']
            
            # Add game points to dictionary
            for entry in game_points:
                user_id = entry['user']
                points_dict[user_id] = points_dict.get(user_id, 0) + entry['points']
            
            # Get all profiles and add their period points
            profiles = Profile.objects.select_related('user').all()
            for profile in profiles:
                profile.period_points = points_dict.get(profile.user.id, 0)
            
            # Sort and filter profiles
            profiles = sorted(profiles, key=lambda x: (x.period_points, x.cyberpoints), reverse=True)
            return [p for p in profiles if p.period_points > 0][:100]
        else:  # all-time
            profiles = Profile.objects.select_related('user').order_by('-cyberpoints')[:100]
            for profile in profiles:
                profile.period_points = profile.cyberpoints
            return profiles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        period = self.request.GET.get('period', 'all')
        
        if period in ['weekly', 'monthly']:
            start_date, _ = self.get_period_dates()
            
            # Get user's points for the period from all sources
            user_points = ScamReport.objects.filter(
                reported_by=user,
                created_at__gte=start_date
            ).aggregate(
                total=Sum('points_earned')
            )['total'] or 0
            
            # Calculate user's rank
            higher_points = ScamReport.objects.filter(
                created_at__gte=start_date
            ).values('reported_by').annotate(
                total=Sum('points_earned')
            ).filter(total__gt=user_points).count()
            
            user_rank = higher_points + 1
            
        else:  # all-time
            user_points = user.profile.cyberpoints
            user_rank = Profile.objects.filter(
                cyberpoints__gt=user.profile.cyberpoints
            ).count() + 1
        
        context.update({
            'active_period': period,
            'period_description': {
                'weekly': 'This Week',
                'monthly': 'This Month',
                'all': 'All Time'
            }.get(period, 'All Time'),
            'user_rank': user_rank,
            'user_period_points': user_points,
        })
        return context

class ReportHistoryView(LoginRequiredMixin, ListView):
    model = ScamReport
    template_name = 'reports/history.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        return ScamReport.objects.filter(
            reported_by=self.request.user
        ).select_related('reported_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        context['total_reports'] = queryset.count()
        context['blocked_sites'] = queryset.filter(is_blocked_by_reporter=True).count()
        context['total_points_earned'] = queryset.aggregate(
            total=Sum('points_earned')
        )['total'] or 0
        
        return context

class ToggleBlockView(LoginRequiredMixin, View):
    def post(self, request, report_id):
        report = get_object_or_404(ScamReport, id=report_id, reported_by=request.user)
        report.is_blocked_by_reporter = not report.is_blocked_by_reporter
        report.save()
        
        return JsonResponse({
            'success': True,
            'is_blocked': report.is_blocked_by_reporter
        })

def authenticate_token(token):
    """Helper function to authenticate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
        return user
    except:
        return None

@csrf_exempt
@require_http_methods(["POST"])
def check_url_status(request):
    """Check if a URL should be blocked for the current user"""
    try:
        data = json.loads(request.body)
        url = data.get('url')
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        user = authenticate_token(token)
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        # Parse the URL to get the domain
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Check if user has reported this URL/domain and wants it blocked
        report = ScamReport.objects.filter(
            Q(reported_by=user) & 
            (Q(url__icontains=domain) | Q(url=url)) &
            Q(is_blocked_by_reporter=True)
        ).first()
        
        if report:
            # Increment visit attempt counter
            report.visit_attempts_after_report += 1
            report.last_visited = timezone.now()
            report.save()
            
            return JsonResponse({
                'should_block': True,
                'report_id': report.id,
                'reason': report.reason,
                'reported_date': report.created_at.isoformat(),
                'visit_attempts': report.visit_attempts_after_report
            })
        
        return JsonResponse({'should_block': False})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Game-related views
@login_required
@csrf_exempt
def generate_game_message(request):
    """API endpoint to generate a new message for the game (fallback non-streaming version)"""
    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
                message_type = data.get('message_type', 'sms')
            except (json.JSONDecodeError, AttributeError):
                message_type = 'sms'
            
            msg_gen, _ = get_ai_components()
            
            is_scam = random.random() < 0.7
            
            message_data = msg_gen.generate_message(is_scam, message_type)
            
            return JsonResponse({
                'success': True,
                'message': message_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required
@csrf_exempt
def generate_game_message_stream(request):
    """API endpoint to generate a new message with streaming effect"""
    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
                message_type = data.get('message_type', 'sms')
            except (json.JSONDecodeError, AttributeError):
                message_type = 'sms'
            
            msg_gen, _ = get_ai_components()
            
            is_scam = random.random() < 0.7
            
            message_data = msg_gen.generate_message(is_scam, message_type)
            
            def generate_streaming_response():
                initial_data = {
                    'type': 'start',
                    'message_type': message_data['type'],
                    'is_scam': message_data['is_scam'],
                    'red_flags': message_data['red_flags']
                }
                
                if message_data['type'] == 'sms':
                    initial_data['phone_number'] = message_data['phone_number']
                else:
                    initial_data['sender_email'] = message_data['sender_email']
                    initial_data['sender_name'] = message_data['sender_name']
                    initial_data['subject'] = message_data['subject']
                
                yield f"data: {json.dumps(initial_data)}\n\n"
                
                text = message_data['text']
                for i, char in enumerate(text):
                    chunk_data = {
                        'type': 'text_chunk',
                        'char': char,
                        'position': i
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    time.sleep(0.03)
                
                completion_data = {
                    'type': 'complete',
                    'full_message': message_data
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
            
            response = StreamingHttpResponse(
                generate_streaming_response(),
                content_type='text/plain'
            )
            response['Cache-Control'] = 'no-cache'
            return response
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required
@csrf_exempt
def submit_game_answer(request):
    """API endpoint to submit and check answer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_thinks_scam = data.get('user_thinks_scam')
            user_explanation = data.get('explanation', '')
            actual_is_scam = data.get('actual_is_scam')
            message_text = data.get('message_text')
            red_flags = data.get('red_flags', [])
            current_score = data.get('current_score', 0)
            current_streak = data.get('current_streak', 0)
            
            _, analyzer = get_ai_components()
            
            is_correct = user_thinks_scam == actual_is_scam
            
            points = 0
            analysis = ""
            new_streak = current_streak
            
            if is_correct:
                new_streak = current_streak + 1
                if actual_is_scam and user_explanation:
                    result = analyzer.analyze_explanation(
                        user_explanation, 
                        red_flags, 
                        message_text
                    )
                    points = result['points']
                    analysis = result['analysis']
                elif not actual_is_scam:
                    points = 30
                    analysis = "Correct! This is a legitimate message."
                else:
                    points = 10
                    analysis = "Correct identification, but explanation would earn more points."
                
                if new_streak > 1:
                    streak_bonus = 5
                    points += streak_bonus
                    analysis += f" (Streak bonus: +{streak_bonus} points!)"
            else:
                new_streak = 0
                points = 0
                if actual_is_scam:
                    analysis = f"This was actually a scam. Red flags: {', '.join(red_flags)}"
                else:
                    analysis = "This was actually a legitimate message."
            
            session_total = current_score + points + (new_streak * 5)
            
            profile = request.user.profile
            profile.cyberpoints += points
            profile.save()
            
            return JsonResponse({
                'success': True,
                'is_correct': is_correct,
                'points': points,
                'analysis': analysis,
                'total_points': profile.cyberpoints,
                'session_total': session_total,
                'new_streak': new_streak
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

# Extension views
@csrf_exempt
def extension_auth(request):
    """Handle extension authentication with auto-connect support"""
    if request.method == 'POST':
        if request.user.is_authenticated:
            token = jwt.encode({
                'user_id': request.user.id,
                'username': request.user.username,
                'exp': datetime.utcnow() + timedelta(days=30)
            }, settings.SECRET_KEY, algorithm='HS256')
            
            return JsonResponse({
                'success': True,
                'token': token,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'cyberpoints': request.user.profile.cyberpoints
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    if request.user.is_authenticated:
        return render(request, 'extension/auth_success.html', {
            'user': request.user,
            'cyberpoints': request.user.profile.cyberpoints
        })
    else:
        return redirect(f'/login/?next={request.path}')

@csrf_exempt
def verify_extension_auth(request):
    """Verify extension auth token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'authenticated': False}, status=401)
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
        
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': user.id,
                'username': user.username,
            },
            'cyberpoints': user.profile.cyberpoints
        })
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
        return JsonResponse({'authenticated': False}, status=401)

@csrf_exempt
def report_scam_from_extension(request):
    """Handle scam reports from extension"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'success': False, 'error': 'Not authenticated', 'needsAuth': True}, status=401)
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Invalid token', 'needsAuth': True}, status=401)
    
    try:
        data = json.loads(request.body)
        
        # Create the report
        report = ScamReport.objects.create(
            reported_by=user,
            url=data.get('url', ''),
            element_text=data.get('element_text', ''),
            element_html=data.get('element_html', ''),
            reason=data.get('user_reason', ''),
            points_earned=10,  # Base points
            is_blocked_by_reporter=True  # Block by default
        )
        
        # Get AI analyzer
        _, analyzer = get_ai_components()
        
        # Analyze the reported content
        analysis_result = analyzer.analyze_web_content(
            element_text=data.get('element_text', ''),
            element_html=data.get('element_html', ''),
            user_reason=data.get('user_reason', ''),
            url=data.get('url', ''),
            context=data.get('context', {})
        )
        
        # Update report with analysis
        report.ai_analysis = analysis_result.get('explanation', '')
        report.confidence_score = analysis_result.get('confidence', 0.0)
        report.scam_type = ', '.join(analysis_result.get('indicators_found', []))[:100]
        
        # Determine points based on analysis
        points = 0
        if analysis_result['is_likely_scam']:
            if analysis_result['confidence'] >= 0.8:
                points = 50
            elif analysis_result['confidence'] >= 0.6:
                points = 30
            else:
                points = 20
        else:
            if len(data.get('user_reason', '')) > 50:
                points = 15
            else:
                points = 10
        
        report.points_earned = points
        report.save()
        
        # Update user points
        user.profile.cyberpoints += points
        user.profile.save()
        
        # Create success message
        if analysis_result['is_likely_scam']:
            message = f"Great catch! {analysis_result['explanation']}"
        else:
            message = "Thanks for your vigilance! While this might not be a scam, your contribution helps keep the web safe."
        
        return JsonResponse({
            'success': True,
            'points': points,
            'analysis': message,
            'total_points': user.profile.cyberpoints,
            'confidence': analysis_result['confidence'],
            'indicators_found': analysis_result.get('indicators_found', [])
        })
        
    except Exception as e:
        print(f"Error processing report: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Processing error: {str(e)}'
        }, status=500)