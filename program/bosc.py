from django.db.models import Q, Case, When, Value, IntegerField
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group
from django.contrib import messages
from django.shortcuts import render, redirect
from usermanagement.decorators import group_required
from usermanagement.encryption_util import encrypt, decrypt
from usermanagement.models import ErrorLogs
from program.models import *
from datetime import datetime


@login_required
@group_required('BOSC')
def programs(request):
    involved_program_ids = ProgramTrackingUserMapping.objects.filter(
        Q(to_user_id=request.user.id) | Q(user_id=request.user.id)
    ).values_list('programs_id', flat=True)

    base_qs = Programs.objects.select_related(
        'program_type', 'program_level', 'program_batch', 'program_status', 'pending_at',
    ).filter(
        Q(id__in=involved_program_ids) | Q(created_by_id=request.user.id)
    ).distinct()

    program_list = base_qs.annotate(
        is_pending_here=Case(
            When(pending_at_id=request.user.id, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('is_pending_here', '-created_at')

    for p in program_list:
        p.enc_id = encrypt(p.id)
        p.is_pending_here = p.pending_at_id == request.user.id
        p.pending_is_doaa = bool(p.pending_at_id) and UserGroups.objects.filter(
            user_id=p.pending_at_id, group_id=7, is_active=1, is_block=0
        ).exists()

    context = {
        'programs': program_list,
        'total_count': base_qs.count(),
        'pending_count': base_qs.filter(pending_at_id=request.user.id, program_status_id=2).count(),
    }
    return render(request, 'program/bosc/programs.html', context)


@login_required
@csrf_exempt
@group_required('BOSC')
def bosc_forward_program(request, id):
    if request.method == "POST":
        status = request.POST.get('status')
        description = request.POST.get('comments')
        program_id = decrypt(id)
        try:
            program = Programs.objects.get(id=program_id)
        except Programs.DoesNotExist:
            messages.error(request, 'Program not found.')
            return redirect('/programs')

        try:
            if not ProgramTrackingUserMapping.objects.filter(
                to_user_id=request.user.id, programs_id=program_id,
                to_user_group_id=1, is_edit=1
            ).exists():
                messages.error(request, 'You do not have permission to forward this program.')
                return redirect('/programs')

            tracking_status = ProgramTrackingStatus.objects.create(
                                description=description,
                                program_id=program_id,
                                program_status_id=int(status),
                                user_id=request.user.id,
                                group_id=1,
                                campus=request.user.campus,
                                institution=request.user.school_code,
                                department=request.user.dept_code,
                                designation=request.user.designation,
                                emp_id=request.user.emp_id,
                                created=datetime.now(),
                            )
            if status == '3':
                to_user_id = program.program_head_id
                to_user_group_id = 5

                ProgramTrackingUserMapping.objects.create(
                    programs_id=program_id,
                    program_tracking_status=tracking_status,
                    to_user_id=to_user_id,
                    to_user_group_id=to_user_group_id,
                    user_id=request.user.id,
                    is_edit=1,
                )

                Programs.objects.filter(id=program.id).update(
                    program_status_id=3, pending_at_id=to_user_id
                )
            elif status == '4':
                to_user_id = program.created_by_id
                to_user_group_id = Group.objects.filter(name='BOSCO').values_list('id', flat=True).first()

                ProgramTrackingUserMapping.objects.create(
                                    programs_id=program_id,
                                    program_tracking_status=tracking_status,
                                    to_user_id=to_user_id,
                                    to_user_group_id=to_user_group_id,
                                    user_id=request.user.id,
                                    is_edit=1,
                                )

                Programs.objects.filter(id=program.id).update(
                    program_status_id=4, pending_at_id=to_user_id
                )
            elif status == '8':
                to_user_id = UserGroups.objects.filter(
                    group_id=7, is_active=1, is_block=0  # DOAA
                ).values_list('user_id', flat=True).first()
                to_user_group_id = 7  # DOAA

                ProgramTrackingUserMapping.objects.create(
                    programs_id=program_id,
                    program_tracking_status=tracking_status,
                    to_user_id=to_user_id,
                    to_user_group_id=to_user_group_id,
                    user_id=request.user.id,
                    is_edit=1,
                )

                Programs.objects.filter(id=program.id).update(
                    program_status_id=8, pending_at_id=to_user_id
                )

            ProgramTrackingUserMapping.objects.filter(
                                            to_user_id=request.user.id,
                                            programs_id=program_id,
                                            to_user_group_id=1,
                                            is_edit=1,
                                        ).update(is_edit=0)

            messages.success(request, 'Submitted Successfully')
            return redirect('/programs')
        except Exception as e:
            ErrorLogs.objects.create(log=str(e), user_id=request.user.id, info=request.POST)
            return redirect('/user/not_found')
    else:
        return redirect('/')
