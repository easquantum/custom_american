# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007-2010 Corvus Latinoamerica, C.A. 
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


commissions_collection_form = '''<?xml version="1.0"?>
	<form string="Calculo de Comisiones Cobranza">
		<field name="zone_id"/>
		<field name="number_day"/>
		<field name="amount"/>
		<field name="type"/>	
		<separator colspan="4" string="Rango de Fecha"/>
	    <newline/>
	    <field name="date1"/>
	    <field name="date2"/>
	</form> 
'''

commissions_collection_fields = {
	'zone_id':   {'string':'Zona', 'type':'many2one', 'relation':'res.partner.zone','required':True},
	'number_day': {'string':'Nro. Domingos', 'type':'integer', 'required':True},
	'amount': {'string':'cuota', 'type':'float', 'required':True},
	'type': {'string':'Tipo:', 'type':'selection', 'required':True, 'selection':[('junior','Junior'),('senior','Senior')]},
	'date1': {'string':'Desde', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-01')},
	'date2': {'string':'Hasta', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
}

_message_collection_form1 = '''<?xml version="1.0"?>
						<form string="Informacion">
							 <label string=" OK: Comisiones Procesadas   !!!" colspan="2"/>
							<newline/>
						</form>''' 


#commissions_calculated_seller------------------------------------------------------------------------------
#
#
def _commissions_calculated_seller(cr, uid,  zona, desde,hasta, dias,cuota,tipo,context={}):
    #Vendedor - para la zona
    obj_partner = pooler.get_pool(cr.dbname).get('res.partner')
    partner_id = pooler.get_pool(cr.dbname).get('res.partner').search(cr, uid, [('code_zone_id','=',zona),('salesman','=',1) ])
    if partner_id: 
        datospartner = obj_partner.browse(cr, uid, partner_id[0])
    else:
        return {'resultado':"No hay Vendedor Asignado a la zona...!"}
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
    ro = []
    nomb = ''
    period_ids= pooler.get_pool(cr.dbname).get('account.period').search(cr,uid,[('date_start','<=',desde),('date_stop','>=',desde)])
    period	= pooler.get_pool(cr.dbname).get('account.period').read(cr, uid, period_ids,['code'])
    if period and period[0]:
        nomb = period[0]['code'] 
    vals = {
            'name': nomb,
            'zone_id': zona,
            'salesman_id': partner_id[0],
            'type': tipo,
            'date_start': desde,
            'date_stop': hasta,
            'number_days':dias,
            'collection_line': ro,
            'quota_amount': cuota,
            'collection_total': 0,
            'daily_salary': 0,
          }
    if datosro:
        #Totales RO.---------------------------------------------------------------------------------------
        collection_total = 0
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
            sqlp  = "SELECT percent_min,percent_max,quota_amount FROM commissions_collection_parameters WHERE type='%s' ORDER BY percent_min"%tipo
            cr.execute (sqlp)
            parameter_dat = cr.fetchall()
            total = 0
            if parameter_dat:
                for d in parameter_dat:
                    if percent >= d[0] and percent <= d[1]:
                        total = d[2]
                        break
                    elif percent >= d[1]:
                        total = d[2]
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
def _commissions_calculated_collection(self, cr, uid, data, context={}):
    resp ='message'
    if not data:
        return {'resultado':"No hay datos...!"}
    form = data['form']
    tipo = form['type']
    zone_id = form['zone_id']
    dias = form['number_day']
    desde = form['date1']
    hasta = form['date2']
    cuota = form['amount']
    zone_ids = []
    if not zone_id:
        zone_ids = pooler.get_pool(cr.dbname).get('res.partner.zone').search(cr, uid, [('type','=','zone')])
    else:
        zone_ids.append(zone_id)
    for zone in zone_ids:
        datos  = _commissions_calculated_seller(cr, uid, zone, desde,hasta, dias,cuota,tipo)
    return resp

class commissions_collection_calculated(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':commissions_collection_form, 'fields':commissions_collection_fields, 'state': [('end', 'Cancelar'),('calculated', 'Aceptar')]}
		},

		'calculated': {
			'actions': [],
			'result' : {'type' : 'choice', 'next_state': _commissions_calculated_collection }
		},
		'message' : {
			'actions' : [],
			'result': {'type':'form', 'arch':_message_collection_form1, 'fields':commissions_collection_fields, 'state':[('end','Ok')]}
		},
	}
commissions_collection_calculated("commissions_collection")
