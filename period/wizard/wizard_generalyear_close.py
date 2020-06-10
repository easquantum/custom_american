# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Latinux Inc (http://www.latinux.com/) All Rights Reserved.
#                    Javier Duran <jduran@corvus.com.ve>
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
import osv
import pooler
from tools.translate import _

_transaction_form = '''<?xml version="1.0"?>
<form string="Close states of general year and periods">
    <field name="gy_id"/>
    <separator string="Are you sure you want to close the general year ?" colspan="4"/>
    <field name="sure"/>
</form>'''

_transaction_fields = {
    'gy_id': {'string':'General Year to close', 'type':'many2one', 'relation': 'period.generalyear','required':True, 'domain':[('state','=','draft')]},
    'sure': {'string':'Check this box', 'type':'boolean'},
}

def _data_save(self, cr, uid, data, context):
    if not data['form']['sure']:
        raise wizard.except_wizard(_('UserError'), _('Closing of states cancelled, please check the box !'))
    pool = pooler.get_pool(cr.dbname)

    gy_id = data['form']['gy_id']

    cr.execute('UPDATE period_generalperiod SET state = %s ' \
            'WHERE generalyear_id = %s', ('done',gy_id))
    cr.execute('UPDATE period_generalyear ' \
            'SET state = %s WHERE id = %s', ('done', gy_id))
    return {}

class wiz_genperiod_close_state(wizard.interface):
    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form', 'arch':_transaction_form, 'fields':_transaction_fields, 'state':[('end','Cancel'),('close','Close states')]}
        },
        'close': {
            'actions': [_data_save],
            'result': {'type': 'state', 'state':'end'}
        }
    }
wiz_genperiod_close_state('period.genyear.close')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

