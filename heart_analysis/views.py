"""Heart analysis views."""
import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils.text import get_valid_filename

from .models import HeartSoundRecording, AnalysisRecord, PredictionResult
from .forms import AudioUploadForm
from .services import run_analysis
from core.models import AuditLog

logger = logging.getLogger(__name__)


def _log(request, action, description='', success=True):
    x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_fwd.split(',')[0].strip() if x_fwd else request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        user=request.user,
        action=action,
        description=description,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        success=success,
    )


@login_required
def upload_view(request):
    """Upload or record heart sound audio."""
    if request.method == 'POST':
        form = AudioUploadForm(request.POST, request.FILES)
        if form.is_valid():
            recording = form.save(commit=False)
            recording.user = request.user
            recording.original_filename = get_valid_filename(
                request.FILES['audio_file'].name
            )[:255]
            recording.file_size_bytes = request.FILES['audio_file'].size
            recording.source = 'upload'
            recording.save()

            # Create analysis record and run pipeline
            analysis = AnalysisRecord.objects.create(
                user=request.user,
                recording=recording,
                status='queued',
            )
            _log(request, 'upload', f'Recording {recording.id}')

            # Run synchronously (simple approach; use Celery for production)
            run_analysis(analysis)

            messages.success(request, 'Analysis complete! View your results below.')
            return redirect('heart_analysis:result', pk=analysis.id)
        else:
            messages.error(request, 'Upload failed. Please check the file and try again.')
    else:
        form = AudioUploadForm()

    return render(request, 'heart_analysis/upload.html', {'form': form})


@login_required
def browser_record_upload(request):
    """Accept a browser-recorded audio blob via AJAX POST."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    audio_data = request.FILES.get('audio_data')
    if not audio_data:
        return JsonResponse({'error': 'No audio data received'}, status=400)

    # Validate size
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 50 * 1024 * 1024)
    if audio_data.size > max_size:
        return JsonResponse({'error': 'Recording too large'}, status=400)

    from django.core.files.base import ContentFile
    import uuid

    # Detect extension from uploaded blob
    orig_name = getattr(audio_data, 'name', '') or ''
    ext = '.webm' if 'webm' in orig_name or 'webm' in getattr(audio_data, 'content_type', '') else '.wav'

    recording = HeartSoundRecording(
        user=request.user,
        original_filename=f'browser_recording{ext}',
        file_size_bytes=audio_data.size,
        source='browser',
        status='pending',
    )
    recording.audio_file.save(f'browser_{uuid.uuid4().hex}{ext}', audio_data, save=False)
    recording.save()

    analysis = AnalysisRecord.objects.create(
        user=request.user,
        recording=recording,
        status='queued',
    )
    _log(request, 'upload', f'Browser recording {recording.id}')
    run_analysis(analysis)

    return JsonResponse({'redirect_url': f'/analysis/{analysis.id}/'})


@login_required
def result_view(request, pk):
    """Display prediction results for a completed analysis."""
    analysis = AnalysisRecord.objects.filter(pk=pk).first()
    if analysis is None:
        messages.info(
            request,
            'This analysis is no longer available. Your analysis history is shown instead.',
        )
        return redirect('heart_analysis:history')
    if analysis.user_id != request.user.id:
        raise Http404

    prediction = getattr(analysis, 'prediction', None)

    context = {
        'analysis': analysis,
        'recording': analysis.recording,
        'prediction': prediction,
        'waveform_url': analysis.waveform_image.url if analysis.waveform_image else None,
        'spectrogram_url': analysis.spectrogram_image.url if analysis.spectrogram_image else None,
        'model_unavailable': (analysis.status == 'model_unavailable'),
    }
    return render(request, 'heart_analysis/result.html', context)


@login_required
def history_view(request):
    """List the user's analysis history."""
    analyses_qs = AnalysisRecord.objects.filter(user=request.user).select_related(
        'recording', 'prediction'
    )
    paginator = Paginator(analyses_qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'heart_analysis/history.html', {
        'page_obj': page_obj,
        'total_analyses': analyses_qs.count(),
    })


@login_required
def detail_view(request, pk):
    """Detailed view of a single analysis record."""
    analysis = get_object_or_404(AnalysisRecord, pk=pk, user=request.user)
    return redirect('heart_analysis:result', pk=pk)


@login_required
@require_POST
def delete_recording(request, pk):
    """Allow user to delete their own recording and analysis."""
    recording = get_object_or_404(HeartSoundRecording, pk=pk, user=request.user)
    _log(request, 'delete', f'Recording {recording.id}')
    recording.delete()
    messages.success(request, 'Recording and associated analysis deleted.')
    return redirect('heart_analysis:history')
