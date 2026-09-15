from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from program.models import *


@login_required
@csrf_exempt
def get_credit_levels_by_program_level(request):
    program_level_id = request.GET.get('program_level')
    credit_levels = list(
        ProgramLevelCreditMapping.objects
        .filter(program_level_id=program_level_id, status=1)
        .values_list('minimum_credits', flat=True)
    )
    return JsonResponse({'credit_levels': credit_levels})


@login_required
@csrf_exempt
def get_hods_by_school(request):
    school_id = request.GET.get('school')
    hods = User.objects.filter(
        is_active=1,
        id__in=BosCochairHODDeptMapping.objects.filter(
            school_id=school_id, is_active=1
        ).values_list('hod_id', flat=True)
    ).distinct().order_by('first_name')

    data = [
        {
            'id': h.id,
            'emp_id': h.emp_id,
            'first_name': h.first_name,
            'last_name': h.last_name,
            'campus': h.campus,
            'school_code': h.school_code,
            'dept_code': h.dept_code,
            'designation': h.designation,
        }
        for h in hods
    ]
    return JsonResponse({'hods': data})


@login_required
@csrf_exempt
def get_duration_exit_plan(request):
    program_level_id = request.GET.get('program_level')
    school_id = request.GET.get('school')
    mapping = ProgramSchoolDurationExitplanMapping.objects.filter(
        program_level_id=program_level_id, school_id=school_id, status=1
    ).first()
    if not mapping:
        return JsonResponse({'found': False})
    return JsonResponse({
        'found': True,
        'duration': mapping.duration,
        'exit_plan': bool(mapping.exit_plan),
    })


def get_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR')