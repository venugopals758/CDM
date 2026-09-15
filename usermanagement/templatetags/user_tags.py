from django import template
register = template.Library()
from usermanagement.models import *
from usermanagement.encryption_util import *
from datetime import datetime


@register.simple_tag
def get_group_data(user_id):
    user_roles=UserGroups.objects.filter(user_id=user_id).values('group__name','role','is_active','group_id').order_by('-is_active')
    for i in user_roles:
        i['enc_group_id']=encrypt(i['group_id'])
    return user_roles

@register.filter(name='has_group')
def has_group(user, group_name):
    return UserGroups.objects.filter(user_id=user.id,group__name=group_name,is_active=1).exists()


@register.filter(name='has_groups')
def has_groups(user, group_name):
    group_names=group_name.split(',')
    return UserGroups.objects.filter(group__name__in=group_names,is_active=1,user_id=user.id).exists()


