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

#Formulario del Wizard - Datos Entrada------------------------------------------------------------------------------------------------
data_form = '''<?xml version="1.0"?>
	<form string="Calculo de Comisiones - Territorios">
		<field name="zone_id"/>
		<field name="number_day"/>	
		<separator colspan="4" string="Periodo "/>
	    <newline/>
	    <field name="period_id"/>
</form>'''

data_fields = {
	'zone_id':   {'string':'Territorio', 'type':'many2one', 'relation':'res.partner.zone', 'domain':[('type','=','territory')]},
	'number_day': {'string':'Nro. Domingos', 'type':'integer', 'required':True},
	'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'sale.commissionsperiod','required':True, 'domain':[('state','=','draft')]},
}


#Formulario del Wizard - Datos Salida-------------------------------------------------------------------------------------------------
_result_form = '''<?xml version="1.0"?>
<form string="Comisiones Territorio">
    <label colspan="4" string=" " align="0.0"/>
    <newline/>
    <separator colspan="4" string="Comisiones Procesadas Corectamente" />

	<newline/>
</form>''' 

_result_fields = {} 


def _get_det_group(cr, uid, zone_ids, period_id):
    list_group = []
    sqldet = """
    SELECT l.category_id, SUM(l.quantity) as cajas  
    FROM commissions_seller             AS s 
    INNER JOIN commissions_group_line  AS l ON s.id=l.commissions_id 
    WHERE  s.zone_id in (%s) AND s.commission_period_id=%d
    GROUP BY l.category_id
    ORDER BY l.category_id;"""%(zone_ids,period_id)
    #print "SQLD",sqldet
    cr.execute (sqldet)
    datosgroup    =[]
    for gps in cr.fetchall():
        datosgroup.append({0:gps[0],1:gps[1]})   
    return datosgroup

#commissions_calculated_seller------------------------------------------------------------------------------
#
#
def _commissions_calculated(cr, uid, ter_id, zone_ids, period_id, nomb, dias):
    #Inicializacion de variables
    totalcred = 0
    totalcont = 0
    totaldesp = 0
    sale_percent = 0
    pay_total = 0
    group_total = 0
    #Vendedor - para la zona
    ids_str = ','.join(map(str,zone_ids))
    #Se obtienen los parametros del territorio, que su usaran para el calculo
    obj_paramerters_ter = pooler.get_pool(cr.dbname).get('parameters.seller.zone')
    parameters_id = obj_paramerters_ter.search(cr, uid, [('zone_id','=',ter_id),('active','=',1)])
    if parameters_id:
        parameters_ter = obj_paramerters_ter.browse(cr, uid, parameters_id[0])
    else:
        raise wizard.except_wizard(_('Error !'), _('No existen parametros definidos para el territorio '))

    obj_partner = pooler.get_pool(cr.dbname).get('res.partner')
    if parameters_ter and parameters_ter.seller_id.id:
        partner_id = parameters_ter.seller_id.id
        datospartner = obj_partner.browse(cr, uid, partner_id)
    else:
        raise wizard.except_wizard(_('Error !'), _('No existen un Gerente Asignado al territorio '))
    #partner_id = pooler.get_pool(cr.dbname).get('res.partner').search(cr, uid, [('code_zone_id','=',ter_id),('salesman','=',1) ])
    #if partner_id: 
    #    datospartner = obj_partner.browse(cr, uid, partner_id[0])
    #else:
    #    return False
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
        if parameters_ter.amount_total > 0:
            sale_percent = totaldesp / parameters_ter.amount_total * 100
            if sale_percent > parameters_ter.percent_max:
                sale_percent = parameters_ter.percent_max
            pay_total = sale_percent * parameters_ter.value_total / 100
    groups = []
    tcajas = 0
    tbscajas = 0
    min   = 0
    max   = 0
    qbase = 0
    qty   = 0
    total_grupos = _get_det_group(cr, uid, ids_str,period_id)
    for p in parameters_ter.parameters_line:
        if p.quota_amount > 0 and p.quota_qty > 0:
            qbase = p.quota_amount
            qty   = p.quota_qty
            min   = p.min
            max   = p.max
        categ_id = p.categ_salesman_id.id
        nb_categ = 'MAS'
        for grp in total_grupos:
            if p.categ_salesman_id.id == grp[0]:
                tcajas += grp[1]
                #print "TOTAL-GRUPOS",tcajas 
    #Parametros de los grupos
    porcent = 0
    if tcajas and qty and qbase:
        porcent = tcajas / qty * 100
        if porcent > max:
            porcent = max
        if porcent >= min:
            tbscajas = qbase * porcent / 100
        groups.append((0,0,{'category_id':categ_id,'name':nb_categ,'quantity': tcajas,'quota_amount': qbase,'quota_qty': qty,'percent_quota': porcent,'amount': tbscajas }))
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
            'zone_id':ter_id,
            'salesman_id':partner_id,
            'commission_invoice':False,
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
    return True

#commissions_calculated_seller_zone------------------------------------------------------------------------------
#
#
def _commissions_calculated_seller_ter(self, cr, uid, data, context={}):
    if not data:
        raise wizard.except_wizard(_('Error !'), _('No Existen Datos !!!'))
    form = data['form']
    period_id = form['period_id']
    ter_id = form['zone_id']
    dias = form['number_day']
    periodo = pooler.get_pool(cr.dbname).get('sale.commissionsperiod').browse(cr, uid, period_id, context)
    desde = periodo.date_start
    hasta = periodo.date_stop
    nomb = periodo.name
    zone_ids = []
    territory_ids = []
    if not ter_id:
        territory_ids = pooler.get_pool(cr.dbname).get('res.partner.zone').search(cr, uid, [('type','=','territory')])
    else:
        territory_ids.append(ter_id)
    for t in territory_ids:
        zone_ids = pooler.get_pool(cr.dbname).get('res.partner.zone').search(cr, uid, [('parent_id','=',t)])
        datos  = _commissions_calculated(cr, uid, t, zone_ids, period_id, nomb, dias)
    return {}
 

class commissions_calculated_territory(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : data_form, 'fields' : data_fields, 'state' : [('end', 'Cancel'),('finish', 'Siguiente', 'gtk-ok', True) ]}
		},
        'finish':{
            'actions':[_commissions_calculated_seller_ter],
            'result':{'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
        },		
	}

commissions_calculated_territory("commissions_seller_territory")
