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

import sys
import time
import locale
import commands
import wizard
import netsvc
import pooler
import tools
from osv import fields,osv,orm
from osv.orm import browse_record
import mx.DateTime

commissions_div_form = '''<?xml version="1.0"?>
	<form string="Calculo de Comisiones - Divisiones">
		<field name="zone_id"/>
		<field name="number_day"/>	
		<separator colspan="4" string="Periodo "/>
	    <newline/>
	    <field name="period_id"/>
	</form> 
'''

commissions_div_fields = {
	'zone_id':   {'string':'Division', 'type':'many2one', 'relation':'res.partner.zone', 'domain':[('type','=','division')]},
	'number_day': {'string':'Nro. Domingos', 'type':'integer', 'required':True},
	#'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'period.generalperiod','required':True},
	'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'sale.commissionsperiod','required':True, 'domain':[('state','=','draft')]},
}

_message_div_form1 = '''<?xml version="1.0"?>
						<form string="Informacion">
							 <label string=" OK: Comisiones Procesadas   !!!" colspan="2"/>
							<newline/>
						</form>''' 

#commissions_calculated_seller------------------------------------------------------------------------------
#
#
def _commissions_calculated(cr, uid, div_id, zone_ids, period_id, nomb, dias):
    #Inicializacion de variables
    totalcred = 0
    totalcont = 0
    totaldesp = 0
    sale_percent = 0
    pay_total = 0
    group_total = 0
    #Territorios - para la zona
    ids_str = ','.join(map(str,zone_ids))
    obj_partner = pooler.get_pool(cr.dbname).get('res.partner')
    partner_id = pooler.get_pool(cr.dbname).get('res.partner').search(cr, uid, [('code_zone_id','=',div_id),('salesman','=',1) ])
    if partner_id: 
        datospartner = obj_partner.browse(cr, uid, partner_id[0])
    else:
        return False
    #Obtener 
    sql = """
    SELECT SUM(credit_total) as total_cred, SUM(cash_total) as total_cont, SUM(sale_total) as total_desp   
    FROM commissions_seller  
    WHERE  commission_period_id=%d AND zone_id in (%s)"""%(period_id,ids_str)
    #print sql 
    cr.execute (sql)
    datosped = cr.fetchall()
    if datosped:
        totalcred = datosped[0][0]
        totalcont = datosped[0][1]
        totaldesp = datosped[0][2]
        if datospartner.amount_total > 0:
            sale_percent = totaldesp / datospartner.amount_total * 100
            if sale_percent > datospartner.percent_max:
                sale_percent = datospartner.percent_max
            pay_total = sale_percent * datospartner.value_total / 100
    groups = []
    tcajas = 0
    tbscajas = 0
    subtotal = pay_total + tbscajas
    sueldo = subtotal / 30 
    totalferiado = sueldo * dias
    total_asig = subtotal + totalferiado
    total_deduc = 0
    deductions = []
    for d in datospartner.deductions_line:
        monto_deduc = 0
        if d.amount_total > 0:
            monto_deduc = d.amount_total
        if d.percent > 0 and total_asig > 0:
            monto_deduc = total_asig * d.percent / 100
        total_deduc  += monto_deduc
        deductions.append((0,0,{'name':d.name ,'amount':monto_deduc ,'deductions_id':d.deduction_id.id }))
    pagar = total_asig - total_deduc 
    vals = {
            'name':nomb,
            'zone_id':div_id,
            'salesman_id':datospartner.id, 
            'commission_period_id':period_id,
            'date_period': time.strftime('%Y-%m-%d'),
            'number_days':dias, 
            'deductions_line': deductions,
            'group_line': groups,
            'amount_group': tbscajas, 
            'amount_total_deduct': 0,
            'amount_cash_order': 0,
            'amount_cred_order': 0,
            'amount_cash_cancel': 0,
            'amount_cred_cancel': 0,                    
            'amount_cash_refund': 0,
            'amount_cred_refund': 0, 
            'credit_total': totalcred,
            'cash_total': totalcont,
            'sale_total': totaldesp,
            'cash_percent': 0,
            'sale_percent': sale_percent,
            'cash_pay': 0,
            'pay_total': pay_total,
            'amount_base': pay_total,
            'commission_base': subtotal,
            'daily_salary': sueldo,
            'amount_holiday':totalferiado,
            'amount_total_asig':total_asig,
            'amount_total_deduct':total_deduc,
            'commission_pay': pagar

          }
    #Registrando la comision 
    pooler.get_pool(cr.dbname).get('commissions.seller').create(cr, uid, vals, context={})
    return vals

#commissions_calculated_seller_ter------------------------------------------------------------------------------
#
#
def _commissions_calculated_seller_div(self, cr, uid, data, context={}):
    form = data['form']
    period_id = form['period_id']
    div_id = form['zone_id']
    dias = form['number_day']
    #periodo = pooler.get_pool(cr.dbname).get('period.generalperiod').browse(cr, uid, period_id, context)
    periodo = pooler.get_pool(cr.dbname).get('sale.commissionsperiod').browse(cr, uid, period_id, context)
    desde = periodo.date_start
    hasta = periodo.date_stop
    nomb = periodo.name
    zone_ids = []
    division_ids = []
    if not div_id:
        division_ids = pooler.get_pool(cr.dbname).get('res.partner.zone').search(cr, uid, [('type','=','division')])
    else:
        division_ids.append(div_id)
    for d in division_ids:
        zone_ids = pooler.get_pool(cr.dbname).get('res.partner.zone').search(cr, uid, [('parent_id','=',d)])
        datos  = _commissions_calculated(cr, uid, d, zone_ids, period_id, nomb, dias)

    resp ='message'
    return resp

class commissions_calculated_div(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':commissions_div_form, 'fields':commissions_div_fields, 'state': [('end', 'Cancelar'),('calculated', 'Aceptar')]}
		},

		'calculated': {
			'actions': [],
			'result' : {'type' : 'choice', 'next_state': _commissions_calculated_seller_div }
		},
		'message' : {
			'actions' : [],
			'result': {'type':'form', 'arch':_message_div_form1, 'fields':commissions_div_fields, 'state':[('end','OK')]}
		},
	}
commissions_calculated_div("commissions_seller_div")
