# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Corvus Latinoamerica (http://www.corvus.com.ve/) All Rights Reserved.
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
import pooler
import tools
from osv import fields,osv,orm
from osv.orm import browse_record

_transaction_form = '''<?xml version="1.0"?>
<form string="Cerrar Periodo de Comisiones">
    <separator string="Si esta seguro, Por favor marque la casilla ?" colspan="4"/>
    <field name="sure"/>
</form>'''

_transaction_fields = {
    'sure': {'string':'Marque esta casilla', 'type':'boolean'},
}

def _check_data(self, cr, uid, data, context):
    obj_period = pooler.get_pool(cr.dbname).get('sale.commissionsperiod')
    period     = obj_period.browse(cr, uid, data['id'])
    if period.state != 'draft':
        raise wizard.except_wizard(_('UserError'), _('Periodo Cerrado..!'))
    return {}

def _data_save(self, cr, uid, data, context):
    mode = 'done'
    if not data['form']['sure']:
        raise wizard.except_wizard(_('UserError'), _('Para cerrar debe marcar la casilla..!'))
    if data['form']['sure']:
        for id in data['ids']:
            cr.execute('update sale_commissionsperiod set state=%s where id=%s', (mode, id))
            cr.execute("update commissions_seller set state=%s where commission_period_id=%s AND state='draft'", ('paid', id))
    return {}

class wiz_commission_period_close(wizard.interface):
    states = {
        'init': {
            'actions': [_check_data],
            'result': {'type': 'form', 'arch':_transaction_form, 'fields':_transaction_fields, 'state':[('end','Cancel'),('close','Cerrar Periodo')]}
        },
        'close': {
            'actions': [_data_save],
            'result': {'type': 'state', 'state':'end'}
        }
    }
wiz_commission_period_close('commissions_period_close')