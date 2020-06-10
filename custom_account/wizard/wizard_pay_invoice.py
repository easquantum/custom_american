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

import wizard
import netsvc
import pooler
import time
from tools.translate import _

pay_form = '''<?xml version="1.0"?>
<form string="Pay invoice">
    <field name="amount"/>
    <newline/>
    <field name="name"/>
    <field name="date"/>
    <field name="journal_id"/>
    <field name="period_id"/>
    <newline/>
    <field name="payment_method"/>
    <field name="account_id" />
</form>'''

payment_number_form = '''
<form string='Pay invoice'> 
    <field name="payment_number" />
</form>
    '''

pay_fields = {
    'amount': {'string': 'Monto a Pagar', 'type':'float', 'digits':'14,4', 'required':True},
    'name': {'string': 'Descripcion', 'type':'char', 'size': 64},
    'date': {'string': 'Dia del Pago', 'type':'date', 'required':True, 'default':lambda *args: time.strftime('%Y-%m-%d')},
    'journal_id': {'string': 'Diario', 'type': 'many2one', 'relation':'account.journal', 'required':True},
    'period_id': {'string': 'Periodo', 'type': 'many2one', 'relation':'account.period', 'required':True},
    'payment_method': {'string': 'Tipo de Pago', 'type': 'selection', 'selection':[('EF','Efectivo'),('DP','Deposito'), ('CH','Cheque'),('TC','Tarjeta_Credito'),('TD','Tarjeta_Debito'),('TR','Transferencia'),('OT','Otros')], 'required':True },
    'account_id': {'string': 'Cuenta', 'type': 'many2one', 'relation':'account.account', 'required':True},
    }

payment_number_field = {
   'payment_number': {'string': 'Numero de Pago', 'type':'char', 'required': True} 
}

payment_number_field_maybe = {
   'payment_number': {'string': 'Payment Number', 'type':'char'} 
}

def _save_payment(self, cr, uid, data, pool, invoice):
    payment_method = pool.get('account.payment.method')
    
    payment = {}
    payment['type'] = 'in_invoice'
    payment['ro']   = False
    payment['payment_type'] = data['form']['payment_method']
    payment['date_payment'] = data['form']['date'] 
    payment['amount'] = data['form']['amount']
    if payment['payment_type'] != 'EF':
        payment['payment_number'] = data['form']['payment_number']
    payment['invoice_id'] = str(invoice.id)
    payment['partner_id'] = invoice.partner_id.id
    payment['account_id'] = data['form']['account_id']
    payment_method.create(cr,uid,payment)

    return {}

def _check_payment(self, cr, uid, data, context):
    if data['form']['payment_method'] == 'EF':
        return 'reconcile'
    elif data['form']['payment_method'] != 'OT':
        return 'check_number'
    return 'check_number_maybe'

def _pay_and_reconcile(self, cr, uid, data, context):
    form = data['form']
    period_id = form.get('period_id', False)
    journal_id = form.get('journal_id', False)
    writeoff_account_id = form.get('writeoff_acc_id', False)
    writeoff_journal_id = form.get('writeoff_journal_id', False)
    pool = pooler.get_pool(cr.dbname)
    cur_obj = pool.get('res.currency')
    amount = form['amount']

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

    acc_id = form.get('account_id', False)
    if not acc_id:
        acc_id = journal.default_credit_account_id and journal.default_credit_account_id.id
        if not acc_id:
            raise wizard.except_wizard(_('Error !'), _('Your journal must have a default credit and debit account.'))
    pool.get('account.invoice').pay_and_reconcile(cr, uid, [data['id']],
            amount, acc_id, period_id, journal_id, writeoff_account_id,
            period_id, writeoff_journal_id, context, data['form']['name'])

    _save_payment(self, cr, uid, data, pool, invoice) 


    return {}

def _get_period(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    ids = pool.get('account.period').find(cr, uid, context=context)
    period_id = False
    if len(ids):
        period_id = ids[0]
    invoice = pool.get('account.invoice').browse(cr, uid, data['id'], context)
    if invoice.state in ['draft', 'proforma2', 'cancel']:
        raise wizard.except_wizard(_('Error !'), _('Can not pay draft/proforma/cancel invoice.'))
    return {
        'period_id': period_id,
        'amount': invoice.residual,
        'date': time.strftime('%Y-%m-%d'),
    }

class wizard_pay_invoice_ext(wizard.interface):
    states = {
        'init': {
            'actions': [_get_period],
            'result': {'type':'form', 'arch':pay_form, 'fields':pay_fields, 'state':[('end','Cancelar'),('check_payment','Pagar')]}
        },
        'check_payment':{
            'actions':[],
            'result':{'type': 'choice','next_state': _check_payment}
        },
        'check_number_maybe':{
            'actions':[],
            'result':{'type': 'form', 'arch': payment_number_form, 'fields':payment_number_field_maybe, 'state':[('end','Cancelar'),('reconcile','Pagar y reconciliar')]}
        },
        'check_number':{
            'actions':[],
            'result':{'type': 'form', 'arch': payment_number_form, 'fields':payment_number_field, 'state':[('end','Cancelar'),('reconcile','Pagar y reconciliar')]}
        },
        'reconcile': {
            'actions': [_pay_and_reconcile],
            'result': {'type':'state', 'state':'end'}
        }
    }

wizard_pay_invoice_ext('account.invoice.pay.ext')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
