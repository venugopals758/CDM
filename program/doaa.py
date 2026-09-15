from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from usermanagement.decorators import group_required
from usermanagement.encryption_util import encrypt
from program.models import *


@login_required
@group_required('DOAA')
def programs(request):
    involved_program_ids = ProgramTrackingUserMapping.objects.filter(
        Q(to_user_id=request.user.id) | Q(user_id=request.user.id)
    ).values_list('programs_id', flat=True)

    base_qs = Programs.objects.select_related(
        'program_type', 'program_level', 'program_batch', 'program_status', 'pending_at',
    ).filter(id__in=involved_program_ids).distinct()

    program_list = base_qs.order_by('-created_at')
    for p in program_list:
        p.enc_id = encrypt(p.id)
        p.is_pending_here = p.pending_at_id == request.user.id
        p.pending_is_doaa = bool(p.pending_at_id) and UserGroups.objects.filter(
            user_id=p.pending_at_id, group_id=7, is_active=1, is_block=0
        ).exists()

    context = {
        'programs': program_list,
        'total_count': base_qs.count(),
        'pending_count': base_qs.filter(pending_at_id=request.user.id).count(),
    }
    return render(request, 'program/doaa/programs.html', context)
