from django.db.models import Q
from django.db.models.fields import Field
from django.db.models import Transform

import sal.plugin


@Field.register_lookup
class FloatValue(Transform):
    # Register this before you filter things, for example in models.py
    lookup_name = 'float'  # Used as object.filter(LeftField__int__gte, "777")
    bilateral = True  # To cast both left and right

    def as_sql(self, compiler, connection):
        sql, params = compiler.compile(self.lhs)
        sql = 'CAST(%s AS FLOAT)' % sql
        return sql, params


# Build some Q objects for use later.
ALERT_RANGE = list(range(0, 90))
DATA = 'pluginscriptsubmission__pluginscriptrow__pluginscript_data__in={}'
ALERT_Q = eval('Q({})'.format(DATA.format(ALERT_RANGE)))
OK_Q = eval('Q({})'.format(DATA.format(ALERT_RANGE[0:30])))
WARNING_Q = eval('Q({})'.format(DATA.format(ALERT_RANGE[30:60])))

PLUGIN_Q = Q(pluginscriptsubmission__plugin='Uptime',
             pluginscriptsubmission__pluginscriptrow__pluginscript_name='UptimeDays')
TITLES = {
    'ok': 'Machines with less than 7 days of uptime',
    'warning': 'Machines with less than 30 days of uptime',
    'alert': 'Machines with more than 30 days of uptime'}


class SISUptime(sal.plugin.Widget):

    description = 'Current uptime'
    template = 'plugins/traffic_lights.html'
    
    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)

        context['ok_count'] = self._filter(queryset, 'ok').count()
        context['warning_count'] = self._filter(queryset, 'warning').count()
        context['alert_count'] = self._filter(queryset, 'alert').count()
        context.update({
            'ok_label': '< 8 Days',
            'warning_label': '8-30 Days',
            'alert_label': '30 Days +',
        })
        return context

    def _filter(self, queryset, data):
        if data == 'ok':
            queryset = queryset.filter(PLUGIN_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data__float__lt=8)
        elif data == 'warning':
            queryset = queryset.filter(PLUGIN_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data__float__range=(8, 30))
        elif data == 'alert':
            queryset = queryset.filter(PLUGIN_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data__float__gt=30)
        return queryset

    def filter(self, machines, data):
        try:
            title = TITLES[data]
        except KeyError:
            return None, None

        machines = self._filter(machines, data)

        return machines, title
