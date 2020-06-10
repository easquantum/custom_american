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
<form string="Crear Comprobante"> 
    <field name="date"/>        
    <field name="account_id"/>  
    
</form>'''


pay_fields = {
    'date': {'string': 'Fecha', 'type':'date', 'required':True, 'default':lambda *args: time.strftime('%Y-%m-%d')},
    'account_id': {'string': 'Cuenta ISLR', 'type': 'many2one', 'relation':'account.account', 'required':True, 'domain':[('type','=','payable')] }
    }

def _pay_and_reconcile(self, cr, uid, data, context):
    invoice_obj =  pooler.get_pool(cr.dbname).get('account.invoice')
    islr_obj =  pooler.get_pool(cr.dbname).get('account.islr.tax')
    form = data['form']
    invoice_id = data['id']
    datosinvoice = invoice_obj.browse(cr, uid, invoice_id)
    #Inicializacion Variables---------------------------------------------------------------------------------------- 
    writeoff_account_id = False
    writeoff_journal_id = False
    period_id      = datosinvoice.period_id.id
    journal_id     = datosinvoice.journal_id.id
    amount_invoice = datosinvoice.amount_untaxed
    acc_id     = form['account_id']
    monto      = 0
    porcentaje = 0
    period_ids= pooler.get_pool(cr.dbname).get('account.period').search(cr,uid,[('date_start','<=',form['date']),('date_stop','>=',form['date'])])
    if period_ids:
        period_id = period_ids[0]
    ci_rif = datosinvoice.partner_id.vat
    if ci_rif:
        if ci_rif[0].upper() == 'J' or ci_rif[0].upper() == 'G':
            tipo_islr = 'legal'
        else:
            tipo_islr = 'natural'
    else:
        raise wizard.except_wizard(_('Alerta !'), _('El Cliente debe poseer: Cedula o RIF'))
    if tipo_islr == 'legal':
        porcentaje = datosinvoice.islr_type_id.porcentaje_j
        monto_max  = datosinvoice.islr_type_id.monto_maximo_j
        monto_des  = datosinvoice.islr_type_id.descuento_j

    if tipo_islr == 'natural':
        porcentaje = datosinvoice.islr_type_id.porcentaje_n
        monto_max  = datosinvoice.islr_type_id.monto_maximo_n
        monto_des  = datosinvoice.islr_type_id.descuento_n
        
    if datosinvoice.amount_untaxed > monto_max:
        monto = datosinvoice.amount_untaxed * porcentaje / 100 - monto_des
    else:
        raise wizard.except_wizard(_('Alerta !'), _('La Factura no excede el monto maximo. No se Aplica ISLR'))   
    #Creando el Comprobante--------------------------------------------------------------------------------------------
    comp_nro   = pooler.get_pool(cr.dbname).get('ir.sequence').get(cr, uid, 'account.islr.tax') 
    vals = {
            'name':comp_nro,
            'type':'in_invoice',
            'type_islr':datosinvoice.islr_type_id.id,
            'type_islr':tipo_islr,
            'inicial_date':form['date'],
            'partner_id':datosinvoice.partner_id.id,
            'currency_id':datosinvoice.currency_id.id,
            'company_id':datosinvoice.company_id.id,
            'account_id':acc_id,
            'invoice_id':invoice_id,
            'base':datosinvoice.amount_untaxed,
            'porcentaje':porcentaje,
            'amount_islr': monto,
            'descuento': monto_des,
            'islr_type_id':datosinvoice.islr_type_id.id
            }
    islr_id=islr_obj.create(cr,uid, vals,context=None)
    if islr_id:
        #Actualizando datos Factura----------------------------------------------------------------------------------
        invoice_obj.write(cr,uid, [invoice_id], {'islr':True},context=None)
        #Creando Asientos del Comprobante de ISLR--------------------------------------------------------------------
        context['date_p'] = form['date']
        descrip = 'Retencion de ISLR'
        move_id = invoice_obj.pay_and_reconcile(cr, uid, [invoice_id],monto, acc_id, period_id, journal_id, writeoff_account_id,period_id, writeoff_journal_id, context,descrip)
        islr_obj.write(cr,uid, [islr_id], {'move_id':move_id},context=None)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'account.islr.tax', islr_id, 'islr_done', cr)
        if move_id:
            move_obj = pooler.get_pool(cr.dbname).get('account.move')
            move_obj.post(cr, uid, [move_id], context=context)
    return {}

def _check_data(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    invoice = pool.get('account.invoice').browse(cr, uid, data['id'], context)
    if invoice.islr:
        raise wizard.except_wizard(_('Alerta !'), _('La Factura Ya Fue Retenida'))
    if not invoice.islr_type_id:
        raise wizard.except_wizard(_('Alerta !'), _('La Factura No posee un Tipo de Islr Asignado'))
    if not invoice.partner_id.special:
        raise wizard.except_wizard(_('Alerta !'), _('El Cliente no es Contribuyente'))
    if invoice.state in ['draft', 'proforma2', 'cancel']:
        raise wizard.except_wizard(_('Alerta !'), _('No puede pagar islr de Facturas en Estatus draft o cancel'))
    return {
        'date': time.strftime('%Y-%m-%d')
    }

class wizard_pay_islr_invoice(wizard.interface):
    states = {
        'init': {
            'actions': [_check_data],
            'result': {'type':'form', 'arch':pay_form, 'fields':pay_fields, 'state':[('end','Cancelar'),('pay_and_reconcile','Pagar')]}
        },
        'pay_and_reconcile': {
            'actions': [_pay_and_reconcile],
            'result': {'type':'state', 'state':'end'}
        }
    }

wizard_pay_islr_invoice('comprobante_islr')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

