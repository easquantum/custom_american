# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007-2010 Corvus Latinoamerica (http://corvus.com.ve) All Rights Reserved.
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
#############################################################################

import time
import locale
import wizard
import netsvc
import pooler
import tools
from tools import config
from osv import osv, fields

class account_retention(osv.osv):
    
    def _amount_ret_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for retention in self.browse(cr, uid, ids, context):
            res[retention.id] = {
                'amount_base_ret': 0.0,
                'total_tax_ret': 0.0
            }
            for line in retention.retention_line:
                if line.invoice_id.type == 'in_refund' or line.invoice_id.type == 'out_refund':
                    res[retention.id]['total_tax_ret']   -= line.retention_amount
                    res[retention.id]['amount_base_ret'] -= line.base_amount
                else:
                    res[retention.id]['total_tax_ret'] += line.retention_amount
                    res[retention.id]['amount_base_ret'] += line.base_amount

        return res
    
    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        type = context.get('type', 'in_invoice')
        return type

    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        type_inv = context.get('type', 'in_invoice')
        type2journal = {'out_invoice': 'sale', 'in_invoice': 'purchase', 'out_refund': 'sale', 'in_refund': 'purchase'}
        journal_obj = self.pool.get('account.journal')
        res = journal_obj.search(cr, uid, [('type', '=', type2journal.get(type_inv, 'purchase'))], limit=1)
        if res:
            return res[0]
        else:
            return False

    def _get_currency(self, cr, uid, context):
        user = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        if user.company_id:
            return user.company_id.currency_id.id
        else:
            return self.pool.get('res.currency').search(cr, uid, [('rate','=',1.0)])[0]

    def _get_code(self,cr,uid,ids):
        pool_seq=self.pool.get('ir.sequence')
        cr.execute("select prefix from ir_sequence where code='account.retention' and active=True")
        res = cr.dictfetchone()
        if res:
            prefix = pool_seq._process(res['prefix'])
            ret = self.browse(cr, uid, ids)[0]
            fecha = time.strptime(ret.final_date,'%Y-%m-%d')
            dia = time.strftime('%d',fecha)
            #codpartner = ret.partner_id.ref[1:6].zfill(6)
            numero_comp = pooler.get_pool(cr.dbname).get('ir.sequence').get(cr,uid, 'account.retention')
            #return prefix+dia+codpartner
            return numero_comp
        return false


    _name = "account.retention"
    _description = "Comprobante de Retencion/withholding statement"
    _columns = {
        'name': fields.char('Description', size=64, select=True,readonly=True, states={'draft':[('readonly',False)]}),
        'code': fields.char('Retention Number', size=32, states={'draft':[('readonly',False)]}),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', readonly=True, select=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('done','Done'),
            ('cancel','Cancelled')
            ],'State', select=True, readonly=True),
        'inicial_date': fields.date('Inicial Date', readonly=True, required=True, states={'draft':[('readonly',False)]}),
        'final_date': fields.date('Final Date', readonly=True, states={'draft':[('readonly',False)]}),
        'account_id': fields.many2one('account.account', 'Account', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True, required=True, states={'draft':[('readonly',False)]}),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True,readonly=True, states={'draft':[('readonly',False)]}),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'retention_line': fields.one2many('account.retention.line', 'retention_id', 'Retention Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'amount_base_ret': fields.function(_amount_ret_all, method=True, digits=(16,4), string='Total Base Ret', multi='all'),
        'total_tax_ret': fields.function(_amount_ret_all, method=True, digits=(16,4), string='Total Tax Ret', multi='all'),


    }
    _defaults = {
        'type': _get_type,
        'inicial_date': lambda *a: time.strftime('%Y-%m-%d'),
        'final_date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'journal_id': _get_journal,
        'currency_id': _get_currency,
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,

    }

    #Crea y asigna a las factura el nro de comprobante de retencion
    def button_create_number(self, cr, uid, ids, *args):
        inv_obj = self.pool.get('account.invoice')
        context = {}
        tipo = ''
        code = ''
        ret = self.browse(cr, uid, ids)[0] 
        if not ret:
            raise osv.except_osv('ERROR	', 'Datos Incompletos !!!') 
        if ret.type=='out_invoice' and not ret.code:
            raise osv.except_osv('ERROR	', 'Debe Asignar un Nro. de Comprobante !!!')
        if ret.type=='in_invoice' and ret.code:
            raise osv.except_osv('ERROR	', 'La facturas ya tiene asignado un codigo de retencion !!!')
        if not ret.retention_line:
            raise osv.except_osv('ERROR	', 'No existen facturas !!!')
        else:
            if ret.type=='in_invoice':
                code = self._get_code(cr,uid,ids)
                self.write(cr, uid, ids, {'code':code}) 
            if ret.type=='out_invoice':
                code = ret.code
            for line in ret.retention_line:
                inv_obj.write(cr, uid, line.invoice_id.id, {'retention':True,'number_retention':code}, context=context)
            
        return True

    #Crea y asigna a las factura el nro de comprobante de retencion
    def button_cancel_number(self, cr, uid, ids, *args):
        inv_obj = self.pool.get('account.invoice')
        context = {}
        ret = self.browse(cr, uid, ids)[0]
        if not ret.retention_line:
            raise osv.except_osv('ERROR	', 'No existen facturas !!!')
        else:
            for line in ret.retention_line:
                inv_obj.write(cr, uid, line.invoice_id.id, {'retention':False,'number_retention':''}, context=context)
            sql="DELETE FROM account_retention_line WHERE retention_id=%d"%(ids[0])
            cr.execute(sql)
            self.write(cr, uid, ids, {'state':'cancel'})
        return True

    #Aqui es donde se pasa la retencion de draft a done
    def action_move_create(self, cr, uid, ids, *args):
        inv_obj = self.pool.get('account.invoice')
        context = {}
        period_id = 0
        descrip   = 'Retencion IVA'
        ret = self.browse(cr, uid, ids)[0]
        if ret.type=='in_invoice':
            period_ids= self.pool.get('account.period').search(cr,uid,[('date_start','<=',ret.inicial_date),('date_stop','>=',ret.inicial_date)])
            context['date_p'] = ret.inicial_date
        else:
            period_ids= self.pool.get('account.period').search(cr,uid,[('date_start','<=',time.strftime('%Y-%m-%d')),('date_stop','>=',time.strftime('%Y-%m-%d'))])
        if period_ids:
            period_id = period_ids[0]
        if not ret.code:
            raise osv.except_osv('ERROR	', 'Debe crear un Nro. de comprobante antes de pagar!!!')
        if not ret.retention_line:
            raise osv.except_osv('ERROR	', 'Debe asignar las facturas antes de pagar!!!')
        acc_id = ret.account_id.id
        if ret.retention_line:
            for line in ret.retention_line:
                if not period_ids:
                    period_id = line.invoice_id.period_id.id
                journal_id = ret.journal_id.id
                writeoff_account_id = False
                writeoff_journal_id = False
                amount = line.retention_amount
                mov_id = inv_obj.pay_and_reconcile(cr, uid, [line.invoice_id.id],amount, acc_id, period_id, journal_id, writeoff_account_id,period_id, writeoff_journal_id, context,descrip)
                cr.execute('UPDATE account_retention_line SET move_id=%d WHERE id = %d;'%(mov_id,line.id))
        return True
    
    def button_compute_retention(self, cr, uid, ids, context={}):
        res = {}
        invoices = []
        tipo = ''
        ret = self.browse(cr, uid, ids)[0]
        ret_info = self.read(cr, uid,ids,['inicial_date','type','account_id','partner_id','company_id'])
        if not ret:
            raise osv.except_osv('ERROR	', 'Datos Incompletos !!!')
        if ret.type=='in_invoice':
            cr.execute('DELETE FROM account_retention_line WHERE retention_id = %d;'%ids[0])
            sql = """
                  SELECT id, partner_id,name,p_ret   
                  FROM account_invoice 
                  WHERE state = 'open' AND p_ret IS NOT NULL AND retention IS NOT TRUE AND type in ('in_invoice','in_invoice_ad','in_refund' )  
                  AND partner_id = %s;
                  """%(ret_info[0]['partner_id'][0]) 
            #print sql 
            cr.execute(sql)
            invoices = cr.fetchall()  
        if ret.type =='out_invoice':
            #cr.execute('DELETE FROM account_retention_line WHERE retention_id = %d;'%ids[0])
            comp_id = ret.company_id.id
            obj_company = pooler.get_pool(cr.dbname).get('res.company')
            datoscomp = obj_company.browse(cr, uid, ret.company_id.id)
            if datoscomp.partner_id.retention:
                p_ret = datoscomp.partner_id.retention
            else:
                raise osv.except_osv('ERROR	', 'La empresa no tiene definido el porcentaje de retencion!!!')
            sql = """
                  SELECT id, partner_id,name,p_ret  
                  FROM account_invoice 
                  WHERE state = 'open' AND retention IS NOT TRUE AND type in ('out_invoice','out_refund' )  
                  AND partner_id = %s;
                  """%(ret_info[0]['partner_id'][0]) 
            #print sql 
            cr.execute(sql)
            invoices = cr.fetchall()
        for invoice in invoices:
            #Se consultan los Impuesto
            invoice_id = invoice[0]
            tax_invoice_ids = pooler.get_pool(cr.dbname).get('account.invoice.tax').search(cr, uid, [('invoice_id','=',invoice_id) ])
            tax_datos       = pooler.get_pool(cr.dbname).get('account.invoice.tax').read(cr, uid, tax_invoice_ids,['name','base','amount'])
            for tax in tax_datos:
                #Se Obtiene el Grupo o tipo de Tax
                tax_id      = pooler.get_pool(cr.dbname).get('account.tax').search(cr, uid, [('name','=',tax['name']) ])
                tax_info    = pooler.get_pool(cr.dbname).get('account.tax').read(cr, uid, tax_id,['tax_group','amount'])
                if tax_info and tax_info[0]['tax_group'] == 'vat':
                    alic    = tax_info[0]['amount'] * 100
                    iva         = tax['amount']
                    base        = tax['base']
                    if ret.type=='in_invoice' and invoice[3] and invoice[3] > 0:
                        retenc = iva * invoice[3] / 100
                        self.pool.get('account.retention.line').create(cr, uid, {'retention_id':ids[0],'invoice_id':invoice[0],'name':invoice[2],'rate_amount':invoice[3],'base_amount':base,'tax_amount':iva,'rate_tax':alic,'retention_amount':retenc})
                    if ret.type=='out_invoice':
                        retenc = iva * p_ret / 100
                        self.pool.get('account.retention.line').create(cr, uid, {'retention_id':ids[0],'invoice_id':invoice[0],'name':invoice[2],'rate_amount':p_ret,'base_amount':base,'tax_amount':iva,'rate_tax':alic,'retention_amount':retenc})
        return True  

    def partner_id_change(self, cr, uid, ids, type, context=None):
        cta_id = False
        if not type:
            return {} 
        if type == 'in_invoice':
            account_ids = pooler.get_pool(cr.dbname).get('account.retention.configure').search(cr,uid,[('account_payable','=',1)])
        if type == 'out_invoice':
            account_ids = pooler.get_pool(cr.dbname).get('account.retention.configure').search(cr,uid,[('account_receivable','=',1)])
        if account_ids:
            account_default = pooler.get_pool(cr.dbname).get('account.retention.configure').read(cr, uid, account_ids,['account_id'])[0]
            cta_id = account_default['account_id'] 
        return {'value':{'account_id': cta_id}}
    
account_retention()



class account_retention_line(osv.osv):
    def _compute_tax_lines(self, cr, uid, ids, name, args, context=None):
        result = {}
        for ret_line in self.browse(cr, uid, ids, context):
            lines = []
            if ret_line.invoice_id:
                ids_tline = ret_line.invoice_id.tax_line
                lines = map(lambda x: x.id, ids_tline)
            result[ret_line.id] = lines
        return result

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for ret_line in self.browse(cr, uid, ids, context):
            res[ret_line.id] = {
                'amount_tax_ret': 0.0,
                'base_ret': 0.0
            }
            #for line in ret_line.invoice_id.tax_line:
            #    res[ret_line.id]['amount_tax_ret'] += line.amount_ret
            #    res[ret_line.id]['base_ret'] += line.base_ret

        return res

    def _retention_rate(self, cr, uid, ids, name, args, context=None):
        res = {}
        for ret_line in self.browse(cr, uid, ids, context=context):
            if ret_line.invoice_id:
                res[ret_line.id] = ret_line.invoice_id.p_ret
            else:
                res[ret_line.id] = 0.0
        return res


    _name = "account.retention.line"
    _description = "Retencion line"
    _columns = {
        'name': fields.char('Description', size=64), 
        'retention_id': fields.many2one('account.retention', 'Retention Ref', ondelete='cascade', select=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice Ref', required=True, select=True),
        'tax_line': fields.function(_compute_tax_lines, method=True, relation='account.invoice.tax', type="one2many", string='Tax Lines'),
        'amount_tax_ret': fields.function(_amount_all, method=True, digits=(16,4), string='Tax Ret', multi='all'),
        'base_ret': fields.function(_amount_all, method=True, digits=(16,4), string='Base Ret', multi='all'),
        'retention_rate': fields.function(_retention_rate, method=True, string='Retention', type='float'),
        'base_amount': fields.float('Base Amount',    digits=(16, int(config['price_accuracy']))),
        'tax_amount': fields.float('Tax Amount',    digits=(16, int(config['price_accuracy']))),
        'rate_tax': fields.float('Rate Tax',    digits=(16, int(config['price_accuracy']))),
        'retention_amount': fields.float('Retention Amount',    digits=(16, int(config['price_accuracy']))),
        'rate_amount': fields.float('Rate Amount',    digits=(16, int(config['price_accuracy']))),
        'move_id': fields.many2one('account.move', 'Retention Movement', readonly=True, help="Link to the automatically generated account moves."),
    }

    def invoice_id_change(self, cr, uid, ids, invoice_id,company_id,type, context=None):
        if not invoice_id:
            return {}
        vals = {}
        p_ret = 0
        if type =='out_invoice':
            obj_company = pooler.get_pool(cr.dbname).get('res.company')
            company = obj_company.browse(cr, uid, company_id)
            if company.partner_id.retention:
                p_ret   = company.partner_id.retention
                invoice = pooler.get_pool(cr.dbname).get('account.invoice').read(cr, uid,[invoice_id],['number','retention'])
                if invoice and invoice[0]['retention']:
                    raise osv.except_osv('ERROR	', 'La factura ya fue retenida!!!')
                tax_invoice_ids = pooler.get_pool(cr.dbname).get('account.invoice.tax').search(cr, uid, [('invoice_id','=',invoice_id) ])
                tax_datos       = pooler.get_pool(cr.dbname).get('account.invoice.tax').read(cr, uid, tax_invoice_ids,['name','base','amount'])
                for tax in tax_datos:
                    #Se Obtiene el Grupo o tipo de Tax
                    tax_id      = pooler.get_pool(cr.dbname).get('account.tax').search(cr, uid, [('name','=',tax['name']) ])
                    tax_info    = pooler.get_pool(cr.dbname).get('account.tax').read(cr, uid, tax_id,['tax_group','amount'])
                    if tax_info and tax_info[0]['tax_group'] == 'vat':
                        alic  = tax_info[0]['amount'] * 100
                        iva   = tax['amount']
                        base  = tax['base']
                        retenc = iva * p_ret / 100
                        vals['name'] = invoice[0]['number']
                        vals['rate_amount'] = p_ret
                        vals['base_amount'] = base
                        vals['tax_amount'] = iva
                        vals['rate_tax'] = alic
                        vals['retention_amount'] = retenc
            else:
                raise osv.except_osv('ERROR	', 'La empresa no tiene definido el porcentaje de retencion!!!')

        return {'value':vals}

    ##action_done_cancel-------------------------------------------------------------------------------------
    #Anula el asiento contable de la factura y reversa el monto procesado
    #
    def action_done_cancel_invoice(self, cr, uid, ids, *args):
        if ids:
            context = None
            move_id = 0
            num_lines = 0
            ret_id = 0
            line = pooler.get_pool(cr.dbname).get('account.retention.line').read(cr, uid, ids,['invoice_id','move_id','retention_amount','retention_id'])
            if line and line[0]:
                ret_id = line[0]['retention_id'][0]
                cr.execute('SELECT id FROM account_retention_line WHERE retention_id = %d;'%(ret_id))
                ret_lines = cr.fetchall()
                num_lines = len(ret_lines)
                invoice_id = line[0]['invoice_id'][0]
                if line[0]['move_id']:
                    move_id    = line[0]['move_id'][0]
                pendiente  = line[0]['retention_amount']
                invoice_obj = pooler.get_pool(cr.dbname).get('account.invoice')
                invoice    = invoice_obj.browse(cr, uid, invoice_id)
                if invoice.state=='paid':
                    raise osv.except_osv('ERROR	', 'La factura esta pagada completamente debe desconciliar primero!!!')
                elif move_id:
                    account_move_obj = pooler.get_pool(cr.dbname).get('account.move')
                    account_move_obj.button_cancel(cr, uid, [move_id])
                    account_move_obj.unlink(cr, uid, [move_id])
                    pendiente += invoice.residual
                    invoice_obj.write(cr, uid, invoice_id, {'retention':False,'number_retention':'','residual':pendiente}, context)
                    cr.execute('DELETE FROM account_retention_line WHERE id = %d;'%(ids[0]))
                    if num_lines == 1 and ret_id:
                        cr.execute("UPDATE account_retention SET state='cancel' WHERE id = %d;"%(ret_id))
                else:
                    raise osv.except_osv('ERROR	', 'La factura no tiene el Nro. de Asiento para poder eliminarla del comprobante!!!') 
        return True

account_retention_line()
