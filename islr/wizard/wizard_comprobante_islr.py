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
    <field name="date1"/>        
    <field name="account_id"/>  
    
</form>'''


pay_fields = {
    'date1': {'string': 'Fecha', 'type':'date', 'required':True, 'default':lambda *args: time.strftime('%Y-%m-%d')},
    'account_id': {'string': 'Cuenta ISLR', 'type': 'many2one', 'relation':'account.account', 'required':True, 'domain':[('type','=','payable')] }
    }

def _pay_and_reconcile(self, cr, uid, data, context):
    invoice_obj =  pooler.get_pool(cr.dbname).get('account.invoice')
    islr_obj =  pooler.get_pool(cr.dbname).get('account.islr.tax')
    form = data['form']
    invoice_id = data['id']
    datosinvoice = invoice_obj.browse(cr, uid, invoice_id)
    next_state = 'report'
    #Inicializacion Variables---------------------------------------------------------------------------------------- 
    writeoff_account_id = False
    writeoff_journal_id = False
    number         = datosinvoice.number_document
    fecha_fact     = datosinvoice.date_document
    period_id      = datosinvoice.period_id.id
    journal_id     = datosinvoice.journal_id.id
    ci_rif = datosinvoice.partner_id.vat
    base           = datosinvoice.amount_untaxed
    acc_id     = form['account_id']
    monto      = 0
    porcentaje = 0
    sustraendo = 0
    period_ids= pooler.get_pool(cr.dbname).get('account.period').search(cr,uid,[('date_start','<=',form['date1']),('date_stop','>=',form['date1'])])
    if period_ids:
        period_id = period_ids[0]
    
    if not ci_rif:
        raise wizard.except_wizard(_('Alerta !'), _('El Proveedor debe poseer: Cedula o RIF'))

    porcentaje = datosinvoice.islr_type_id.porcentaje
    monto_max  = datosinvoice.islr_type_id.monto_maximo
    sustraendo = datosinvoice.islr_type_id.sustraendo
        
    if base > monto_max:
        monto = datosinvoice.amount_untaxed * porcentaje / 100 - sustraendo
    else:
        raise wizard.except_wizard(_('Alerta !'), _('La Factura no excede el monto maximo. No se Aplica ISLR'))   
    #Creando el Comprobante-------------------------------------------------------------------------------------------- 
    vals = {
            'type':'in_invoice',
            'document_date':form['date1'],
            'inicial_date': time.strftime('%Y-%m-%d'),
            'partner_id':datosinvoice.partner_id.id,
            'currency_id':datosinvoice.currency_id.id,
            'company_id':datosinvoice.company_id.id,
            'account_id':acc_id,
            'islr_type_id':datosinvoice.islr_type_id.id,
            'base':datosinvoice.amount_untaxed,
            'porcentaje':porcentaje,
            'descuento': sustraendo,
            'amount_islr': monto
            }
    islr_id=islr_obj.create(cr,uid, vals,context=None)
    if islr_id:
        line_ids = pooler.get_pool(cr.dbname).get('account.islr.tax.line').create(cr, uid,{'islr_id':islr_id,'invoice_id':invoice_id,'name': number,'date_invoice':fecha_fact,'base_amount':base,'retention_amount':monto})
        #wf_service = netsvc.LocalService('workflow')
        #wf_service.trg_validate(uid, 'account.islr.tax', islr_id, 'islr_done', cr)
        #Actualizando datos Factura----------------------------------------------------------------------------------
        islr_num = ''
        islr_dat = pooler.get_pool(cr.dbname).get('account.islr.tax').read(cr, uid, [islr_id],['name'])
        if islr_dat and islr_dat[0] and islr_dat[0]['name']:
            islr_num = islr_dat[0]['name']
        invoice_obj.write(cr,uid, [invoice_id], {'islr':True,'islr_number':islr_num},context=None)
        #Creando Asientos del Comprobante de ISLR--------------------------------------------------------------------
        context['date_p'] = form['date1']
        descrip = 'Retencion de ISLR'
        #print "CONTEX-RET-ISLR",context,"  FEC ",form['date1'] 
        move_id = invoice_obj.pay_and_reconcile(cr, uid, [invoice_id],monto, acc_id, period_id, journal_id, writeoff_account_id,period_id, writeoff_journal_id, context,descrip)
        if move_id:
            islr_obj.write(cr,uid, [islr_id], {'state':'done','move_id':move_id},context=None)
            move_obj = pooler.get_pool(cr.dbname).get('account.move')
            #move_obj.post(cr, uid, [move_id], context=context)
    return next_state

def _check_data(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    invoice = pool.get('account.invoice').browse(cr, uid, data['id'], context)
    cta_id = False
    if invoice.islr:
        raise wizard.except_wizard(_('Alerta !'), _('La Factura Ya Fue Retenida'))
    if not invoice.islr_type_id:
        raise wizard.except_wizard(_('Alerta !'), _('La Factura No posee un Tipo de Islr Asignado'))
    else:
        cta_id = invoice.islr_type_id.account_id.id
    if not invoice.partner_id.islr:
        raise wizard.except_wizard(_('Alerta !'), _('El Proveedor no es Contribuyente'))
    if invoice.state in ['draft', 'proforma2', 'cancel']:
        raise wizard.except_wizard(_('Alerta !'), _('No puede pagar islr de Facturas en Estatus draft o cancel'))
    return {
        'account_id': cta_id,
        'date1': time.strftime('%Y-%m-%d')
    }

class wizard_pay_islr_invoice(wizard.interface):
    states = {
        'init': {
            'actions': [_check_data],
            'result': {'type':'form', 'arch':pay_form, 'fields':pay_fields, 'state':[('end','Cancelar'),('pay_and_reconcile','Pagar')]}
        },
        'pay_and_reconcile': {
            'actions': [],
            'result': {'type' : 'choice', 'next_state':_pay_and_reconcile}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'wizard_islr', 'state': 'end'}
        }
    }

wizard_pay_islr_invoice('comprobante_islr')