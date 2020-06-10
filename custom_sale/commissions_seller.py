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

import tools
import pooler
import time
import netsvc
from osv import fields, osv
import ir
from mx import DateTime
from tools import config 

#commissions_seller:---------------------------------------------------------------------------------
#Comisiones del Vendedor: 
#
class commissions_seller(osv.osv):
    _name = "commissions.seller"
    _description = 'Comisiones Vendedor'	
    _columns = {
        'name': fields.char('Description', size=64),
        'notes': fields.text('Notes Information'),
        'date_period': fields.date('Date', required=True),
        'period_id': fields.many2one('period.generalperiod', 'Periodo'),
        'commission_period_id': fields.many2one('sale.commissionsperiod', 'Periodo', readonly=True),
        'zone_id': fields.many2one('res.partner.zone', 'Zone', required=True),
        'salesman_id': fields.many2one('res.partner', 'Salesman'),
        'number_days': fields.integer('Holidays'),
        'cuota_percent': fields.float('Porcentage Cuota', digits=(16, int(config['price_accuracy']))),
        'cuota_year': fields.float('Amount Cuota Year',  digits=(16, int(config['price_accuracy']))),
        'cuota_month': fields.float('Amount Cuota Month',  digits=(16, int(config['price_accuracy']))),
        'daily_salary': fields.float('Daily Salary',  digits=(16, int(config['price_accuracy']))),
        'amount_cred_order': fields.float('Amount Cred Order',  digits=(16, int(config['price_accuracy']))),
        'amount_cash_order': fields.float('Amount Cash Order', digits=(16, int(config['price_accuracy']))),
        'amount_cash_invoice': fields.float('Amount Cash Invoice', digits=(16, int(config['price_accuracy']))),
        'amount_cred_invoice': fields.float('Amount Credit Invoice',  digits=(16, int(config['price_accuracy']))),
        'amount_cash_refund': fields.float('Amount Cash Refund',  digits=(16, int(config['price_accuracy']))),
        'amount_cred_refund': fields.float('Amount Credit Refund',  digits=(16, int(config['price_accuracy']))),
        'amount_cred_cancel': fields.float('Amount Credit Refund',  digits=(16, int(config['price_accuracy']))),
        'amount_cash_cancel': fields.float('Amount Cash Refund', digits=(16, int(config['price_accuracy']))),
        'credit_total': fields.float('Total Credit',  digits=(16, int(config['price_accuracy']))),
        'cash_total': fields.float('Total Cash',  digits=(16, int(config['price_accuracy']))),
        'sale_total': fields.float('Total Sale',  digits=(16, int(config['price_accuracy']))),
        'cash_percent': fields.float('Porcentage Cash', digits=(16, int(config['price_accuracy']))),
        'sale_percent': fields.float('Porcentage Sale', digits=(16, int(config['price_accuracy']))),
        'cash_pay': fields.float('Total Cash',  digits=(16, int(config['price_accuracy']))),
        'pay_total': fields.float('Total Pay',  digits=(16, int(config['price_accuracy']))),
        'amount_base': fields.float('Amount Sale Base',  digits=(16, int(config['price_accuracy']))),
        'amount_group': fields.float('Amount Sale Base Group',  digits=(16, int(config['price_accuracy']))),
        'commission_base': fields.float('Amount SubTotal', digits=(16, int(config['price_accuracy']))),
        'amount_holiday': fields.float('Amount Holiday',  digits=(16, int(config['price_accuracy']))),
        'amount_adjustment': fields.float('Amount Adjustment', digits=(16, int(config['price_accuracy']))),
        'amount_total_deduct': fields.float('Amount Adjustment', digits=(16, int(config['price_accuracy']))),
        'amount_total_asig': fields.float('Amount Total Deductions', digits=(16, int(config['price_accuracy']))),
        'commission_pay': fields.float('Commission Pay', digits=(16, int(config['price_accuracy']))),
        'commission_invoice': fields.boolean('Commissions Invoice'),
        'group_line': fields.one2many('commissions.group.line', 'commissions_id', 'Group Lines'),
        'deductions_line': fields.one2many('deductions.seller.line', 'commissions_id', 'Deductions Lines'),
        'state': fields.selection([
            ('draft','Draft'),
            ('paid','Paid'),
            ('cancel','Cancelled')
        ],'State', readonly=True),
    }	
    _defaults = {
        'date_period': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
    }

    
    ##button_change_state----------------------------------------------------------------------------------------------------
    #Cambia el estatus del pago:
    # 
    def button_change_state(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state': 'paid'})
        return True


    ##button compute_commission_pay----------------------------------------------------------------------------------------------------
    #Se Calcula los montos de:
    # Total Dominogs y Feriado
    # Total Asignaciones
    # Total Deducciones
    # Total comisione a Pagar
    def compute_commission_pay(self, cr, uid, ids, context={}):
        total_deduct   = 0
        total_asig	   = 0	
        total_holiday  = 0
        total_com      = 0
        if not  ids:
            return {}

        #Datos Requiridos: se obtienen los datos necesario para realizar el calculo 
        datoscomis = self.pool.get('commissions.seller').read(cr, uid, ids, ['number_days','daily_salary','amount_adjustment','deductions_line','commission_base','salesman_id'])
        if datoscomis and datoscomis[0]:
            deductions = []
            dias	= datoscomis[0]['number_days']
            total_asig = datoscomis[0]['commission_base']
            salesman_id = datoscomis[0]['salesman_id'][0]
            if datoscomis[0]['amount_adjustment']:
                total_asig	   += datoscomis[0]['amount_adjustment']
            salario = total_asig / 30
            if dias and salario > 0:
                total_holiday = dias * salario
                total_asig	   += total_holiday 
            #print "TOTAL_ASG",total_asig
            for d in  datoscomis[0]['deductions_line']:
                datosde = self.pool.get('deductions.seller.line').read(cr, uid, [d], ['amount','deductions_id'])
                mnt_deduc = datosde[0]['amount']
                if datoscomis[0]['amount_adjustment']:
                    deduc_line_id  = datosde[0]['deductions_id'][0]
                    assig_dec_id = self.pool.get('deductions.assigned.seller').search(cr,uid, [('seller_id','=',salesman_id),('deduction_id','=',deduc_line_id)])
                    dpartner = self.pool.get('deductions.assigned.seller').read(cr, uid, assig_dec_id, ['percent'])
                    if dpartner and dpartner[0]['percent']:
                        mnt_deduc = total_asig * dpartner[0]['percent'] / 100
                        deductions.append((1,d,{'amount':mnt_deduc }))
                total_deduct += mnt_deduc
            total_com  = total_asig - total_deduct
            self.pool.get('commissions.seller').write(cr, uid, ids, {'amount_holiday': total_holiday,'amount_total_asig':total_asig, 'amount_total_deduct':total_deduct, 'commission_pay':total_com,'deductions_line':deductions,'daily_salary':salario })		
        return True
	

    ##unlink----------------------------------------------------------------------------------------------------
    #No se puede borrar una comision ya pagada
    # 
    def unlink(self, cr, uid, ids, context=None):      
        if ids:
            status = self.read(cr, uid, ids, ['state'])
            if status and status[0] and status[0]['state'] == 'paid':
                raise osv.except_osv(_('Error !'), _('No puede borrar una comision pagada...!'))
        return super(commissions_seller, self).unlink(cr, uid, ids, context)

commissions_seller()


#commissions_group_line:---------------------------------------------------------------------------------
#: 
#
class commissions_group_line(osv.osv):
    _name = "commissions.group.line"
    _description = 'Commissions Group Line'	
    _columns = {
        'name': fields.char('Description', size=64),
        'category_id': fields.many2one('product.category.salesman', 'Category', required=True),
        'cuota_year': fields.float('Amount Cuota Year',  digits=(16, int(config['price_accuracy']))),
        'quota_qty': fields.float('Quota Value', digits=(16, int(config['price_accuracy']))),
        'quota_amount': fields.float('Quota Amount', digits=(16, int(config['price_accuracy']))),
        'quantity': fields.float('Quantity', digits=(16, int(config['price_accuracy']))),
        'percent_quota': fields.float('Percentage Quantity', digits=(16, int(config['price_accuracy']))),
        'amount': fields.float('Amount', digits=(16, int(config['price_accuracy']))),
        'commissions_id': fields.many2one('commissions.seller', 'Commissions Ref', ondelete='cascade'),
    }	
    _defaults = {}
commissions_group_line()


#deductions_seller_line:---------------------------------------------------------------------------------
#: 
#
class deductions_seller_line(osv.osv):
    _name = "deductions.seller.line"
    _description = 'Deductions Seller Line'	
    _columns = {
        'name': fields.char('Description', size=64),
        'deductions_id': fields.many2one('deductions.seller', 'Deductions Seller', required=True),
        'amount': fields.float('Deductions Amount', digits=(16, int(config['price_accuracy']))),
        'commissions_id': fields.many2one('commissions.seller', 'Commissions Ref', ondelete='cascade'),
    }	
    _defaults = {}
deductions_seller_line()
