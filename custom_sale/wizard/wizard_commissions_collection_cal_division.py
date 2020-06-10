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

#Formulario del Wizard - Datos Entrada------------------------------------------
data_form = '''<?xml version="1.0"?>
	<form string="Calculo de Comisiones - Divisiones">
		<field name="division_id"/>
		<field name="number_day"/>
		<field name="amount"/>
		<field name="commissions_type"/>	
		<separator colspan="4" string=" "/>
	    <newline/>
	    <field name="period_id" string="Perido"/>
</form>'''

data_fields = {
	'division_id':   {'string':'Division', 'type':'many2one', 'relation':'res.partner.zone','required':True,'domain':[('type','=','division')]},
	'number_day': {'string':'Nro. Domingos', 'type':'integer', 'required':True},
	'amount': {'string':'cuota', 'type':'float', 'required':True},
	'commissions_type': {'string':'Comision Tipo:', 'type':'selection', 'readonly':1, 'default': lambda *a: 'division','selection':[('division','Division')]},
	'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'sale.commissionsperiod','required':True,'domain':[('state','=','draft')]},
}


#Formulario del Wizard - Datos Salida----------------------------------------------
_result_form = '''<?xml version="1.0"?>
    <form string="Comisiones Territorio">
        <label colspan="4" string=" " align="0.0"/>
        <newline/>
        <separator colspan="4" string="Comisiones Procesadas Corectamente" />
    
    	<newline/>
    </form>
''' 

_result_fields = {} 


#commissions_calculated_seller------------------------------------------------------------------------------
#
#
def _collection_calculated_division(cr, uid, div_id, ter_ids, period_id, nomb, dias,tipo,cuota,partner_id,desde,hasta):
    #Inicializacion de variables
    collection_total = 0
    vals = {
            'name': nomb,
            'zone_id': div_id,
            'salesman_id': partner_id,
            'commissions_type': tipo,
            'commission_period_id':period_id,
            'date_start': desde,
            'date_stop': hasta,
            'number_days':dias,
            'collection_line': [],
            'quota_annual': 0,
            'quota_amount': cuota,
            'collection_total': 0,
            'daily_salary': 0,
            }          

    #Zonas del Territorio
    ids_str = ','.join(map(str,ter_ids))
    #Obtener 
    sql = """
    SELECT SUM(collection_total) as total
    FROM commissions_collection_seller  
    WHERE  commission_period_id=%d AND zone_id in (%s)"""%(period_id,ids_str)
    #print sql 
    cr.execute (sql)
    datos = cr.fetchall()
    if datos and datos[0]:
        collection_total = datos[0][0]
    vals['collection_total'] = collection_total
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

    #Registrando la comision 
    pooler.get_pool(cr.dbname).get('commissions.collection.seller').create(cr, uid, vals, context={})
    return True

#commissions_calculated_seller_zone------------------------------------------------------------------------------
#
#
def _commissions_collection_calculated_div(self, cr, uid, data, context={}):
    if not data:
        raise wizard.except_wizard(_('Error !'), _('No Existen Datos !!!'))
    form = data['form']
    period_id = form['period_id']
    div_id = form['division_id']
    dias = form['number_day']
    tipo = form['commissions_type']
    cuota = form['amount']
    periodo = pooler.get_pool(cr.dbname).get('sale.commissionsperiod').browse(cr, uid, period_id, context)
    desde = periodo.date_start
    hasta = periodo.date_stop
    nomb = periodo.name
    #Gerente Territorial
    obj_partner = pooler.get_pool(cr.dbname).get('res.partner')
    partner_id = pooler.get_pool(cr.dbname).get('res.partner').search(cr, uid, [('code_zone_id','=',div_id),('salesman','=',1) ])
    if partner_id and partner_id[0]: 
        partn_id = partner_id[0]
    else:
        return {'resultado':"No hay Gerente Divisional Asignado, por favor signar uno y procesar nuevamente...!"}


    zone_ids = []
    if div_id:
        ter_ids = pooler.get_pool(cr.dbname).get('res.partner.zone').search(cr, uid, [('parent_id','=',div_id)])
        datos  = _collection_calculated_division(cr, uid,div_id,ter_ids,period_id,nomb,dias,tipo,cuota,partn_id,desde,hasta)
    return {}
 

class commiss_collection_calc_division(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : data_form, 'fields' : data_fields, 'state' : [('end', 'Cancel'),('finish', 'Siguiente', 'gtk-ok', True) ]}
		},
        'finish':{
            'actions':[_commissions_collection_calculated_div],
            'result':{'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
        },		
	}

commiss_collection_calc_division("commissions_collection_calc_div")
