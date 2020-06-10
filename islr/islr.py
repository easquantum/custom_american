##############################################################################
#
# Copyright (c) 2007 - 2010 Corvus Latinoamerica, C.A. (http://corvus.com.ve) All Rights Reserved
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
import netsvc
from osv import fields,osv,orm
from tools import config
import mx.DateTime
import pooler
from osv.orm import browse_record

class account_islr_tax(osv.osv):
	##amount_ret_all-----------------------------------------------------------------------------------------------
	#Se obtiene los totales de documento
	# 
    def _amount_ret_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for retention in self.browse(cr, uid, ids, context):
            res[retention.id] = { 'total_tax_ret': 0.0,'total_base_ret': 0.0}
            for line in retention.islr_line:
                res[retention.id]['total_base_ret'] += line.base_amount
                res[retention.id]['total_tax_ret'] += line.retention_amount
        return res

    _name = "account.islr.tax"
    _description ="Islr Taxing"
    _columns = { 
        'name': fields.char('Description', size=64, readonly=True),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type Document', readonly=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('done','Done'),
            ('cancel','Cancelled')
            ],'State', readonly=True),
        'document_date': fields.date('Document Date'),
        'account_id': fields.many2one('account.account', 'Account'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'base': fields.float('Base'),
        'porcentaje': fields.float('Porcentaje'),
        'amount_islr': fields.float('Islr Amount'),
        'islr_type_id': fields.many2one('account.islr.tax.type','Type ISLR'),
        'move_id': fields.many2one('account.move', 'ISLR Movement', readonly=True),
        'notes': fields.text('Description'),
        'manual': fields.boolean('Manual'),
        'islr_line': fields.one2many('account.islr.tax.line', 'islr_id', 'ISLR Lines'),
        'total_base_ret': fields.function(_amount_ret_all, method=True,  digits=(16, int(config['price_accuracy'])), string='Total Base Ret', multi='all'),
        'total_tax_ret': fields.function(_amount_ret_all, method=True,  digits=(16, int(config['price_accuracy'])), string='Total Tax Ret', multi='all'),
        #Campos Estructura Vieja
        'inicial_date': fields.date('Inicial Date', readonly=True),
        'descuento': fields.float('Descuento', readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
        'type_islr': fields.selection([
            ('legal','Legal'),
            ('natural','Natural'),
            ],'Type Islr', readonly=True),
    }

    ##get_type-----------------------------------------------------------------------------------------------
    #Se obtiene el tipo de documento
    #
    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        type = context.get('type', 'in_invoice')
        return type

    ##get_journal--------------------------------------------------------------------------------------------
    #Se obtiene el Diario
    #
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

    ##get_currency-------------------------------------------------------------------------------------------
    #Se obtiene el tipo de  moneda
    #
    def _get_currency(self, cr, uid, context):
        user = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        if user.company_id:
            return user.company_id.currency_id.id
        else:
            return self.pool.get('res.currency').search(cr, uid, [('rate','=',1.0)])[0]

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('account.islr.tax').islr_seq_get(cr, uid),
        'type': _get_type,
        'document_date': lambda *a: time.strftime('%Y-%m-01'),
        'state': lambda *a: 'draft',
        'manual': lambda *a: False,
        'journal_id': _get_journal,
        'currency_id': _get_currency,
        'company_id': lambda self,cr,uid,context: self.pool.get('res.users').browse(cr,uid,uid,context=context).company_id.id,
        }

    ##islr_seq_get-------------------------------------------------------------------------------------------
    #Asigna el numero comprobante temporal de retencion ISLR
    #
    def islr_seq_get(self, cr, uid):
        pool_seq=self.pool.get('ir.sequence')
        cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='account.islr.tax' and active=True")
        res = cr.dictfetchone()
        if res:
            if res['number_next']:
                return pool_seq._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + pool_seq._process(res['suffix'])
            else:
                return pool_seq._process(res['prefix']) + pool_seq._process(res['suffix'])
        return True

    ##create-------------------------------------------------------------------------------------------------
    #Asigna el numero comprobante de retencion ISLR
    #
    def create(self, cursor, user, vals, context=None):
        vals['name']=self.pool.get('ir.sequence').get(cursor, user, 'account.islr.tax')
        ret_id=super(account_islr_tax, self).create(cursor, user, vals,context=context)		
        return ret_id

    ##action_done_cancel-------------------------------------------------------------------------------------
    #Anula el comprobante de retencion ISLR y reversa los asientos contables 
    #
    def action_done_cancel(self, cr, uid, ids, *args):
        if ids:
            islr_id     = ids[0]            
            invoice_id  = 0
            move_id     = 0
            pendiente   = 0
            islr_obj    = self.pool.get('account.islr.tax')
            invoice_obj = self.pool.get('account.invoice')
            islr = islr_obj.browse(cr, uid, islr_id)
            #Si existen Facturas se valida el estatus actual de da cada una, solo si todas ellas estan en status=open,
            #se puede cancelar el comprobante
            if islr.islr_line:
                status = 'open'
                for l in  islr.islr_line:
                    if l.invoice_id.state == 'paid':
                        status='paid'
                        break
                if status == 'paid':
                    raise osv.except_osv('ERROR	', 'Todas las facturas debe estar en estatu Abierto, para poder cancelar el comprobante!!!')
            if islr.move_id.id:
                move_id = islr.move_id.id
                account_move_obj = self.pool.get('account.move')
                account_move_obj.button_cancel(cr, uid, [move_id])
                account_move_obj.unlink(cr, uid, [move_id])
            for ln in  islr.islr_line:
                invoice_id  = ln.invoice_id.id
                pendiente   = ln.invoice_id.residual
                pendiente  += ln.retention_amount
                invoice_obj.write(cr, uid,[invoice_id],{'residual':pendiente,'islr':False},context=None)
                cr.execute('DELETE FROM account_islr_tax_line WHERE id = %d;'%ln.id)            
            self.write(cr, uid, ids, {'state':'cancel','move_id':False})
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_create(uid, 'account.islr.tax', islr_id, cr)
        return True

    ##compute_islr-------------------------------------------------------------------------------------------
    #
    #
    def compute_islr(self, cr, uid, ids, context={}):
        if not ids:
            return True
        total = 0
        datos = self.pool.get('account.islr.tax').read(cr, uid, ids, ['base','porcentaje'])
        if datos[0]['base'] and  datos[0]['porcentaje']:
            total = datos[0]['base'] * datos[0]['porcentaje'] / 100
            self.pool.get('account.islr.tax').write(cr, uid, ids, {'amount_islr':total  })
        return True

account_islr_tax()

class account_islr_tax_line(osv.osv):
    _name = "account.islr.tax.line"
    _description = "ISLR tax line"
    _columns = {
        'name': fields.char('Description', size=64),
        'islr_id': fields.many2one('account.islr.tax', 'islr Ref', ondelete='cascade'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice Ref', required=True, select=True),
        'date_invoice': fields.date('Document Date'),
        'base_amount': fields.float('Base Amount',    digits=(16, int(config['price_accuracy']))),
        'retention_amount': fields.float('Retention Amount',    digits=(16, int(config['price_accuracy']))),
    }

    def change_invoice_id_islr(self, cr, uid, ids, invoice_id, type,porcentaje=0, context=None):
        if not invoice_id:
            return {}
        vals = {}
        base = 0
        if type =='in_invoice':
            invoice = self.pool.get('account.invoice').browse(cr,uid,invoice_id)
            if invoice:
                vals['name'] = invoice.number_document
                if porcentaje:
                    if not invoice.amount_tax:
                        vals['base_amount'] = invoice.amount_untaxed
                        vals['retention_amount'] = invoice.amount_untaxed * porcentaje / 100
                    else:
                        for t in invoice.tax_line:
                            base = t.base
                        vals['base_amount'] = base
                        vals['retention_amount'] = base * porcentaje / 100
        return {'value':vals}

account_islr_tax_line()