from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from usermanagement.decorators import group_required
from usermanagement.encryption_util import encrypt, decrypt
from program.models import *
from program.forms import get_course_structure_context, get_program_outcomes_context


@login_required
@group_required('BOSCO', 'BOSC', 'HOD', 'DOAA')
def program_details(request, id):
    dec_id = decrypt(id)
    program = Programs.objects.filter(id=dec_id).first()
    if not program:
        return redirect('/programs')

    course_structure_context = get_course_structure_context(program)
    program_outcomes_context = get_program_outcomes_context(program)

    tracking_status = ProgramTrackingStatus.objects.filter(program=program).order_by('-id').values(
        'created', 'description', 'campus', 'institution', 'department', 'designation', 'emp_id',
        'user__first_name', 'user__last_name', 'program_status__name', 'group__name',
    )

    pending_group_name = None
    # DoAA is assigned a single default user internally (Programs.pending_at is a single
    # FK), but that specific person is never named in the UI - it always just reads
    # "Pending at DoAA" for this group.
    is_pending_doaa = False
    if program.pending_at_id:
        pending_mapping = ProgramTrackingUserMapping.objects.filter(
            programs_id=program.id, to_user_id=program.pending_at_id
        ).select_related('to_user_group').order_by('-id').first()
        if pending_mapping:
            pending_group_name = pending_mapping.to_user_group.name
            is_pending_doaa = pending_mapping.to_user_group.name == 'DOAA'

    groups = UserGroups.objects.filter(
        user_id=request.user.id, is_active=1, is_block=0
    ).values_list('group__name', flat=True)

    course_requests = CourseRequest.objects.filter(program=program).select_related(
        'department', 'request_status', 'raised_by', 'pending_at'
    ).order_by('-created')
    for cr in course_requests:
        cr.timeline = cr.tracking_status.select_related('request_status', 'user').order_by('created')
        cr.enc_id = encrypt(cr.id)
        cr.can_delete = (
            cr.raised_by_id == request.user.id and program.program_status_id == 3
            and cr.request_status_id not in (3, 7)  # not already initiated or cancelled
        )
        cr.is_pending_here = cr.pending_at_id == request.user.id

    program_status = ProgramStatus.objects.all()
    template = ''
    if 'BOSCO' in groups:
        template = 'program/bosco/program_details.html'
        last_record = ProgramTrackingUserMapping.objects.filter(
                        programs_id=dec_id, to_user_id=request.user.id,
                        to_user_group_id=2, is_edit=1
                    )
        if last_record.filter(program_tracking_status__program_status_id=4).exists():
            program_status = program_status.filter(id__in=[2])
        else:
            program_status = program_status.none()
    elif 'BOSC' in groups:
        template = 'program/bosc/program_details.html'
        last_record = ProgramTrackingUserMapping.objects.filter(
                        programs_id=dec_id, to_user_id=request.user.id,
                        to_user_group_id=1, is_edit=1
                    )
        if last_record.filter(program_tracking_status__program_status_id=2).exists():
            program_status = program_status.filter(id__in=[3, 4])
        elif last_record.filter(program_tracking_status__program_status_id=7).exists():
            program_status = program_status.filter(id__in=[8])  # Recommend Programme in BoS Meeting
        else:
            program_status = program_status.none()
    elif 'DOAA' in groups:
        template = 'program/doaa/program_details.html'
        program_status = program_status.none()
    hod_department = None
    course_requests_pending = False
    if 'HOD' in groups:
        template = 'program/hod/program_details.html'
        hod_mapping = BosCochairHODDeptMapping.objects.filter(
            hod_id=request.user.id, is_active=1
        ).select_related('dept').first()
        hod_department = hod_mapping.dept if hod_mapping else None

        # Forward/Action stays hidden until every course request raised for this program
        # has been resolved (pending_at cleared - either initiated or cancelled).
        course_requests_pending = course_requests.filter(pending_at__isnull=False).exists()
        program_status = ProgramStatus.objects.filter(id=7)  # Program Head Curriculum Submitted

    forward_access = False
    user_group = UserGroups.objects.filter(user_id=request.user.id, is_active=1).first()
    if user_group and ProgramTrackingUserMapping.objects.filter(
        programs_id=dec_id, to_user_id=request.user.id,
        to_user_group_id=user_group.group_id, is_edit=1
    ).exists() and program.pending_at_id == request.user.id:
        forward_access = True

    context = {
        'program': program,
        'enc_program_id': id,
        'tracking_status': tracking_status,
        **course_structure_context,
        **program_outcomes_context,
        'pending_group_name': pending_group_name,
        'is_pending_doaa': is_pending_doaa,
        'forward_access': forward_access,
        'program_status': program_status,
        'hod_department': hod_department,
        'departments': Departments.objects.filter(status=1).exclude(
            id=hod_department.id if hod_department else None
        ).order_by('name'),
        'course_requests': course_requests,
        'course_requests_pending': course_requests_pending,
    }
    return render(request, template, context)
