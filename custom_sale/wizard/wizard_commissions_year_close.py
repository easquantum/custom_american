# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Latinux Inc (http://www.latinux.com/) All Rights Reserved.
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
<form string="Cierre Anual de Commisiones y periodos">
    <separator string="Si esta seguro de efectuar el cierre anual de commisiones, marque la casilla ?" colspan="4"/>
    <field name="sure"/>
</form>'''

_transaction_fields = {
    'sure': {'string':'Marque esta casilla', 'type':'boolean'},
}

def _check_data(self, cr, uid, data, context):
    obj_period = pooler.get_pool(cr.dbname).get('sale.commissionsyear')
    period     = obj_period.browse(cr, uid, data['id'])
    if period.state != 'draft':
        raise wizard.except_wizard(_('UserError'), _('Periodo Anual Cerrado..!'))
    return {}

def _data_save(self, cr, uid, data, context):
    if not data['form']['sure']:
        raise wizard.except_wizard(_('UserError'), _('Para cerrar debe marcar la casilla..!'))
    pool = pooler.get_pool(cr.dbname)
    year_id = data['id']

    cr.execute('UPDATE sale_commissionsperiod SET state = %s WHERE commissionsyear_id = %s', ('done',year_id))
    cr.execute('UPDATE sale_commissionsyear   SET state = %s WHERE id = %s', ('done', year_id))
    period_ids = pooler.get_pool(cr.dbname).get('sale.commissionsperiod').search(cr, uid, [('commissionsyear_id','=',year_id)])
    if period_ids:
        for p in period_ids:
            cr.execute("update commissions_seller set state=%s where commission_period_id=%s AND state='draft'", ('paid', p))
    return {}

class wiz_commissions_close_state(wizard.interface):
    states = {
        'init': {
            'actions': [_check_data],
            'result': {'type': 'form', 'arch':_transaction_form, 'fields':_transaction_fields, 'state':[('end','Cancel'),('close','Cierre Anual')]}
        },
        'close': {
            'actions': [_data_save],
            'result': {'type': 'state', 'state':'end'}
        }
    }
wiz_commissions_close_state('commissions_year_close')