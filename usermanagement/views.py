from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from usermanagement.models import *
from usermanagement.encryption_util import *
from datetime import datetime
from django.contrib.auth import authenticate, login as auth_login,logout
from django.contrib.auth.models import Group
from django.db.models import Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from usermanagement.utils import *
from django.db.models import Case, When, IntegerField, Sum
from django.http import JsonResponse
from collections import defaultdict
from .decorators import *

def get_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ipaddress = x_forwarded_for.split(',')[-1].strip()
    else:
        ipaddress = request.META.get('REMOTE_ADDR')
    return ipaddress



@login_required
def dashboard(request):
    template = ''
    context = {}
    if UserGroups.objects.filter(user_id=request.user.id, group__name__in=['BOSCO'], is_active=1).exists():
        template = 'dashboard/bosco.html'
        context = {

        }
    elif UserGroups.objects.filter(user_id=request.user.id, group__name__in=['BOSC'], is_active=1).exists():
        template = 'dashboard/bosc.html'
        context = {

        }
    elif UserGroups.objects.filter(user_id=request.user.id, group__name__in=['HOD'], is_active=1).exists():
        template = 'dashboard/hod.html'
        context = {

        }
    elif UserGroups.objects.filter(user_id=request.user.id, group__name__in=['ADMIN'], is_active=1).exists():
        template = 'dashboard/admin.html'
        context = {

        }
    return render(request, template, context)


def userlogout(request):
    UserAuthLogs.objects.filter(user_id=request.user.id, session_key=request.session.session_key).update(logout_time=datetime.now())
    logout(request)
    return redirect('/')


@login_required
def switch_role(request, group_id):
    group_id=decrypt(group_id)
    UserGroups.objects.filter(user_id=request.user.id).update(is_active=0)
    if UserGroups.objects.filter(user_id=request.user.id).exists():
        UserGroups.objects.filter(user_id=request.user.id, group_id=group_id).update(is_active=1)
    else:
        messages.error(request, "You don't have Permission to access this role")
    return redirect('/dashboard')


def not_found(request):
    return HttpResponse('Page not found')

def ulogin(request,emp_id):
    if User.objects.filter(username=emp_id).exists():
        user = User.objects.get(username=emp_id)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth_login(request, user)
        return redirect('/')
    else:
        return redirect('/')


