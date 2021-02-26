from django.db.models import Q
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.db.models.fields import Field
from django.db.models import Transform

import sal.plugin

@Field.register_lookup
class IntegerValue(Transform):
    # Register this before you filter things, for example in models.py
    lookup_name = 'int'  # Used as object.filter(LeftField__int__gte, "777")
    bilateral = True  # To cast both left and right

    def as_sql(self, compiler, connection):
        sql, params = compiler.compile(self.lhs)
        sql = 'CAST(%s AS INT)' % sql
        return sql, params

TITLES = {
    'ok': 'Batteries that are Healthy',
    'alert': 'Batteries that are not Healthy',
    'unknown': 'No battery information',
    'cycle_ok': 'Batteries with less than 300 cycles',
    'cycle_warning': 'Batteries with 300-500 cycles',
    'cycle_alert': 'Batteries with more than 500 cycles',
    'cycle_unknown': 'Machines with no battery cycle data'}
PLUGIN_Q = Q(pluginscriptsubmission__plugin='Battery')
SCRIPT_Q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_name='BatteryHealth')
CYCLE_Q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_name='CycleCount')
LAPTOPS_Q = Q(machine_model__contains='Book')


class BatteryStatus(sal.plugin.Widget):

    description = "Aggregate Battery Information"
    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        queryset = queryset.filter(os_family='Darwin')
        context = self.super_get_context(queryset, **kwargs)
        context['ok'] = self._filter(queryset, 'ok').count()
        context['alert'] = self._filter(queryset, 'alert').count()
        context['unknown'] = (
            queryset.filter(LAPTOPS_Q).count() - context['ok'] - context['alert'])
        context['cycle_ok_label'] = '< 300'
        context['cycle_warning_label'] = '300 - 500'
        context['cycle_alert_label'] = '500 +'
        context['cycle_unknown_label'] = 'No Data'
        context['cycle_ok'] = self._filter(queryset, 'cycle_ok').count()
        context['cycle_warning'] = self._filter(queryset, 'cycle_warning').count()
        context['cycle_alert'] = self._filter(queryset, 'cycle_alert').count()
        context['cycle_unknown'] = (
            queryset.filter(LAPTOPS_Q).count() - context['cycle_ok'] - context['cycle_alert'] - context['cycle_warning'])
        return context

    def filter(self, machines, data):
        if data not in TITLES:
            return None, None
        return self._filter(machines, data), TITLES[data]

    def _filter(self, machines, data):
        if data == 'ok':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        SCRIPT_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data='Healthy'))
        elif data == 'alert':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        SCRIPT_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data='Failing'))
        elif data == 'unknown':
            machines = (
                machines
                .filter(LAPTOPS_Q)
                .exclude(pk__in=self._filter(machines, 'ok').values('pk'))
                .exclude(pk__in=self._filter(machines, 'alert').values('pk')))
        elif data == 'cycle_ok':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        CYCLE_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data__int__lt=300))
        elif data == 'cycle_warning':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        CYCLE_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data__int__range=(300, 500))
        elif data == 'cycle_alert':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        CYCLE_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data__int__gt=500))
        elif data == 'cycle_unknown':
            machines = (
                machines
                .filter(LAPTOPS_Q)
                .exclude(pk__in=self._filter(machines, 'cycle_ok').values('pk'))
                .exclude(pk__in=self._filter(machines, 'cycle_warning').values('pk'))
                .exclude(pk__in=self._filter(machines, 'cycle_alert').values('pk')))
        else:
            machines = None

        return machines