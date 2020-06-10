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
from osv import osv
from osv.osv import except_osv
from tools.translate import _

recovery_form = '''<?xml version="1.0"?>
<form string="Recovery invoice">
    <separator colspan="4" string="Datos contables"/>
    <newline/>
    <field name="control_number" />
    <newline/>
    <field name="name"/>
    <field name="ro"/>
    <field name="journal_id"/>
    <field name="date"/>
    <field name="account_id" />
    <field name="period_id"/>
    <separator colspan="4" string="Datos Cobranza"/>
    <newline/>
    <field name="amount"/>
    <newline/>
    <field name="payment_method"/>
    <field name="payment_number" />
    <separator colspan="4" string="Datos Banco"/>
    <field name="bank_id" />
    <field name="document_number" />
</form>'''

recovery_fields = {
    'control_number': {'string': 'Recibo Nro.', 'type':'char', 'size': 34, 'required':True},
    'name': {'string': 'Descripcion', 'type':'char', 'size': 64},
    'date': {'string': 'Dia del Pago', 'type':'date', 'required':True, 'default':lambda *args: time.strftime('%Y-%m-%d')},
    'journal_id': {'string': 'Diario', 'type': 'many2one', 'relation':'account.journal', 'required':True},
    'period_id': {'string': 'Periodo', 'type': 'many2one', 'relation':'account.period', 'required':True},
    'account_id': {'string': 'Cuenta', 'type': 'many2one', 'relation':'account.account', 'required':True},
    'amount': {'string': 'Monto a Cobrar', 'type':'float', 'digits':'14,4', 'required':True},
    'payment_method': {'string': 'Tipo de Pago', 'type': 'selection', 'selection':[('EF','Efectivo'),('DP','Deposito'), ('CH','Cheque'),('TR','Transferencia'),('OT','Otros')], 'required':True },
    'payment_number': {'string': 'Numero de Pago', 'type':'char', 'required': True},
    'bank_id': {'string': 'Banco', 'type': 'many2one', 'relation':'res.bank'},
    'document_number': {'string': 'Cheque Nro.', 'type':'char', 'size': 34},
    'ro': {'string':"RO",'type':'boolean'}
    }

def _save_recovery(self, cr, uid, data, pool, invoice):
    payment_method = pool.get('account.payment.method')
    payment = {}
    payment['type'] = 'out_invoice'
    payment['ro']   = data['form']['ro']
    payment['control_number'] = data['form']['control_number']
    payment['payment_type'] = data['form']['payment_method']
    payment['date_payment'] = data['form']['date'] 
    payment['amount'] = data['form']['amount']
    payment['payment_number'] = data['form']['payment_number']
    payment['invoice_id'] = str(invoice.id)
    payment['partner_id'] = invoice.partner_id.id
    payment['bank_id'] = data['form']['bank_id']
    payment['document_number'] = data['form']['document_number']
    payment['account_id'] = data['form']['account_id']
    try:
        resp = payment_method.create(cr,uid,payment)
        #print "CREANDO EL PAGO",resp
    except except_osv, e:
        raise wizard.except_wizard(e.name, e.value)
    return {}

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
        context={'comment':form['comment']}
    else:
        context={'comment':False}

    acc_id = form.get('account_id', False)
    if not acc_id:
        acc_id = journal.default_credit_account_id and journal.default_credit_account_id.id
        if not acc_id:
            raise wizard.except_wizard(_('Error !'), _('Your journal must have a default credit and debit account.'))
    if form['date']:
        context['date_p'] = form['date']
    res= pool.get('account.invoice').pay_and_reconcile(cr, uid,[data['id']],amount,acc_id,period_id,journal_id,writeoff_account_id,period_id,writeoff_journal_id,context,data['form']['name'])
    #print "RETORN-COBRO",res

    _save_recovery(self, cr, uid, data, pool, invoice) 
    return {}

def _get_period(self, cr, uid, data, context={}):
    if not data:
        return {}
    elif not data.has_key('id'):
        return {}
    if not data['id']:
        return {}
    pool = pooler.get_pool(cr.dbname)
    ids = pool.get('account.period').find(cr, uid, context=context)
    period_id = False
    pendiente = 0
    diario_banco = 20    # ID 20 que corresponde al diario de Banco
    cta_defecto  = 2965  # ID 2965 que corresponde a cuenta 1.1.2.99.00.000
    if len(ids):
        period_id = ids[0]
    invoice = pool.get('account.invoice').browse(cr, uid, data['id'], context)
    if invoice and invoice.state in ['draft', 'proforma2', 'cancel']:
        raise wizard.except_wizard(_('Error !'), _('Can not pay draft/proforma/cancel invoice.'))
    if invoice.residual < 1:
        raise wizard.except_wizard(_('Error !'), _('La Factura no tiene un momto pendiente de Cobro!!!'))
    else:
        pendiente = invoice.residual
    return {
        'period_id': period_id, 
        'amount': pendiente,
        'date': time.strftime('%Y-%m-%d'),
        'ro': True,
        'payment_method': 'DP',
        'journal_id': diario_banco,
        'account_id': cta_defecto,
    }

class wizard_recovery_invoice(wizard.interface):
    states = {
        'init': {
            'actions': [_get_period],
            'result': {'type':'form', 'arch':recovery_form, 'fields':recovery_fields, 'state':[('end','Cancelar'),('reconcile','Cobrar')]}
        },
        'reconcile': {
            'actions': [_pay_and_reconcile],
            'result': {'type':'state', 'state':'end'}
        }
    }

wizard_recovery_invoice('account.invoice.recovery')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
