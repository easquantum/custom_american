# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import wizard
import ir
import pooler
from osv.osv import except_osv
import netsvc

invoice_form = """<?xml version="1.0"?>
<form string="Creando Factura del Cliente">
    <separator colspan="4" string="Creando Facturas" />
    <field name="journal_id"/>
    <newline/>
    <field name="group"/>
    <newline/>
    <field name="type"/>
</form>
"""

invoice_fields = {
    'journal_id': {
        'string': 'Diario de Destino',
        'type': 'many2one',
        'relation': 'account.journal',
        'domain':[('type','=','sale')],
        'required': True
    },
    'group': {
        'string': 'Agrupar por Empresa',
        'type':'boolean',
        'readonly': True
    },
    'type': {
        'string': 'Tipo',
        'type': 'selection',
        'selection': [
            ('out_invoice', 'Customer Invoice'),
            ],
        'required': True
    },
}

def _get_type(obj, cr, uid, data, context):
    picking_obj=pooler.get_pool(cr.dbname).get('stock.picking')
    type = 'out_invoice'
    pick = picking_obj.browse(cr, uid, data['id'], context)  
    if pick.state !='done':
        raise wizard.except_wizard('Error','La Nota de Salida Debe estar Realizada, para poder Facturar!!!')
    if pick.invoice_state=='invoiced':
        raise wizard.except_wizard('UserError','La Nota de Salida ya fue Facturada')
    if pick.invoice_state=='none':
        raise wizard.except_wizard('UserError','Esta Nota de Salida no puede ser facturada.')

    if not pick.move_lines:
        raise wizard.except_wizard('Error','No se puede crear la Factura, no existen productos')

    return {'type': type}

def _create_invoice(obj, cr, uid, data, context):
    if data['form'].get('new_picking',False):
        data['id'] = data['form']['new_picking']
        data['ids'] = [data['form']['new_picking']]
    pool = pooler.get_pool(cr.dbname)
    picking_obj = pooler.get_pool(cr.dbname).get('stock.picking')
    mod_obj = pool.get('ir.model.data')
    act_obj = pool.get('ir.actions.act_window')

    type = data['form']['type']
    try:
        res = picking_obj.action_invoice_create(cr, uid, data['ids'], journal_id=data['form']['journal_id'],group=data['form']['group'],type=type, context= context)
    except except_osv, e: 
        raise wizard.except_wizard(e.name, e.value)     
    return res


class create_invoice_customers(wizard.interface):
    states = {
        'init': {
            'actions': [_get_type],
            'result': {
                'type': 'form',
                'arch': invoice_form,
                'fields': invoice_fields,
                'state': [
                    ('end', 'Cancel'),
                    ('create_invoice', 'Create invoice')
                ]
            }
        },
        'create_invoice': {
            'actions': [],
            'result': {
                'type': 'action',
                'action': _create_invoice,
                'state': 'end'
            }
        },
    }

create_invoice_customers("stock.create_invoices_customers")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

