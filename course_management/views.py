import json

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from usermanagement.decorators import group_required
from usermanagement.encryption_util import encrypt, decrypt
from usermanagement.models import User
from program.models import ProgramLevel, Programs
from .models import (
    Course, CourseHeader, CourseType, CourseCategory, DepartmentInstituteCodes, CourseLevels,
    CourseProposedPrograms, CourseUnits, CourseSyllabus, CourseSyllabusTopicsMapping,
    CourseSyllabusPractical, SyllabusType, CourseBooks, References, CourseCoPoPso,
)


@login_required
@group_required('BOSCO')
def courses(request):
    course_list = Course.objects.filter(
        created_by=request.user, is_delete=False,
    ).select_related(
        'course_type', 'level_of_course', 'program', 'created_by',
    ).order_by('-created')

    for c in course_list:
        c.enc_id = encrypt(c.id)

    return render(request, 'course_management/courses.html', {'courses': course_list})


@login_required
@group_required('BOSCO')
def check_course_code(request):
    course_code = request.POST.get('course_code')
    course_id = request.POST.get('course_id')
    qs = Course.objects.filter(course_code=course_code)
    if course_id:
        qs = qs.exclude(id=course_id)
    return JsonResponse({'is_exists': qs.exists()})


@login_required
@group_required('BOSCO')
def get_levels_by_ptype(request):
    program_type = request.POST.get('program_type')
    levels = CourseLevels.objects.filter(status=1, program_level_id=program_type).values('id', 'level')
    return JsonResponse(list(levels), safe=False)


def _save_about_the_course(request, course):
    post = request.POST

    if course is None:
        course = Course(created_by=request.user)
        course.course_header = CourseHeader.objects.create(user=request.user)

    course.modified_by = request.user
    course.course_name = post.get('course_title')
    course.course_type_id = post.get('type_of_course') or None
    course.course_code_exists = post.get('course_code_exists') == '1'
    course.course_code = post.get('course_code') or None
    course.program_type_id = post.get('program_type') or None
    course.dept_code_id = post.get('dept_inst') or None
    course.pass_fail = post.get('pass_fail') == '1'
    course.mode_of_delivery = ','.join(post.getlist('faculty'))
    course.course_category_id = post.get('course_category_id') or None

    course.L = post.get('L') or None
    course.T = post.get('T') or None
    course.P = post.get('P') or None
    course.S = post.get('S') or None
    course.J = post.get('J') or None
    course.C = post.get('C') or None
    course.total_no_of_contact_hours = post.get('total_hours') or None
    course.L_hours = post.get('l_hours') or None
    course.T_hours = post.get('t_hours') or None
    course.P_hours = post.get('p_hours') or None
    course.S_hours = post.get('s_hours') or None
    course.J_hours = post.get('j_hours') or None

    course.course_descrption = post.get('course_description')
    course.level_of_course_id = post.get('level_of_course') or None
    course.alternative_exposure = post.get('alt_exposure')

    course.pre_requisites = post.get('pre_requisites') == '1'
    course.pre_requisites_codes = post.get('pre_requisites_codes')
    course.co_requisites = post.get('co_requisites') == '1'
    course.co_requisites_codes = post.get('co_requisites_codes')
    course.anti_requisites = post.get('anti_requisites') == '1'
    course.anti_requisites_codes = post.get('anti_requisites_codes')

    course.course_objectives = [
        v for v in post.getlist('course_objectives') + post.getlist('course_objectives_optional')
        if v.strip()
    ]
    course.course_outcome = [
        v for v in post.getlist('course_outcome') + post.getlist('course_outcome_optional')
        if v.strip()
    ]
    course.sdg = [int(v) for v in post.getlist('sdg')]
    course.sdg_description = post.get('sdg_description')

    course.active_step = max(course.active_step or 1, 2)
    course.save()
    return course


def _save_syllabus(request, course):
    post = request.POST

    CourseProposedPrograms.objects.filter(course=course).delete()
    for row in json.loads(post.get('proposed_programs_json') or '[]'):
        CourseProposedPrograms.objects.create(
            course=course,
            program_name=row.get('program_ids') or [],
            branch_code=row.get('program_codes') or [],
            pos=row.get('pos') or None,
            psos=row.get('psos') or None,
        )

    # Deleting the unit cascades to its CourseSyllabus row, which cascades to its sub-unit rows.
    CourseUnits.objects.filter(course=course).delete()
    for unit_no, unit in enumerate(json.loads(post.get('units_json') or '[]'), start=1):
        course_unit = CourseUnits.objects.create(course=course, unit_no=unit_no)
        syllabus = CourseSyllabus.objects.create(
            course=course,
            course_unit=course_unit,
            unit_name=unit.get('title'),
            number_of_contact_hours=unit.get('hours') or None,
            created_by=request.user,
        )
        for sub in unit.get('subunits', []):
            if not (sub.get('title') or '').strip():
                continue
            CourseSyllabusTopicsMapping.objects.create(
                course_syllabus=syllabus,
                title=sub.get('title'),
                duration=sub.get('duration') or None,
            )

    practical_type, _ = SyllabusType.objects.get_or_create(name='Practical')
    CourseSyllabusPractical.objects.filter(course=course, syllabus_type=practical_type).delete()
    for p in json.loads(post.get('practicals_json') or '[]'):
        if not (p.get('topic') or '').strip():
            continue
        CourseSyllabusPractical.objects.create(
            course=course,
            syllabus_type=practical_type,
            topic=p.get('topic'),
            user=request.user,
        )

    course.active_step = max(course.active_step or 1, 3)
    course.save()
    return course


def _syllabus_context(course):
    proposed_programs = []
    units = []
    practicals = []
    if course:
        for pp in CourseProposedPrograms.objects.filter(course=course):
            proposed_programs.append({
                'program_ids': pp.program_name or [],
                'program_codes': pp.branch_code or [],
                'pos': pp.pos,
                'psos': pp.psos,
            })
        for course_unit in CourseUnits.objects.filter(course=course).order_by('unit_no'):
            syllabus = CourseSyllabus.objects.filter(course_unit=course_unit).first()
            units.append({
                'title': syllabus.unit_name if syllabus else '',
                'hours': syllabus.number_of_contact_hours if syllabus else '',
                'subunits': [
                    {'title': t.title, 'duration': t.duration}
                    for t in CourseSyllabusTopicsMapping.objects.filter(course_syllabus=syllabus)
                ] if syllabus else [],
            })
        practical_type = SyllabusType.objects.filter(name='Practical').first()
        if practical_type:
            practicals = [
                {'topic': p.topic}
                for p in CourseSyllabusPractical.objects.filter(course=course, syllabus_type=practical_type)
            ]
    programs_options = [
        {'id': p.id, 'title': p.title} for p in Programs.objects.filter(status=1)
    ]
    return {
        'programs_options_json': json.dumps(programs_options),
        'proposed_programs_json': json.dumps(proposed_programs),
        'units_json': json.dumps(units),
        'practicals_json': json.dumps(practicals),
    }


def _save_bibliography(request, course):
    post = request.POST

    CourseBooks.objects.filter(course=course).delete()
    for row in json.loads(post.get('text_books_json') or '[]'):
        if not (row.get('title') or '').strip():
            continue
        CourseBooks.objects.create(
            course=course,
            created_by=request.user,
            author=row.get('author'),
            title=row.get('title'),
            edition=row.get('edition'),
            publisher=row.get('publisher'),
            place_of_publication=row.get('place_of_publication'),
            isbn=row.get('isbn'),
            year=row.get('year') or None,
        )

    References.objects.filter(course=course).delete()
    for row in json.loads(post.get('references_json') or '[]'):
        if not (row.get('title') or '').strip():
            continue
        References.objects.create(
            course=course,
            created_by=request.user,
            author=row.get('author'),
            title=row.get('title'),
            edition=row.get('edition'),
            publisher=row.get('publisher'),
            place_of_publication=row.get('place_of_publication'),
            isbn=row.get('isbn'),
            year=row.get('year') or None,
            url=row.get('url'),
        )

    course.active_step = max(course.active_step or 1, 4)
    course.save()
    return course


def _bibliography_context(course):
    text_books = []
    references = []
    if course:
        text_books = [
            {
                'author': b.author, 'title': b.title, 'edition': b.edition,
                'publisher': b.publisher, 'place_of_publication': b.place_of_publication,
                'isbn': b.isbn, 'year': b.year,
            }
            for b in CourseBooks.objects.filter(course=course)
        ]
        references = [
            {
                'author': r.author, 'title': r.title, 'edition': r.edition,
                'publisher': r.publisher, 'place_of_publication': r.place_of_publication,
                'isbn': r.isbn, 'year': r.year, 'url': r.url,
            }
            for r in References.objects.filter(course=course)
        ]
    return {
        'text_books_json': json.dumps(text_books),
        'references_json': json.dumps(references),
    }


def _save_copo(request, course):
    post = request.POST

    CourseCoPoPso.objects.filter(course=course).delete()
    for entry in json.loads(post.get('copo_json') or '[]'):
        proposed_program = CourseProposedPrograms.objects.filter(
            id=entry.get('proposed_program_id'), course=course
        ).first()
        for row in entry.get('rows', []):
            CourseCoPoPso.objects.create(
                course=course,
                proposed_program=proposed_program,
                co=row.get('co'),
                po=row.get('po') or [],
                pso=row.get('pso') or [],
                user=request.user,
            )

    course.regulations = post.get('regulations')
    course.bos_date = post.get('bos_date') or None
    course.ac_council_number = post.get('ac_council_number') or None
    course.ac_council_date = post.get('ac_council_date') or None
    course.active_step = max(course.active_step or 1, 5)
    course.save()
    return course


def _copo_context(course):
    course_outcomes = course.course_outcome if course and course.course_outcome else []
    proposed_programs = []
    if course:
        for pp in CourseProposedPrograms.objects.filter(course=course):
            titles = [p.title for p in Programs.objects.filter(id__in=pp.program_name or [])]
            existing_rows = {}
            for row in CourseCoPoPso.objects.filter(course=course, proposed_program=pp):
                existing_rows[row.co] = {'po': row.po or [], 'pso': row.pso or []}
            proposed_programs.append({
                'id': pp.id,
                'title': ' / '.join(titles),
                'pos': pp.pos or 0,
                'psos': pp.psos or 0,
                'rows': existing_rows,
            })
    return {
        'course_outcomes_json': json.dumps(course_outcomes),
        'proposed_programs_display_json': json.dumps(proposed_programs),
    }


def _wizard_context(course, request_user):
    context = {
        'course': course,
        'course_details': course,
        'new_objectives': range(1, 5),
        'new_outcomes': range(1, 5),
        'course_type': CourseType.objects.filter(status=1).values('id', 'name'),
        'course_category': CourseCategory.objects.filter(status=1),
        'program_type': ProgramLevel.objects.filter(status=1).values('id', 'name'),
        'dept': DepartmentInstituteCodes.objects.filter(status=1),
        'course_levels': CourseLevels.objects.filter(status=1),
        'users': User.objects.filter(Q(is_active=1), ~Q(id=request_user.id)).exclude(
            groups__name__in=['GUEST', 'ADMIN', 'HOD', 'HOI']
        ),
        'sdg': range(1, 18),
        'selected_sdg': course.sdg if course and course.sdg else [],
        'mode_of_delivery': course.mode_of_delivery.split(',') if course and course.mode_of_delivery else [],
        'enc_course_id': encrypt(course.id) if course else '',
    }
    context.update(_syllabus_context(course))
    context.update(_bibliography_context(course))
    context.update(_copo_context(course))
    return context


@login_required
@group_required('BOSCO')
def create_course(request, id=None):
    course = None
    if id:
        course = get_object_or_404(Course, id=decrypt(id))

    if request.method == 'POST':
        step = request.POST.get('step')
        if step == '1':
            course = _save_about_the_course(request, course)
        elif step == '2':
            course = _save_syllabus(request, course)
        elif step == '3':
            course = _save_bibliography(request, course)
        elif step == '4':
            course = _save_copo(request, course)
        return redirect('edit_course', id=encrypt(course.id))

    return render(request, 'course_management/forms/form_base.html', _wizard_context(course, request.user))


@login_required
@group_required('BOSCO')
def course_details(request, id):
    course = get_object_or_404(Course, id=decrypt(id), created_by=request.user)
    return render(request, 'course_management/forms/form_base.html', _wizard_context(course, request.user))
