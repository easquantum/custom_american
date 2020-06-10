# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Corvus Latinoamerica, C.A. 
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
import time
from tools.translate import _
import pdb

pay_form = '''<?xml version="1.0"?>
<form string="Pay invoice">
    <field name="name"/>
    <field name="date"/>
    <field name="journal_id"/>
    <field name="period_id"/>
    <field name="cta_id"/>
    <newline/>
    <field name="retencion_id" />
    <field name="retencion_number" />
    <field name="amount"/>
</form>'''

pay_fields = {
    'name': {'string': 'Descripcion', 'type':'char', 'size': 64},
    'date': {'string': 'Fecha', 'type':'date', 'required':True, 'default':lambda *args: time.strftime('%Y-%m-%d')},
    'journal_id': {'string': 'Diario', 'type': 'many2one', 'relation':'account.journal', 'required':True },
    'period_id': {'string': 'Periodo', 'type': 'many2one', 'relation':'account.period', 'required':True},
    'cta_id': {'string': 'Cuenta', 'type': 'many2one', 'relation':'account.account', 'required':True},
    'retencion_id': {'string': 'Tipo de Rentencion', 'type': 'many2one', 'relation':'account.retention.types' , 'required':True },
    'retencion_number': {'string': 'Numero de Retencion', 'type':'char', 'required': True},
    'amount': {'string': 'Monto Retenido', 'type':'float', 'required':True} 
    }

def _save_retencion(self, cr, uid, data):
    pool = pooler.get_pool(cr.dbname)
    form = data['form']
    
    retencion_method = pool.get('account.invoice.retencion.client')
    invoice_method  = pool.get('account.invoice')
    invoice = invoice_method.read(cr, uid, data['id'])
    '''
    TODO
    VALIDACION PARA RESTAR LAS RETENCIONES QUE YA SE HAN PAGADO CONTRA EL MONTO DEL IVA. DE MANERA DE HACER UNA VALIDACION MAS EXACTA 
    invoice_amount = invoice['amount_tax']

    try:
        alredy_retention_id = retencion_method.search(cr, uid, [('invoice_id','=',data['id'])])
    
        if alredy_retencion_id:
            alredy_retencion = retencion_method.read(cr, uid, alredy_retencion_id)
            invoice_amount = invoice_amount - alredy_retencion
    except:
        pass
    '''

    if invoice['amount_tax'] < form.get('amount'):
        raise wizard.except_wizard(_('Error !'), _('No se puede pagar una retencion con un monto mayor al del iva'))

    retencion = {}
    retencion['retencion_id'] = form.get('retencion_id',False)
    retencion['amount'] = form.get('amount',False)
    retencion['number'] = form.get('retencion_number',False)
    retencion['date_retencion'] = form.get('date',False)
    retencion['invoice_id'] = data['id']
    retencion['include'] = data['include']
    retencion_method.create(cr,uid,retencion)

    return {}

def _pay_and_reconcile(self, cr, uid, data, context):
    form = data['form']
    period_id = form.get('period_id', False)
    journal_id = form.get('journal_id', False)
    retencion_id = form.get('retencion_id',False)
    acc_id = form.get('cta_id',False)
    writeoff_account_id = form.get('writeoff_account_id', False)
    writeoff_journal_id = form.get('writeoff_journal_id', False)
    pool = pooler.get_pool(cr.dbname)
    retencion = pool.get('account.retention.types').read(cr,uid,retencion_id)
    cur_obj = pool.get('res.currency')
    amount = form['amount']
    data['include']= retencion['include']

    invoice = pool.get('account.invoice').browse(cr, uid, data['id'], context)
    journal = pool.get('account.journal').browse(cr, uid, data['form']['journal_id'], context)

    if journal.currency and invoice.company_id.currency_id.id<>journal.currency.id:
        ctx = {'date':data['form']['date']}
        amount = cur_obj.compute(cr, uid, journal.currency.id, invoice.company_id.currency_id.id, amount, context=ctx)

    # Take the choosen date
    if form.has_key('comment'):
        context={'date_p':form['date'],'comment':form['comment']}
    else:
        context={'date_p':form['date'],'comment':False}
    #acc_id = retencion['account_receivable'] and retencion['account_payable'][0]

    if not acc_id:
        raise wizard.except_wizard(_('Error !'), _('Your journal must have a default credit and debit account.'))
    
    pool.get('account.invoice').pay_and_reconcile(cr, uid, [data['id']],
            amount, acc_id, period_id, journal_id, writeoff_account_id,
            period_id, writeoff_journal_id, context, data['form']['name'])

    _save_retencion(self, cr, uid, data) 
    return {}

def _get_period(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    ids = pool.get('account.period').find(cr, uid, context=context)
    period_id = False
    if len(ids):
        period_id = ids[0]
    invoice = pool.get('account.invoice').browse(cr, uid, data['id'], context)
    if invoice.state in ['draft', 'proforma2', 'cancel']:
        raise wizard.except_wizard(_('ALERTA !'), _('No se puede cargar la retencion si el estado de la factura es: draft/cancel'))
    
    return {
        'period_id': period_id,
        'date': time.strftime('%Y-%m-%d')
    }

class wizard_set_retention_client(wizard.interface):
    states = {
        'init': {
            'actions': [_get_period],
            'result': {'type':'form', 'arch':pay_form, 'fields':pay_fields, 'state':[('end','Cancel'),('reconcile','OK')]}
        },
        'reconcile': {
            'actions': [_pay_and_reconcile],
            'result': {'type':'state', 'state':'end'}
        }
    }

wizard_set_retention_client('set_retention_client')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
