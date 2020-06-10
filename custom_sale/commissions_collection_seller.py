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

import tools
import pooler
import time
import netsvc
from osv import fields, osv
import ir
from mx import DateTime
from tools import config 

#commissions_collection_seller:---------------------------------------------------------------------------------
#Comisiones Cobranza del Vendedor: 
#
class commissions_collection_seller(osv.osv):
    _name = "commissions.collection.seller"
    _description = 'Comisiones Cobranza Vendedor'	
    _columns = {
        'name': fields.char('Description', size=64),
        'notes': fields.text('Notes Information'),
        'commission_period_id': fields.many2one('sale.commissionsperiod', 'Periodo'),
        'date_start': fields.date('Date Start'),
        'date_stop': fields.date('Date Stop'),
        'zone_id': fields.many2one('res.partner.zone', 'Zone'),
        'salesman_id': fields.many2one('res.partner', 'Salesman'),
        'number_days': fields.integer('Holidays'),
        'amount_adjustment': fields.float('Amount Adjustment'),
        'quota_annual': fields.float('Annual Quota',  digits=(16, int(config['price_accuracy']))),
        'quota_amount': fields.float('Amount Quota',  digits=(16, int(config['price_accuracy']))),
        'daily_salary': fields.float('Daily Salary',  digits=(16, int(config['price_accuracy']))),
        'collection_total': fields.float('Total collection',  digits=(16, int(config['price_accuracy']))),
        'collection_percent': fields.float('Porcentage Cash', digits=(16, int(config['price_accuracy']))),
        'collection_pay': fields.float('Total Pay',  digits=(16, int(config['price_accuracy']))),
        'amount_holiday': fields.float('Amount Holiday',  digits=(16, int(config['price_accuracy']))),
        'commission_pay': fields.float('Commission Pay', digits=(16, int(config['price_accuracy']))),
        'collection_line': fields.one2many('commissions.collection.line', 'collection_id', 'Collection Lines'), 
        'state': fields.selection([
            ('draft','Draft'),
            ('paid','Paid'),
            ('cancel','Cancelled')
        ],'State', readonly=True),        
        'type': fields.selection([
            ('junior','Junior'),
            ('senior','Senior')
        ],'Tipo'),
        'commissions_type': fields.selection([
            ('zone','Vendedor'),
            ('territory','Territorio'),
            ('division','Division')
        ],'Commissions Type'),
    }	
    _defaults = {
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
        dias     = 0
        percent	 = 0	
        quota_amount  = 0
        collection_total    = 0
        collection_pay      = 0
        daily_salary        = 0
        total = 0
        if not  ids:
            return {}

        #Datos Requiridos: se obtienen los datos necesario para realizar el calculo 
        datoscomis = self.pool.get('commissions.collection.seller').read(cr, uid, ids, ['number_days','quota_amount','collection_total','amount_adjustment','type','salesman_id'])
        if datoscomis and datoscomis[0]:
            dias = datoscomis[0]['number_days']
            quota_amount = datoscomis[0]['quota_amount']
            collection_total = datoscomis[0]['collection_total']
            amount_adjustment = datoscomis[0]['amount_adjustment']
            tipo =  datoscomis[0]['type']
            percent = collection_total / quota_amount * 100
            sqlp  = "SELECT percent_min,percent_max,quota_amount FROM commissions_collection_parameters WHERE type='%s' ORDER BY percent_min"%tipo
            cr.execute (sqlp)
            parameter_dat = cr.fetchall()
            if parameter_dat:
                for d in parameter_dat:
                    if percent >= d[0] and percent <= d[1]:
                        collection_pay = d[2]
                        break
                    elif percent >= d[1]:
                        collection_pay = d[2]
                if collection_pay:
                    daily_salary  = collection_pay / 30
                amount_holiday = daily_salary * dias
                commission_pay = amount_holiday + collection_pay + amount_adjustment
                vals = {
                        'collection_percent': percent,
                        'collection_pay': collection_pay,
                        'daily_salary': daily_salary,
                        'amount_holiday': amount_holiday,
                        'commission_pay': commission_pay
                        } 
            self.pool.get('commissions.collection.seller').write(cr, uid, ids, vals)		
        return True

    ##compute_commission_v2---------------------------------------------------------------------------------
    #Se Calcula los montos 
    def compute_commission_v2(self, cr, uid, ids, context={}):
        dias     = 0
        percent	 = 0	
        quota_amount  = 0
        collection_total    = 0
        collection_pay      = 0
        daily_salary  = 0
        total = 0
        if not  ids:
            return {}
        #Datos Requiridos: se obtienen los datos necesario para realizar el calculo 
        datoscomis = self.pool.get('commissions.collection.seller').read(cr, uid, ids, ['number_days','commissions_type','quota_annual','quota_amount','collection_total','collection_pay','amount_holiday','amount_adjustment'])
        if datoscomis and datoscomis[0]:
            #Parametros
            dias = datoscomis[0]['number_days']
            quota_annual = datoscomis[0]['quota_annual']
            quota_amount = datoscomis[0]['quota_amount']
            collection_total = datoscomis[0]['collection_total']
            amount_adjustment = datoscomis[0]['amount_adjustment']
            percent = collection_total / quota_amount * 100
            tipo = datoscomis[0]['commissions_type']
            sqlp  = "SELECT percent_min,percent_max FROM commissions_collection_parameters WHERE active=True AND commissions_type='%s' ORDER BY percent_min"%tipo
            cr.execute (sqlp)
            parameter_dat = cr.fetchall()
            total = 0
            if parameter_dat:
                for d in parameter_dat:
                    if percent >= d[0] and percent <= d[1]:
                        total = quota_annual * percent / 100 
                        break
                    elif percent >= d[1]:
                        total = quota_annual * d[1] / 100
            collection_pay = total
            daily_salary = total / 30
            amount_holiday = daily_salary * dias
            amount_adjustment = datoscomis[0]['amount_adjustment']
            commission_pay = amount_holiday + collection_pay + amount_adjustment
            vals = {
                    'collection_percent': percent,
                    'collection_pay': collection_pay,
                    'daily_salary': daily_salary,
                    'amount_holiday': amount_holiday,
                    'commission_pay': commission_pay
                    }
            self.pool.get('commissions.collection.seller').write(cr, uid, ids, vals)		
        return True
commissions_collection_seller()

#deductions_seller_line:---------------------------------------------------------------------------------
#: 
#
class commissions_collection_line(osv.osv):
    _name = "commissions.collection.line"
    _description = 'Commissions Collection Line'	
    _columns = {
        'name': fields.char('Recibo Oficial', size=64),
        'amount_ro': fields.float('Amount RO', digits=(16, int(config['price_accuracy']))),
        'date_ro': fields.date('Date RO'),
        'collection_id': fields.many2one('commissions.collection.seller', 'Commissions Ref', ondelete='cascade'),
    }	
    _defaults = {}
commissions_collection_line()

commissions_collection_seller()

#deductions_seller_line:---------------------------------------------------------------------------------
#: 
#
class commissions_collection_parameters(osv.osv):
    _name = "commissions.collection.parameters"
    _description = 'Commissions Collection parameters'	
    _columns = {
        'name': fields.char('Description', size=64),
        'quota_amount': fields.float('Quota Amount', digits=(16, int(config['price_accuracy']))),
        'percent_min': fields.float('Percent Min', digits=(16, int(config['price_accuracy']))),
        'percent_max': fields.float('Percent Max', digits=(16, int(config['price_accuracy']))),
        'active' : fields.boolean('Active'),
        'type': fields.selection([
            ('junior','Junior'),
            ('senior','Senior')
        ],'Tipo'),
        'commissions_type': fields.selection([
            ('zone','Vendedor'),
            ('territory','Territorio'),
            ('division','Division')
        ],'Commissions Type'),
    }	
    _defaults = {
        'active' : lambda *a: 1,
    }
commissions_collection_parameters()
