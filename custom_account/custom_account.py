# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007 - 2009 Corvus Latinoamerica, C.A. (http://corvus.com.ve) All Rights Reserved
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

import time
import tools
from osv import fields,osv,orm
from tools import config
import ir
import pooler
import mx.DateTime
from mx.DateTime import RelativeDateTime

#-------------------------------------------------------------------------------------------------------------------------------
#'paymenterm_id': Se agrega dicho campo para poder establcer la relacion con la tabla 'account.payment.term'
#esta realcion permite asignale a las condicones de pago y determinado porcentaje de descuento,
#que sera usado especificamente por el modulo de Ventas.
#Se usa la estructura de los impuestos, para asociar el descuento a un determinada cuenta contable.
    
#-------------------------------------------------------------------------------------------------------------------------------
class account_tax(osv.osv):

    _inherit = "account.tax"
    _columns = {
        'paymenterm_id': fields.many2one('account.tax', 'Payment Term', select=True),
    }
    _defaults = {}
    
    def _unit_compute(self, cr, uid, taxes, price_unit, address_id=None, product=None, partner=None, pret=0.0): 
        taxes = self._applicable(cr, uid, taxes, price_unit, address_id, product, partner)

        res = [] 
        cur_price_unit=price_unit
        for tax in taxes:
            # we compute the amount for the current tax object and append it to the result

            data = {'id':tax.id, 
                            'name':tax.name, 
                            'account_collected_id':tax.account_collected_id.id,
                            'account_paid_id':tax.account_paid_id.id,
                            'base_code_id': tax.base_code_id.id,
                            'ref_base_code_id': tax.ref_base_code_id.id,
                            'sequence': tax.sequence, 
                            'base_sign': tax.base_sign, 
                            'tax_sign': tax.tax_sign,
                            'ref_base_sign': tax.ref_base_sign,
                            'ref_tax_sign': tax.ref_tax_sign,
                            'price_unit': cur_price_unit, 
                            'tax_code_id': tax.tax_code_id.id,
                            'ref_tax_code_id': tax.ref_tax_code_id.id,
                            'tax_group':tax.tax_group, 
            }
            res.append(data)
            if tax.type=='percent':
                amount = cur_price_unit * tax.amount 
                data['amount'] = amount
                data['amount_ret'] = 0.0
                if pret:
                    if tax.tax_group == 'vat':
                        amount_ret = cur_price_unit * tax.amount*(pret/100.0) 
                        data['amount_ret'] = amount_ret
            elif tax.type=='fixed':
                data['amount'] = tax.amount
            elif tax.type=='code': 
                address = address_id and self.pool.get('res.partner.address').browse(cr, uid, address_id) or None
                localdict = {'price_unit':cur_price_unit, 'address':address, 'product':product, 'partner':partner}
                exec tax.python_compute in localdict
                amount = localdict['result']
                data['amount'] = amount
            elif tax.type=='balance': 
                data['amount'] = cur_price_unit - reduce(lambda x,y: y.get('amount',0.0)+x, res, 0.0)
                data['balance'] = cur_price_unit

            amount2 = data['amount'] 
            if len(tax.child_ids): 
                if tax.child_depend:
                    latest = res.pop()
                amount = amount2
                child_tax = self._unit_compute(cr, uid, tax.child_ids, amount, address_id, product, partner)
                res.extend(child_tax)
                if tax.child_depend: 
                    for r in res:
                        for name in ('base','ref_base'):
                            if latest[name+'_code_id'] and latest[name+'_sign'] and not r[name+'_code_id']:
                                r[name+'_code_id'] = latest[name+'_code_id']
                                r[name+'_sign'] = latest[name+'_sign']
                                r['price_unit'] = latest['price_unit']
                                latest[name+'_code_id'] = False
                        for name in ('tax','ref_tax'):
                            if latest[name+'_code_id'] and latest[name+'_sign'] and not r[name+'_code_id']:
                                r[name+'_code_id'] = latest[name+'_code_id']
                                r[name+'_sign'] = latest[name+'_sign']
                                r['amount'] = data['amount']
                                latest[name+'_code_id'] = False
            if tax.include_base_amount:
                cur_price_unit+=amount2
        #print 'res salir: ',res
        return res 

    def compute(self, cr, uid, taxes, price_unit, quantity, address_id=None, product=None, partner=None, pret=0.0): 

        """
        Compute tax values for given PRICE_UNIT, QUANTITY and a buyer/seller ADDRESS_ID.

        RETURN:
            [ tax ]
            tax = {'name':'', 'amount':0.0, 'account_collected_id':1, 'account_paid_id':2}
            one tax for each tax id in IDS and their childs
        """ 
        res = self._unit_compute(cr, uid, taxes, price_unit, address_id, product, partner, pret)
        total = 0.0
        for r in res:
            if r.get('balance',False):
                r['amount'] = round(r['balance'] * quantity, 2) - total
            else:
                r['amount'] = round(r['amount'] * quantity, 2)
                total += r['amount']
                r['amount_ret'] = round(r['amount_ret'] * quantity, 2)

        return res
account_tax()



#-------------------------------------------------------------------------------------------------------------------------
#Se agrega a la tabla 'account_payment_term' el campo 'tax_id' para poder asignar a los terminos de pago
#un porcentaje de descuento. Se usa la tabla de impuestos para declarar estos descuentos. 
#Esta funcionalidad es aplicada en las ventas
#-------------------------------------------------------------------------------------------------------------------------
class account_payment_term(osv.osv):

    _inherit = "account.payment.term"
    _columns = {
        'tax_id': fields.many2many('account.tax', 'account_payment_tax_rel', 'paymenterm_id', 'tax_id', 'Dscto'),
        'contado': fields.boolean('Contado'),
    }
    _defaults = {}
account_payment_term()



#-------------------------------------------------------------------------------------------------------------------------
#Se agregan campos requeridos para procesar las facturas de las compras y de las ventas
#-------------------------------------------------------------------------------------------------------------------------
class account_invoice(osv.osv):

    _inherit = "account.invoice"
    _columns = {
        'date_document': fields.date('Document Date'),
        'date_received': fields.date('Purchase Date'),
        'number_document': fields.char('Document Number', size=20),
        'number_control': fields.char('Invoice Control', size=20),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'),
        'code_zone_id': fields.many2one('res.partner.zone', 'Code Zone'),
        'nota_atencion': fields.char('Nota Atencion', size=100),
        'nota_atencion_ids': fields.many2many('nota.atencion', 'account_nota_atencion_rel', 'invoice_id', 'nota_atencion_id', 'Notas Atencion'),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ('in_invoice_ad','Supplier Invoice Admin'),
            ],'Type', readonly=True, select=True),
        'exentas': fields.boolean('Exentas'),
        'no_sujetas': fields.boolean('No Sujetas'),
        'parent_id': fields.many2one('account.invoice', 'Parent Invoice', select=True),
        'retention': fields.boolean('Retention', readonly=True),
        'p_ret': fields.float('P Retention', digits=(14,4)),
        'number_retention': fields.char('Numero de Retencion', size=64),
        'islr': fields.boolean('Islr', readonly=True),
        'islr_type_id': fields.many2one('account.islr.tax.type','ISLR'),
        'islr_number': fields.char('ISLR number', size=64),
        'printed': fields.boolean('Printed'),
        'internal': fields.boolean('Invoice or Refund Internal'),
        'manual': fields.boolean('Invoice or Refund Internal Manual'),
        'adjustment': fields.boolean('Invoice Refund Internal Adjustment'),
        'check': fields.boolean('Check return'),
        'refund_supplier': fields.boolean('Refund Supplier'),
    }
    _defaults = {
        'date_invoice': lambda *a: time.strftime('%Y-%m-%d'),
        'number_document': lambda *a: '',
        'number_control': lambda *a: '',
        'name': lambda obj, cr, uid, context: obj.pool.get('account.invoice').ad_seq_get(cr, uid,context),
        'printed': lambda *a: False,
        'exentas': lambda *a: False,
        'no_sujetas': lambda *a: False,
        'internal': lambda *a: False,
        'manual': lambda *a: False,
        'retention':lambda *a: False,
        'adjustment':lambda *a: False,
        'check':lambda *a: False,
        'refund_supplier':lambda *a: False
        }

    ##ad_seq_get-------------------------------------------------------------------------------------------------------
    #Asigna el numero a la fcatura de compra y ventas, el cual puede ser temporal, ya que solo cuando se guarda
    #la factura se asigna el nro definitivo
    #
    def ad_seq_get(self, cr, uid, context=None):
        ap_obj = self.pool.get('account.period')
        ap_ids = ap_obj.find(cr, uid)
        #ap = ap_obj.browse(cr, uid, ap_ids)[0]
        #to_update = {'suffix':'/'+ap.code}
        pool_seq=self.pool.get('ir.sequence')
        res = False
        #self.pool.get('ir.sequence').get(cr, uid, 'account.invoice.out_invoice')
        if context and context.has_key('type'):
            if context['type'] == 'in_refund' and context.has_key('refund_supplier'):
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='account.invoice.in_refund_prove' and active=True")
                res = cr.dictfetchone()
            if context['type'] == 'in_refund' and context.has_key('check'):
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='account.invoice.in_refund_chcli' and active=True")
                res = cr.dictfetchone()
            if context['type'] == 'in_refund' and context.has_key('internal'):
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='account.invoice.in_refund_client' and active=True")
                res = cr.dictfetchone()
            if context['type'] == 'in_refund' and context.has_key('adjustment'):
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='account.invoice.in_refund_ajcli' and active=True")
                res = cr.dictfetchone()
                print context 
            if context['type'] == 'in_invoice_ad':
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='account.invoice.in_invoice' and active=True")
                res = cr.dictfetchone()
                #res.update(to_update)
            if context['type'] == 'out_invoice':
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='account.invoice.sales' and active=True")
                res = cr.dictfetchone()
            if context['type'] == 'out_refund' and context.has_key('adjustment'):
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='account.invoice.out_refund_ajcli' and active=True")
                res = cr.dictfetchone()
            elif context['type'] == 'out_refund':
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='account.invoice.out_refund' and active=True")
                res = cr.dictfetchone()
        if res:
            if res['number_next']:
                return pool_seq._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + pool_seq._process(res['suffix'])
            else:
                return pool_seq._process(res['prefix']) + pool_seq._process(res['suffix'])
        return False
    

    ##create------------------------------------------------------------------------------------------------------------
    #Este porceso se llama cada vez que se crea una nueva compra o una venta manual.
    #Asigna el numero de factura de compra definitivo y aumenta el contador en la secuencia 'account.invoice.in_invoice'
    def create(self, cr, user, vals, context=None):
        #print "CONTEX ",context, " vals ",vals   
        if context and context.has_key('type') and context['type'] == 'out_invoice':
            nrofventa=self.pool.get('ir.sequence').get(cr, user, 'account.invoice.sales')
            vals['name']  =nrofventa
            vals['number']=nrofventa
        if vals and vals.has_key('adjustment') and context and context.has_key('type') and context['type'] == 'out_refund':
            nronc=self.pool.get('ir.sequence').get(cr, user, 'account.invoice.out_refund_ajcli')
            vals['name']   = nronc
            vals['number'] = nronc
        elif context and context.has_key('type') and context['type'] == 'out_refund':
            nronc=self.pool.get('ir.sequence').get(cr, user, 'account.invoice.out_refund')
            vals['name']  = nronc
            vals['number']= nronc
        
        if context and context.has_key('type') and context['type'] == 'in_invoice_ad':
            #ap_obj = self.pool.get('account.period')
            #ap_ids = ap_obj.find(cr, user)
            #ap = ap_obj.browse(cr, user, ap_ids)[0]  #Para asignar el numero segun el periodo
            nrofprov=self.pool.get('ir.sequence').get(cr, user, 'account.invoice.in_invoice')
            #vals['name']=nrofprov+'/'+ap.code
            vals['name']   = nrofprov
            vals['number'] = nrofprov
        if vals and vals.has_key('refund_supplier') and context and context['type'] == 'in_refund':
            nrond=self.pool.get('ir.sequence').get(cr, user, 'account.invoice.in_refund_prove')
            vals['name']  =nrond
            vals['number']=nrond
        if vals and vals.has_key('internal') and context and context['type'] == 'in_refund':
            nrond=self.pool.get('ir.sequence').get(cr, user, 'account.invoice.in_refund_client')
            vals['name']  =nrond
            vals['number']=nrond
        if vals and vals.has_key('adjustment') and context and context['type'] == 'in_refund':
            nrond=self.pool.get('ir.sequence').get(cr, user, 'account.invoice.in_refund_ajcli')
            vals['name']  =nrond
            vals['number']=nrond
        if vals and vals.has_key('check') and context and context['type'] == 'in_refund':
            nrond=self.pool.get('ir.sequence').get(cr, user, 'account.invoice.in_refund_chcli')
            vals['name']  =nrond
            vals['number']=nrond
        if vals and vals.has_key('type') and vals['type'] == 'in_refund' and  vals.has_key('invoice_line') and vals['invoice_line']:
            line = vals['invoice_line'][0][2]
            sup_id  = line['suppinfo_id']
            price_h = line['price_historic']
            if sup_id:
                vals['invoice_line'][0][2]['suppinfo_id']= sup_id[0]
            if price_h:
                vals['invoice_line'][0][2]['price_historic']= price_h[0]
        return super(account_invoice,self).create(cr, user, vals, context)


    ##name_get------------------------------------------------------------------------------------------------------------
    #Se sobreescribe este metodo para incluir el tipo 'in_invoice_ad' que corresponde a las facturas de compras de los Gastos Administrativos 
    #
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        types = {
                'out_invoice': '',
                'in_invoice': '',
                'out_refund': '',
                'in_refund': '',
                'in_invoice_ad': '',
                }
        return [(r['id'], types[r['type']]+' '+(r['name'] or '')) for r in self.read(cr, uid, ids, ['type', 'name'], context, load='_classic_write')]


    ##_refund_cleanup_lines--------------------------------------------------------------------------------------------
    # Se modifica para agregar la cuenta de reserva y obtener solamente el id 
    # Realizado por: Javier Duran
    # Fecha:26-08-09

    def _refund_cleanup_lines(self, lines):
        for line in lines:
            del line['id']
            del line['invoice_id']
            if 'account_id' in line:
                line['account_id'] = line.get('account_id', False) and line['account_id'][0]
            if 'product_id' in line:
                line['product_id'] = line.get('product_id', False) and line['product_id'][0]
            if 'uos_id' in line:
                line['uos_id'] = line.get('uos_id', False) and line['uos_id'][0]
            if 'invoice_line_tax_id' in line:
                line['invoice_line_tax_id'] = [(6,0, line.get('invoice_line_tax_id', [])) ]
            if 'account_analytic_id' in line:
                line['account_analytic_id'] = line.get('account_analytic_id', False) and line['account_analytic_id'][0]
            if 'tax_code_id' in line :
                if isinstance(line['tax_code_id'],tuple)  and len(line['tax_code_id']) >0 :
                    line['tax_code_id'] = line['tax_code_id'][0]
            if 'base_code_id' in line :
                if isinstance(line['base_code_id'],tuple)  and len(line['base_code_id']) >0 :
                    line['base_code_id'] = line['base_code_id'][0]
            if 'account_res_id' in line:
                line['account_res_id'] = line.get('account_res_id', False) and line['account_res_id'][0]
        return map(lambda x: (0,0,x), lines)


    #refund--------------------------------------------------------------------------------------------------------------------------
    #Se sobreescribe el metodo 'refund':
    #para asignar el Nro de Nota de Debito, se usa la secuencia 'account.invoice.in_refund'
    #para asignar el Nro de Nota de Credito, se una la secuencia 'account.invoice.out_refund'
    #para contemplar el tipo de facturas de gastos administrativos en las Notas de Debito 'in_invoice_ad'
    #-------------------------------------------------------------------------------------------------------------------------------
    def refund(self, cr, uid, ids, date=None, period_id=None, description=None):
        invoices = self.read(cr, uid, ids, ['name', 'type', 'number', 'reference', 'comment', 'date_due', 'partner_id', 'address_contact_id', 'address_invoice_id', 'partner_contact', 'partner_insite', 'partner_ref', 'payment_term', 'account_id', 'currency_id', 'invoice_line', 'tax_line', 'journal_id','p_ret','warehouse_id','guide_id','code_zone_id'])
        #-----------------------------------------------------------------------------------------------------
        #Modificado:  Corvus Latinoamerica
        # Asignarle el nro de nota de debito
        invoices[0]['reference'] = invoices[0]['name']
        invoices[0]['parent_id'] = ids[0]
        #asignarle el Almacen 
        if invoices[0]['warehouse_id']:
            invoices[0]['warehouse_id'] = invoices[0]['warehouse_id'][0]
        #Se obtiene el Nro. de la Nota dependiendo del tipo Credito o Debito
        if invoices[0]['type'] == "out_invoice":            
            nro =self.pool.get('ir.sequence').get(cr, uid, 'account.invoice.out_refund')
            number_refund = nro
            if invoices[0]['guide_id']:
                invoices[0]['guide_id'] = invoices[0]['guide_id'][0]
            if invoices[0]['code_zone_id']:
                invoices[0]['code_zone_id'] = invoices[0]['code_zone_id'][0]
        else:
            nro =self.pool.get('ir.sequence').get(cr, uid, 'account.invoice.in_refund')
            number_refund = False    
        invoices[0]['reference'] = invoices[0]['name']                
        invoices[0]['name'] = nro
        new_ids = []
        for invoice in invoices:
            del invoice['id']
            #Modificado: Corvus Latinoamerica
            #Se agrega 'in_invoice_ad': 'in_refund'
            #para que sean contempladas la notas de debito para este tipo de facturas correspondiente 
            #a las compras de Gastos Administrativos
            type_dict = {
                'out_invoice': 'out_refund', # Customer Invoice
                'in_invoice': 'in_refund',   # Supplier Invoice
                'out_refund': 'out_invoice', # Customer Refund
                'in_refund': 'in_invoice',   # Supplier Refund
                'in_invoice_ad': 'in_refund',   # Supplier Invoice 
            }
            invoice_lines = self.pool.get('account.invoice.line').read(cr, uid, invoice['invoice_line'])
            invoice_lines = self._refund_cleanup_lines(invoice_lines)
            
            #Modificado: Corvus Latinoamerica
            #El siguiente 'for inlines in invoice_lines' descarta el precio historico que pueda tener una determinada 
            #factura de Compra de Gestion al momento de crearle la Nota de Debito 
            cont = 0
            for inlines in invoice_lines:
                vals = inlines[2]             
                if vals.has_key('suppinfo_id') and vals['suppinfo_id']:
                    invoice_lines[cont][2]['suppinfo_id'] = False
                    invoice_lines[cont][2]['price_historic'] = False
                cont += 1
            
            tax_lines = self.pool.get('account.invoice.tax').read(cr, uid, invoice['tax_line'])
            tax_lines = filter(lambda l: l['manual'], tax_lines)
            tax_lines = self._refund_cleanup_lines(tax_lines)
            date = time.strftime('%Y-%m-%d')
            #Se obtiene Period Actual
            period = self.pool.get('account.period').search(cr, uid, [('date_start','<=',date),('date_stop', '>=', date) ])
            if period:
                period_id = period[0]             
            invoice.update({
                'type': type_dict[invoice['type']],
                'date_invoice': date,
                'state': 'draft',
                'number': number_refund,
                'invoice_line': invoice_lines,
                'tax_line': tax_lines
            })
            if period_id :
                invoice.update({'period_id': period_id,})
            #Corvus Latinoamerica
            #Se comenta la condicion 'id description' para evitar que asigne por defecto el valor de la variable 'description' 
            #al campo 'name' ya que este posee el Nro de la Nota 
            #
            #if description :
            #    invoice.update({'name': description, })
            
            # take the id part of the tuple returned for many2one fields
            for field in ('address_contact_id', 'address_invoice_id', 'partner_id','account_id', 'currency_id', 'payment_term', 'journal_id'):
                invoice[field] = invoice[field] and invoice[field][0]
            # create the new invoice
            new_ids.append(self.create(cr, uid, invoice))
        return new_ids


    ##action_move_create--------------------------------------------------------------------------------------------
    # Se modifica para agregar el monto subtotal de la compra en el asiento
    # Realizado por: Javier Duran
    # Fecha:03-07-09
        
    def action_move_create(self, cr, uid, ids, *args):
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        context = {}
        for inv in self.browse(cr, uid, ids):
            if inv.move_id:
                continue

            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice':time.strftime('%Y-%m-%d')})
            company_currency = inv.company_id.currency_id.id
            # create the analytical lines
            line_ids = self.read(cr, uid, [inv.id], ['invoice_line'])[0]['invoice_line']
            ils = self.pool.get('account.invoice.line').read(cr, uid, line_ids)
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, inv.id)
            #print 'IML FACTURA:', iml
            # check if taxes are all computed
            mov_lst = []
            #guardando los movimientos provenientes de las lineas de facturas
            for mov in iml:
                temp = str(mov['account_id'])
                temp += '-'+str('tax_code_id' in mov and mov['tax_code_id'] or "False")
                temp += '-'+str('product_id' in mov and mov['product_id'] or "False")
                temp += '-'+str('account_analytic_id' in mov and mov['account_analytic_id'] or "False")
                mov_lst.append(temp)

            context.update({'lang': inv.partner_id.lang})
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=context)
            if not inv.tax_line:
                for tax in compute_taxes.values():
                    ait_obj.create(cr, uid, tax)
            else:
                tax_key = []
                for tax in inv.tax_line:
                    if tax.manual:
                        continue
                    key = (tax.tax_code_id.id, tax.base_code_id.id, tax.account_id.id)
                    tax_key.append(key)
                    if not key in compute_taxes:
                        raise osv.except_osv(_('Warning !'), _('Global taxes defined, but are not in invoice lines !'))
                    base = compute_taxes[key]['base']
                    if abs(base - tax.base) > inv.company_id.currency_id.rounding:
                        raise osv.except_osv(_('Warning !'), _('Tax base different !\nClick on compute to update tax base'))
                for key in compute_taxes:
                    if not key in tax_key:
                        raise osv.except_osv(_('Warning !'), _('Taxes missing !'))

            if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0):
                raise osv.except_osv(_('Bad total !'), _('Please verify the price of the invoice !\nThe real total does not match the computed total.'))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)

            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
            else:
                ref = self._convert_ref(cr, uid, inv.number)

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            #print 'iml FACTURAS MAS IMPUESTO:', iml
            for i in iml:
                if inv.currency_id.id != company_currency:
                    i['currency_id'] = inv.currency_id.id
                    i['amount_currency'] = i['price']
                    i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
                            company_currency, i['price'],
                            context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
                else:
                    i['amount_currency'] = False
                    i['currency_id'] = False
                i['ref'] = ref
                if inv.type in ('out_invoice','in_refund'):
                    total += i['price']
                    total_currency += i['amount_currency'] or i['price']
                    i['price'] = - i['price']
                else:
                    total -= i['price']
                    total_currency -= i['amount_currency'] or i['price']
            acc_id = inv.account_id.id

            name = inv['name'] or '/'
            totlines = False
            if inv.payment_term:
                totlines = self.pool.get('account.payment.term').compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid,
                                company_currency, inv.currency_id.id, t[1])
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and  amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                #print 'TOTAL: ',total
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity' : inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref
            })

            #print 'iml Factura mas pago:', iml
            #modificando el asiento con el nuevo monto de compra
            #y agregando el asiento de la cuenta de reserva
            if inv.type in ('in_invoice','out_invoice','out_refund'):
                for l in iml:
                    tmp = str(l['account_id'])
                    tmp += '-'+str('tax_code_id' in l and l['tax_code_id'] or "False")
                    tmp += '-'+str('product_id' in l and l['product_id'] or "False")
                    tmp += '-'+str('account_analytic_id' in l and l['account_analytic_id'] or "False")
                    #print 'TMP: ******',tmp
                    if tmp in mov_lst:
                        p_comp = 0.0
                        if inv.type == 'out_refund': 
                            p_fact = round(l['price_fact'] * l['quantity'],4)
                            #if l['price_fact']:
                                #p_comp =   (l['price'] - p_fact)
                                #l['price'] = p_fact
                            cta_reserva = l['reserva_ventas']
                            if l['cta_prod_ventas']:
                                l['account_id'] = l['cta_prod_ventas']
                        
                        if inv.type == 'out_invoice': 
                            #p_fact = round(l['price_fact'] * l['quantity'],4)
                            #if l['price'] < 0 and l['price_fact']:
                            #    l['price'] *=  -1
                            #if l['price_fact']:
                            #    p_comp =  - (l['price'] - p_fact)
                            #    l['price'] = p_fact * -1  
                            cta_reserva = l['reserva_ventas']
                            #print 'PRICE: ',l['price'],'PRICE_VENTT: ',p_fact,'P_COMP: ',p_comp
                            if l['cta_prod_ventas']:
                                l['account_id'] = l['cta_prod_ventas']

                        if inv.type == 'in_invoice':
                            #p_comp = - (l['price_comp'] - l['price'])
                            #l['price'] = l['price_comp']
                            cta_reserva = l['account_res_id']
                        #else:
                        #    p_comp =  (l['price_comp'] + l['price'])
                        #    l['price'] = - l['price_comp']

                        if p_comp:
                            iml.append({
                                'type': 'dest',
                                'name': 'RES:'+l['name'][:60],
                                'price': p_comp,
                                'account_id': cta_reserva,
                                'date_maturity' : inv.date_due or False,
                                'amount_currency': diff_currency_p and  amount_currency or False,
                                'currency_id': diff_currency_p and inv.currency_id.id or False,
                                'ref': ref,
                            })
                    else:
                        continue

            #--------------------------------------------------------------------------------------------
            #print 'iml Reserva:', iml 
            date = inv.date_invoice or time.strftime('%Y-%m-%d')
            part = inv.partner_id.id

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part, date, context={})) ,iml)

            if inv.journal_id.group_invoice_lines:
                line2 = {}
                for x, y, l in line:
                    tmp = str(l['account_id'])
                    tmp += '-'+str('tax_code_id' in l and l['tax_code_id'] or "False")
                    tmp += '-'+str('product_id' in l and l['product_id'] or "False")
                    tmp += '-'+str('analytic_account_id' in l and l['analytic_account_id'] or "False")

                    if tmp in line2:
                        am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                        line2[tmp]['debit'] = (am > 0) and am or 0.0
                        line2[tmp]['credit'] = (am < 0) and -am or 0.0
                        line2[tmp]['tax_amount'] += l['tax_amount']
                        line2[tmp]['analytic_lines'] += l['analytic_lines']
                    else:
                        line2[tmp] = l
                line = []
                for key, val in line2.items():
                    line.append((0,0,val))


            journal_id = inv.journal_id.id #self._get_journal(cr, uid, {'type': inv['type']})
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
            if journal.centralisation:
                raise osv.except_osv(_('UserError'),
                        _('Cannot create invoice move on centralised journal'))
            #print 'LINE_ID: ',line
            move = {'ref': inv.number, 'line_id': line, 'journal_id': journal_id, 'date': date}
            period_id=inv.period_id and inv.period_id.id or False
            if not period_id:
                period_ids= self.pool.get('account.period').search(cr,uid,[('date_start','<=',inv.date_invoice or time.strftime('%Y-%m-%d')),('date_stop','>=',inv.date_invoice or time.strftime('%Y-%m-%d'))])
                if len(period_ids):
                    period_id=period_ids[0]
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            #print 'ASIENTO COMPRA: ',move
            move_id = self.pool.get('account.move').create(cr, uid, move)
            new_move_name = self.pool.get('account.move').browse(cr, uid, move_id).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name})
            self.pool.get('account.move').post(cr, uid, [move_id])
        self._log_event(cr, uid, ids)
        return True

        #-----------------------------------------------------------------------------------------
        #Creado: Corvus latinoamerica
        #Fecha: 2/11/2009
        #Autor: Tomas Henriquez
        #Nota: Se aplican redondeos para evitar errores de validacion del total
        #      Se coloca en l1 y l2 la fecha para guardarla en account_invoice_line correctamente 

    def pay_and_reconcile(self, cr, uid, ids, pay_amount, pay_account_id, period_id, pay_journal_id, writeoff_acc_id, writeoff_period_id, writeoff_journal_id, context=None, name=''):
        if context is None:
            context = {}
        #TODO check if we can use different period for payment and the writeoff line
        assert len(ids)==1, "Can only pay one invoice at a time"
        invoice = self.browse(cr, uid, ids[0])
        src_account_id = invoice.account_id.id
        # Take the seq as name for move
        types = {'out_invoice': -1, 'in_invoice': 1, 'in_invoice_ad': 1, 'out_refund': 1, 'in_refund': -1}
        direction = types[invoice.type]
        #take the choosen date
        #print "pay_and_reconcile-CONTEXT",context 
        if 'date_p' in context and context['date_p']:
            date=context['date_p']
        else:
            date=time.strftime('%Y-%m-%d')
        #print "FECHA-DATE_P",date 
        l1 = {
            'debit': direction * pay_amount>0 and direction * pay_amount,
            'credit': direction * pay_amount<0 and - direction * pay_amount,
            'account_id': src_account_id,
            'partner_id': invoice.partner_id.id,
            'ref':invoice.number,
            'date':date,
        }
        l2 = {
            'debit': direction * pay_amount<0 and - direction * pay_amount,
            'credit': direction * pay_amount>0 and direction * pay_amount,
            'account_id': pay_account_id,
            'partner_id': invoice.partner_id.id,
            'ref':invoice.number,
            'date':date,
        }
 
        if not name:
            name = invoice.invoice_line and invoice.invoice_line[0].name or invoice.number
        l1['name'] = name
        l2['name'] = name

        lines = [(0, 0, l1), (0, 0, l2)]
        move = {'ref': invoice.number, 'line_id': lines, 'journal_id': pay_journal_id, 'period_id': period_id, 'date': date}
        move_id = self.pool.get('account.move').create(cr, uid, move)

        line_ids = []
        total = 0.0
        line = self.pool.get('account.move.line')
        cr.execute('select id from account_move_line where move_id in ('+str(move_id)+','+str(invoice.move_id.id)+')')
        lines = line.browse(cr, uid, map(lambda x: x[0], cr.fetchall()) )
        for l in lines+invoice.payment_ids:
            if l.account_id.id==src_account_id:
                line_ids.append(l.id)
                total += (l.debit or 0.0) - (l.credit or 0.0)

        #Redondeamos ya que da errores para la reconciliacion
        #############################################
        if total > -0.000001 and total < 0 :
            total = 0.0
        #############################################
        if (not total) or writeoff_acc_id:
            self.pool.get('account.move.line').reconcile(cr, uid, line_ids, 'manual', writeoff_acc_id, writeoff_period_id, writeoff_journal_id, context)
        else:
            self.pool.get('account.move.line').reconcile_partial(cr, uid, line_ids, 'manual', context)

        # Update the stored value (fields.function), so we write to trigger recompute
        self.pool.get('account.invoice').write(cr, uid, ids, {}, context=context)
        if move_id:
            return move_id
        return True


    ##parent_id_change------------------------------------------ 
    def parent_id_change(self, cr, uid, ids, idparent, context=None):
        vals   ={}
        if not idparent:
            return {'value':vals}
        resp = self.pool.get('account.invoice').browse(cr, uid, idparent, context=context)
        if resp:
            vals['partner_id'] = resp.partner_id.id
            if resp.warehouse_id.id:
                vals['warehouse_id'] = resp.warehouse_id.id
            vals['reference'] = resp.number
            if resp.payment_term.id:
                vals['payment_term'] = resp.payment_term.id
            if resp.partner_id.id:
                res = self.pool.get('res.partner').address_get(cr, uid, [resp.partner_id.id], ['contact', 'invoice'])
                contact_addr_id = res['contact']
                invoice_addr_id = res['invoice']
                vals['address_contact_id'] = contact_addr_id
                vals['address_invoice_id'] = invoice_addr_id
                partner = self.pool.get('res.partner').browse(cr, uid, resp.partner_id.id)
                acc_id = partner.property_account_receivable.id
                vals['account_id'] = acc_id
        return {'value':vals}


    #Se sobreescribe el metodo para obtener el porcentaje de retencion del parnert
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
            date_invoice=False, payment_term=False, partner_bank_id=False):
        invoice_addr_id = False
        contact_addr_id = False
        partner_payment_term = False
        acc_id = False
        bank_id = False
        fiscal_position = False

        opt = [('uid', str(uid))]
        if partner_id:

            opt.insert(0, ('id', partner_id))
            res = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['contact', 'invoice'])
            contact_addr_id = res['contact']
            invoice_addr_id = res['invoice']
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if type in ('out_invoice', 'out_refund'):
                acc_id = p.property_account_receivable.id
            else:
                acc_id = p.property_account_payable.id
            fiscal_position = p.property_account_position and p.property_account_position.id or False
            partner_payment_term = p.property_payment_term and p.property_payment_term.id or False
            if p.bank_ids:
                bank_id = p.bank_ids[0].id

        result = {'value': {
            'address_contact_id': contact_addr_id,
            'address_invoice_id': invoice_addr_id,
            'account_id': acc_id,
            'payment_term': partner_payment_term,
            'fiscal_position': fiscal_position,
            'p_ret': p.retention,
            }
        }

        if type in ('in_invoice', 'in_refund'):
            result['value']['partner_bank'] = bank_id

        if payment_term != partner_payment_term:
            if partner_payment_term:
                to_update = self.onchange_payment_term_date_invoice(
                    cr,uid,ids,partner_payment_term,date_invoice)
                result['value'].update(to_update['value'])
            else:
                result['value']['date_due'] = False

        if partner_bank_id != bank_id:
            to_update = self.onchange_partner_bank(cr, uid, ids, bank_id)
            result['value'].update(to_update['value'])
        return result
account_invoice()

#-------------------------------------------------------------------------------------------------------------------------
#Se agregan campos a la tabla 'account_invoice_line' para procesar tanto las facturas de compras como las de ventas
#ajustadas a la metodologia de la empresa
#Se crean nuevos metodos: 'price_historic_change','new_price_unit'
#-------------------------------------------------------------------------------------------------------------------------
class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"

    ##_amount_line_vent--------------------------------------------------------------------------------------------
    # Cacula el monto subtotal de la venta en la linea
    # Realizado por: William Saurez
    # Fecha:03-07-09
    def _amount_line_vent(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        resp = {}
        for line in self.browse(cr, uid, ids):
            resp[line.id] = round(line.price_fact * line.quantity,4)
        return resp
 
    ##_amount_line_comp--------------------------------------------------------------------------------------------
    # Cacula el monto subtotal de la compra en la linea
    # Realizado por: Javier Duran
    # Fecha:03-07-09   
    def _amount_line_comp(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = round(line.price_standard * line.quantity,4)
        return res


    _columns = {
        'price_standard': fields.float('Standard Price', digits=(16, int(config['price_accuracy']))),
        'price_fact': fields.float('Invoice Price', digits=(16, int(config['price_accuracy']))),
        'quantity_received': fields.float('Quantity Received', digits=(16,2)),
        'suppinfo_id': fields.many2one('product.supplierinfo', 'Supplier info' ),
        'price_historic': fields.many2one('pricelist.partnerinfo', 'Price Historic'),
        'price_subtotal_comp': fields.function(_amount_line_comp, method=True, string='Subtotal Compra',store=True),
        'price_subtotal_vent': fields.function(_amount_line_vent, method=True, string='Subtotal Venta',store=True),
        'account_res_id': fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], help="The reserv account related to the selected product."),
        'islr_id': fields.many2one('account.islr.tax.type','ISLR'),
        'concept_id': fields.many2one('concept.invoice.refund', 'Concept Note'),
    }
    _defaults = {
        'price_standard':      lambda *a: 0,
        'price_fact':          lambda *a: 0,
        'quantity_received':   lambda *a: 0,
    }

    ##price_historic_change------------------------------------------------------------------------------------------------------------
    #Modulo de compras de gestion
    #Se crea este nuevo porceso que calcula el nuevo precio unitario que se aplicara al producto. Basado en una
    #lista de precios historicos
    #
    def price_historic_change(self, cr, uid, ids,price_id,partner_id,product_id):
        v   ={}
        dscto = 0
        if price_id and partner_id:
            price_historic = pooler.get_pool(cr.dbname).get('pricelist.partnerinfo').read(cr,uid, [price_id],['sup_price'])
            sqlp =  """
            SELECT     t.categ_id
            FROM       product_product AS p
            INNER JOIN product_template AS t ON p.product_tmpl_id=t.id
            WHERE p.id=%d;"""%product_id
            cr.execute (sqlp)
            rslt =cr.fetchall()
            categ_p = rslt[0][0]

            #se obtiene la lista de precio del proveedor
            priceclist_id = self.pool.get('res.partner').browse(cr, uid, partner_id).property_product_pricelist_purchase.id
            version_ids = pooler.get_pool(cr.dbname).get('product.pricelist.version').search(cr,uid, [('pricelist_id','=',priceclist_id), ('active', '=',True) ])

            if len(version_ids) > 1:
                fecha = time.strftime('%Y-%m-%d')
                version_ids = pooler.get_pool(cr.dbname).get('product.pricelist.version').search(cr,uid, [('pricelist_id','=',priceclist_id), ('active', '=',True), ('date_start','<=',fecha),('date_end','>=',fecha)])

            #NOTAS - PENDIENTES :
            #        1.- No se toma en cuenta las lista estan encadenadas
            #        2.- No se toma en cuenta si la lista aplica para un producto en particular


            if version_ids:
                items_ids = pooler.get_pool(cr.dbname).get('product.pricelist.item').search(cr,uid, [('price_version_id','=',version_ids[0]) ])
                if len(items_ids) == 1:
                    discount = pooler.get_pool(cr.dbname).get('product.pricelist.item').read(cr,uid, items_ids,['price_discount','categ_id','product_id'])
                    categoria = discount[0]['categ_id']
                    discount_val =  discount[0]['price_discount']
                    if discount_val > 0:
                        if categoria:
                            if categoria == categ_p:
                                dscto = price_historic[0]['sup_price']    *  discount_val
                        else:
                            dscto = price_historic[0]['sup_price']    *  discount_val
                else:
                    sqli = """
                    SELECT     price_discount,categ_id,product_id,name
                      FROM       product_pricelist_item
                      WHERE price_version_id = %d
                      ORDER BY sequence;"""%version_ids[0]
                    cr.execute (sqli)
                    for lst in cr.fetchall():
                        if lst[1]:
                            if lst[1] == categ_p:
                                dscto = price_historic[0]['sup_price']    *  lst[0]
                                break
                        else:
                                dscto = price_historic[0]['sup_price']    *  lst[0]
                                break
                price  = price_historic[0]['sup_price'] - dscto
                v['price_unit'] =     price
        return{'value':v}

    ##new_price_unit--------------------------------------------------------------------------------------------
    # Proceso para el Modulo de compras, la finalidad de este es guardar en la tabla el precio obtenido
    # del historico, es necesario ya que los campos en la vista estan de solo lectura
    # Realizado por: William Suarez

    def new_price_unit(self, cr, uid, ids, context={}):
        if not ids:
            return
        listprice = pooler.get_pool(cr.dbname).get('account.invoice.line').read(cr,uid, ids,['price_historic'])
        if listprice:
            price = listprice[0]
            if price.has_key('price_historic') and price['price_historic']:
                newprice = price['price_historic'][1]
                self.write(cr, uid, ids, {'price_unit': newprice})
        return


    ##product_id_change--------------------------------------------------------------------------------------------
    # Se agrega el campo account_res_id y price_standard para su actualizacion
    # Realizado por: Javier Duran
    # Fecha:03-07-09

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, context=None):
        if context is None:
            context = {}
        if not partner_id:
            raise osv.except_osv(_('No Partner Defined !'),_("You must first select a partner !") )
        if not product:
            if type in ('in_invoice', 'in_refund'):
                return {'domain':{'product_uom':[]}}
            else:
                return {'value': {'price_unit': 0.0}, 'domain':{'product_uom':[]}}
        part = self.pool.get('res.partner').browse(cr, uid, partner_id)
        fpos = fposition_id and self.pool.get('account.fiscal.position').browse(cr, uid, fposition_id) or False

        lang=part.lang
        context.update({'lang': lang})
        result = {}
        res = self.pool.get('product.product').browse(cr, uid, product, context=context)

        if type in ('out_invoice','out_refund'):
            a =  res.product_tmpl_id.property_account_income.id
            ar = part.property_account_payable.id
            if not a:
                a = res.categ_id.property_account_income_categ.id
        else:
            a =  res.product_tmpl_id.property_account_expense.id
            # se agrego para buscar el id de la cuenta de reserva
            ar = part.property_account_reserv.id
            if not a:
                a = res.categ_id.property_account_expense_categ.id

        a = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, a)
        if a:
            result['account_id'] = a

        # se agrego para actualizar la cuenta de reserva
        if bool(ar):
            result['account_res_id'] = ar

        taxep=None
        tax_obj = self.pool.get('account.tax')
        if type in ('out_invoice', 'out_refund'):
            taxes = res.taxes_id and res.taxes_id or (a and self.pool.get('account.account').browse(cr, uid,a).tax_ids or False)
            tax_id = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)
        else:
            taxes = res.supplier_taxes_id and res.supplier_taxes_id or (a and self.pool.get('account.account').browse(cr, uid,a).tax_ids or False)
            tax_id = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)
            # se agrego para buscar los precios de los productos   ------------------------------------------
            pricelist_id = part.property_product_pricelist_purchase.id
            prod_uom_po = res.uom_po_id.id
            if not uom:
                uom = prod_uom_po            
            date_inv = time.strftime('%Y-%m-%d')
            price = self.pool.get('product.pricelist').price_get(cr,uid,[pricelist_id],
                product, qty or 1.0, partner_id, {
                    'uom': uom,
                    'date': date_inv,
                    })[pricelist_id]
            ##------------------------------------------------------------------------------------------------
        if type in ('in_invoice', 'in_refund'):
            to_update = self.product_id_change_unit_price_inv(cr, uid, tax_id, price_unit, qty, address_invoice_id, product, partner_id, context=context)
            # actualizando los precios de los productos   ------------------------------------------
            to_update.update({'price_unit': price, 'price_standard': res.cost_price})
            result.update(to_update)
        else:
            result.update({'price_unit': res.list_price, 'invoice_line_tax_id': tax_id, 'price_standard': res.price_standard})

#        if not name:
        result['name'] = res.name_get()[0][1]

        domain = {}
        result['uos_id'] = uom or res.uom_id.id or False
        if result['uos_id']:
            res2 = res.uom_id.category_id.id
            if res2 :
                domain = {'uos_id':[('category_id','=',res2 )]}
            
        return {'value':result, 'domain':domain}



    ##concept_id_change--------------------------------------------------------------------------------------------
    # Se agrega los conceptos de las notas de credito internas
    # Realizado por: William Suarez
    # Fecha:03-07-09

    def account_id_change(self, cr, uid, ids, idaccount, context=None):
        vals   ={}
        if not idaccount:
            return {'value':vals}
        vals['account_res_id'] = idaccount
        return {'value':vals}


    ##concept_id_change--------------------------------------------------------------------------------------------
    # Se agrega los conceptos de las notas de credito internas
    # Realizado por: William Suarez
    # Fecha:03-07-09

    def concept_id_change(self, cr, uid, ids, idconcept, context=None):
        vals   ={}
        if not idconcept:
            return {'value':vals}
        resp = self.pool.get('concept.invoice.refund').browse(cr, uid, idconcept, context=context)
        vals['quantity'] = 1
        vals['price_unit'] = 0
        vals['name'] = resp.name
        return {'value':vals}


    ##move_line_get_item--------------------------------------------------------------------------------------------
    # Se agrega los campos price_standard, price_comp y account_res_id
    # Realizado por: Javier Duran
    # Fecha:03-07-09
    # Actualizado:William Suarez 
    # Fecha:06-02-2010
    # Se agrega la Cta de reserva de ventas

    def move_line_get_item(self, cr, uid, line, context=None):
        vals = {
            'type':'src',
            'name': line.name[:64],
            'price_unit':line.price_unit,
            'quantity':line.quantity,
            'price':line.price_subtotal,
            'account_id':line.account_id.id,
            'product_id':line.product_id.id,
            'uos_id':line.uos_id.id,
            'account_analytic_id':line.account_analytic_id.id,
            'taxes':line.invoice_line_tax_id,
            'price_standard':line.price_standard,
            'price_fact':line.price_fact,
            'price_comp':line.price_subtotal_comp,
            'account_res_id':line.account_res_id.id,
            'reserva_ventas':False,
            'cta_prod_ventas':False,
        }
        if line.product_id.account_reserv_id:
            vals['reserva_ventas'] = line.product_id.account_reserv_id.id
        if line.product_id.property_account_income:
            vals['cta_prod_ventas'] = line.product_id.property_account_income.id
        return vals

account_invoice_line()


#-------------------------------------------------------------------------------------------------------------------------
#'amount_ret':
#'base_ret':
#
#Se sobreescribe el metodo 'compute', con la finalidad de que el mismo pueda procesar las compras de Gastos Admnistrativos
#ya que el metodo por defecto no contempla el tipo de facturas 'in_invoice_ad'
#-------------------------------------------------------------------------------------------------------------------------
class account_invoice_tax(osv.osv):
    _inherit = "account.invoice.tax"
    _columns = { 
        'amount_ret': fields.float('Amount Ret', digits=(16, int(config['price_accuracy']))),
        'base_ret': fields.float('Amount Ret', digits=(16, int(config['price_accuracy']))),
     }

    def compute(self, cr, uid, invoice_id, context={}):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            for tax in tax_obj.compute(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id, inv.p_ret):
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = tax['price_unit'] * line['quantity']
                val['amount_ret'] = tax['amount_ret']
                val['base_ret'] = 0.0
                if tax['tax_group'] == 'vat':
                    val['base_ret'] = tax['price_unit'] * line['quantity']

                
                #Corvus Latinoamerica
                #Se agrega el tipo 'in_invoice_ad' para que puede ser evaluado
                if inv.type in ('out_invoice','in_invoice','in_invoice_ad'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']
                    tax_grouped[key]['amount_ret'] += val['amount_ret']
                    tax_grouped[key]['base_ret'] += val['base_ret']

        for t in tax_grouped.values():
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['amount_ret'] = cur_obj.round(cr, uid, cur, t['amount_ret'])
        return tax_grouped
account_invoice_tax()

class account_invoice_retencion_client(osv.osv):
    _name = 'account.invoice.retencion.client'
    _columns = {
        'date_retencion':  fields.date('Document Date'),
        'invoice_id': fields.many2one('account.invoice', 'Parent Invoice', select=True),
        'number': fields.char('Document Number', size=20),
        'amount': fields.float('Amount payed'),
        'retencion_id': fields.many2one('account.retention.types','name',select=True),
        'include': fields.boolean('Include'),
    }
    _defaults = {
        'include': lambda *a: False
        }
account_invoice_retencion_client()

#------------------------------------------------------------------------
#Conceptos Notas de Credito: Para las notas de credito internas
#------------------------------------------------------------------------

class concept_invoice_refund(osv.osv): 
	_name = 'concept.invoice.refund'
	_description = 'Concept Invoice Customer Refund'	
	_columns = {
		'name': fields.char('Description', size=200, required=True),
		'code': fields.char('Code', size=8),	
	}
	_defaults = {
			
	}
concept_invoice_refund()

class account_move(osv.osv):
	_inherit = "account.move"
	_columns = {
		'ref': fields.char('Ref', size=200),
		'file_name': fields.char('File Name', size=100),
		'file_import': fields.boolean('File import'),
	}
	_defaults = {
            'file_import': lambda *a: False
	}
account_move()