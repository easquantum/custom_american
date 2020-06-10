# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Latinux Inc (http://www.corvus.com.ve/) All Rights Reserved.
# 
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


import wizard
import netsvc
import pooler



period_form = '''<?xml version="1.0"?>
	<form string="Crear Periodos">
        <field name="part" required="True"/>
	</form> 
'''

period_fields = {
    'part':{
        'string':"Periodos",
        'type':'selection',
        'selection':[('1','Mensual'),('3','Trimestral')],
        'default': lambda *a:'1'
    },

}


def _do_period(self, cr, uid, data, context):
    pgy_obj = pooler.get_pool(cr.dbname).get('sale.commissionsyear')
    pgy = pgy_obj.browse(cr, uid, [data['id']])[0]

    interv = int(data['form']['part'])
    pgp = pgy.create_commissions_periods(context,interv)

    return {}

class commissions_period_by_year(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':period_form, 'fields':period_fields, 'state': [('end', 'Cancel','gtk-cancel'),('open', 'Create','gtk-ok')]}
		},
        'open': {
            'actions': [ _do_period ],
            'result': {'type': 'state', 'state': 'end'}
        }

	}
commissions_period_by_year("sale_commissions_period_year")