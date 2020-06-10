# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007-2015 Corvus Latinoamerica, C.A. 
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


commissions_collection_zone_form = '''<?xml version="1.0"?>
	<form string="Calculo de Comisiones Vendedores">
		<field name="zone_id"/>
		<field name="number_day"/>
		<field name="amount"/>
		<field name="commissions_type"/>	
		<separator colspan="4" string=" "/>
	    <newline/>
	    <field name="period_id" string="Perido"/>
	</form> 
'''

commissions_collection_zone_fields = {
	'zone_id':   {'string':'Zona', 'type':'many2one', 'relation':'res.partner.zone','required':True,'domain':[('type','=','zone')]},
	'number_day': {'string':'Nro. Domingos', 'type':'integer', 'required':True},
	'amount': {'string':'cuota', 'type':'float', 'required':True},
	'commissions_type': {'string':'Comision Tipo:', 'type':'selection', 'readonly':1, 'default': lambda *a: 'zone','selection':[('zone','Vendedor')]},
	'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'sale.commissionsperiod','required':True,'domain':[('state','=','draft')]},
}

_message_collection_form1 = '''<?xml version="1.0"?>
	<form string="Informacion">
		 <label string=" Comision Procesada" colspan="2"/>
		<newline/>
	</form>
''' 


#commissions_calculated_seller------------------------------------------------------------------------------
#
#
def _collection_calculated_zone(cr, uid,  zona, desde,hasta, dias,cuota,tipo,period_id,context={}):
    #Vendedor - para la zona
    obj_partner = pooler.get_pool(cr.dbname).get('res.partner')
    partner_id = pooler.get_pool(cr.dbname).get('res.partner').search(cr, uid, [('code_zone_id','=',zona),('salesman','=',1) ])
    if partner_id: 
        datospartner = obj_partner.browse(cr, uid, partner_id[0])
    else:
        return {'resultado':"No hay Vendedor Asignado a la zona...!"}
    ro = []
    nomb = ''
    collection_total = 0
    period	= pooler.get_pool(cr.dbname).get('account.period').read(cr, uid, [period_id],['code'])
    if period and period[0]:
        nomb = period[0]['code'] 
    vals = {
            'name': nomb,
            'zone_id': zona,
            'salesman_id': partner_id[0],
            'commissions_type': tipo,
            'commission_period_id':period_id,
            'date_start': desde,
            'date_stop': hasta,
            'number_days':dias,
            'collection_line': ro,
            'quota_annual': 0,
            'quota_amount': cuota,
            'collection_total': 0,
            'daily_salary': 0,
          }
    #Obtener datos de la cobranza 
    sql = """
    SELECT  p.control_number,p.date_payment, SUM(p.amount) as total  
    FROM account_payment_method     AS p  
    INNER JOIN account_invoice      AS a ON p.invoice_id=a.id 
    WHERE p.ro=True AND a.state!='cancel' AND a.code_zone_id=%d AND p.date_payment BETWEEN '%s' AND '%s'
    GROUP BY p.control_number,p.date_payment;"""%(zona,desde,hasta)
    #print sql 
    cr.execute (sql)
    datosro = cr.fetchall()
    if datosro:
        #Totales RO.---------------------------------------------------------------------------------------
        for d in datosro:
            number_ro = d[0]
            fecha = d[1]
            monto = d[2]
            collection_total  += monto
            ro.append((0,0,{'name':number_ro, 'amount_ro':monto, 'date_ro':fecha }))
    vals['collection_line'] = ro
    vals['collection_total'] = collection_total
    #Totales Ventas Bs.---------------------------------------------------------------------------------------
    if cuota > 0 and collection_total > 0:
        percent = collection_total / cuota * 100
        vals['collection_percent'] = percent
        sqlp  = "SELECT percent_min,percent_max,quota_amount FROM commissions_collection_parameters WHERE active=True AND commissions_type='%s' ORDER BY percent_min"%tipo
        cr.execute (sqlp)
        parameter_dat = cr.fetchall()
        total = 0
        if parameter_dat:
            for d in parameter_dat:
                vals['quota_annual'] = d[2]
                if percent >= d[0] and percent <= d[1]:
                    total = d[2] * percent / 100 
                    break
                elif percent >= d[1]:
                    total = d[2] * d[1] / 100
            vals['collection_pay'] = total
            if total:
                vals['daily_salary'] = total / 30
            vals['amount_holiday'] = vals['daily_salary'] * dias
            vals['commission_pay'] = vals['amount_holiday'] + vals['collection_pay']
    pooler.get_pool(cr.dbname).get('commissions.collection.seller').create(cr, uid, vals, context)
    return True


#commissions_calculated_seller_zone------------------------------------------------------------------------------
#
#
def _commissions_collection_calc_zone(self, cr, uid, data, context={}):
    resp ='message'
    if not data:
        return {'resultado':"No hay datos...!"}
    form = data['form']
    tipo = form['commissions_type']
    zone_id = form['zone_id']
    dias = form['number_day']
    period_id = form['period_id']
    cuota = form['amount']
    periodo = pooler.get_pool(cr.dbname).get('sale.commissionsperiod').browse(cr, uid, period_id, context)
    desde = periodo.date_start
    hasta = periodo.date_stop
    zone_ids = []
    if not zone_id:
        zone_ids = pooler.get_pool(cr.dbname).get('res.partner.zone').search(cr, uid, [('type','=','zone')])
    else:
        zone_ids.append(zone_id)
    for zone in zone_ids:
        datos  = _collection_calculated_zone(cr, uid, zone, desde,hasta, dias,cuota,tipo,period_id)
    return resp

class commiss_collection_calc_zone(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':commissions_collection_zone_form, 'fields':commissions_collection_zone_fields, 'state': [('end', 'Cancelar'),('calculated', 'Aceptar')]}
		},

		'calculated': {
			'actions': [],
			'result' : {'type' : 'choice', 'next_state': _commissions_collection_calc_zone }
		},
		'message' : {
			'actions' : [],
			'result': {'type':'form', 'arch':_message_collection_form1, 'fields':commissions_collection_zone_fields, 'state':[('end','Ok')]}
		},
	}
commiss_collection_calc_zone("commissions_collection_calc_zone")
