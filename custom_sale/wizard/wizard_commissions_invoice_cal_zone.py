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
	<form string="Calculo Comisiones Despachados por Zona">
		<field name="zone_id"/>
		<field name="number_day"/>	
		<separator colspan="4" string="Periodo Facturacion"/>
	    <newline/>
	    <field name="period_id"/>
</form>'''

data_fields = {
	'zone_id':   {'string':'Zona', 'type':'many2one', 'relation':'res.partner.zone','required':True, 'domain':[('type','=','zone')]},
	'number_day': {'string':'Nro. Domingos', 'type':'integer', 'required':True},
	'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'sale.commissionsperiod','required':True, 'domain':[('state','=','draft')]},
}


#Formulario del Wizard - Datos Salida-------------------------------------------------------------------------------------------------
_result_form = '''<?xml version="1.0"?>
<form string="Comisiones Zonas">
    <label colspan="4" string="Info" align="0.0"/>
    <newline/>
    <separator colspan="4" string="Comisiones Procesadas Corectamente" />

	<newline/>
</form>''' 

_result_fields = {} 


#get_order_refund--------------------------------------------------------------------------------------
# Obtener Notas Credito del periodo para cada vendedor
#
def _get_order_refund_bs(cr, uid, zone,desde,hasta):
    sqlnc = """
    SELECT a.id,t.contado,amount_untaxed       
    FROM account_invoice AS a  
    LEFT JOIN account_payment_term AS t ON a.payment_term=t.id 
    WHERE  a.internal=False AND a.type='out_refund' AND a.state!='cancel' AND a.code_zone_id=%d AND date_invoice BETWEEN '%s' AND '%s'
    """%(zone,desde,hasta) 
    cr.execute (sqlnc)
    datosnc  = cr.fetchall()
    ttnc = 0
    totalnc = 0
    descuentonc = 0
    for nc in datosnc:
        totalnc += nc[2]
    #print "TOTAL-NC",totalnc
    #Facturas Descuentos en Notas Credito
    sqldnc = """
    SELECT SUM(it.tax_amount) AS totaldnc 
    FROM account_invoice As i 
    INNER JOIN  account_invoice_tax AS it ON i.id=it.invoice_id 
    INNER JOIN  account_tax AS t ON it.name=t.name 
    WHERE  i.internal=False AND i.type='out_refund' AND i.state!='cancel' AND i.code_zone_id=%d
    AND i.date_invoice BETWEEN '%s' AND '%s' AND t.tax_group='other'
    """%(zone,desde,hasta)
    cr.execute (sqldnc)
    descuentonc = cr.fetchall()
    if descuentonc and descuentonc[0] and descuentonc[0][0]:
        totalnc += descuentonc[0][0]
    return totalnc

#get_order_refund_group--------------------------------------------------------------------------------------
# Obtener Notas Credito por cajas
#
def _get_order_refund_group(cr, uid, zone,desde,hasta):
    sqlncgp = """
    SELECT p.categ_salesman_id,c.name,SUM(l.quantity) as total       
    FROM account_invoice                 AS a  
    INNER JOIN account_invoice_line      AS l ON a.id=l.invoice_id 
    INNER JOIN product_product           AS p ON l.product_id=p.id 
    INNER JOIN product_category_salesman AS c ON p.categ_salesman_id=c.id
    WHERE  a.internal=False and a.adjustment=False and a.type='out_refund' 
    AND a.state!='cancel' AND a.code_zone_id=%d AND a.date_invoice BETWEEN '%s' AND '%s'
    GROUP BY p.categ_salesman_id, c.name"""%(zone,desde,hasta) 
    cr.execute (sqlncgp)
    datosncgp  = cr.fetchall()
    if datosncgp:
        return datosncgp
    else:
        return False

def _get_det_group(cr, uid, zone,desde,hasta):
    list_group = []
    sqldet = """
    SELECT p.categ_salesman_id,c.name,SUM(l.quantity) as total       
    FROM account_invoice                 AS a  
    INNER JOIN account_invoice_line      AS l ON a.id=l.invoice_id 
    INNER JOIN product_product           AS p ON l.product_id=p.id 
    INNER JOIN product_category_salesman AS c ON p.categ_salesman_id=c.id
    WHERE  a.internal=False  AND a.type='out_invoice' AND a.state!='cancel' AND a.code_zone_id=%d   
    AND a.date_invoice BETWEEN '%s' AND '%s'
    GROUP BY p.categ_salesman_id, c.name"""%(zone,desde,hasta) 
    #print sqldet
    cr.execute (sqldet)
    datosgroup    =[]
    for gps in cr.fetchall():
        datosgroup.append({0:gps[0],1:gps[1],2:gps[2]})   
   
    return datosgroup
#commissions_calculated_seller------------------------------------------------------------------------------
#
#
def _commissions_calculated_seller(cr, uid, zona, desde,hasta, nomb, dias, period_id, cuota_percent, context={}):
    #Cuotas
    cuota_year    = 0
    cuota_month   = 0
    #Se obtienen los parametros del la Zona, que su usaran para el calculo
    obj_paramerters_zone = pooler.get_pool(cr.dbname).get('parameters.seller.zone')
    parameters_id = obj_paramerters_zone.search(cr, uid, [('zone_id','=',zona),('active','=',1)])

    if parameters_id:
        parameters_zone = obj_paramerters_zone.browse(cr, uid, parameters_id[0])
    else:
        raise wizard.except_wizard(_('Error !'), _('No existen parametros definidos para la zona '))
    obj_partner = pooler.get_pool(cr.dbname).get('res.partner')
    if parameters_zone and parameters_zone.seller_id.id: 
        partner_id    = parameters_zone.seller_id.id
        cuota_year    =parameters_zone.amount_total
        datospartner = obj_partner.browse(cr, uid, partner_id)
    else:
        raise wizard.except_wizard(_('Error !'), _('No existen un Vendedor Asignado a la zona '))
    #Calculo de cuota mensual
    if cuota_percent and cuota_year:
        cuota_month   = cuota_year * cuota_percent / 100
        cuota_month   = round(cuota_month) 

    #Facturas del Periodo 
    sql = """
    SELECT SUM(amount_untaxed) AS total       
    FROM account_invoice 
    WHERE  internal=False AND type='out_invoice' AND state!='cancel' AND code_zone_id=%d AND date_invoice BETWEEN '%s' AND '%s'
    """%(zona,desde,hasta)
    #print sql
    cr.execute (sql)
    facturado       = cr.fetchall()
    total_facturado = 0
    if facturado and facturado[0] and facturado[0][0]:
        total_facturado = facturado[0][0]
    #Facturas Descuentos en Factura 
    sqld = """
    SELECT SUM(it.tax_amount) AS total       
    FROM account_invoice As i
    INNER JOIN  account_invoice_tax AS it ON i.id=it.invoice_id
    INNER JOIN  account_tax AS t ON it.name=t.name
    WHERE  i.internal=False AND i.type='out_invoice' AND i.state!='cancel' AND i.code_zone_id=%d 
    AND i.date_invoice BETWEEN '%s' AND '%s' AND t.tax_group='other'
    """%(zona,desde,hasta)
    #print sql
    cr.execute (sqld)
    descuento       = cr.fetchall()
    if descuento and descuento[0] and descuento[0][0]:
        total_facturado += descuento[0][0]
    deductions = []
    vals = {
            'name':nomb,
            'zone_id':zona,
            'commission_invoice':True,
            'commission_period_id':period_id,
            'date_period': time.strftime('%Y-%m-%d'),
            'number_days':dias,
            'cuota_percent':cuota_percent,
            'cuota_year': cuota_year,
            'cuota_month':cuota_month,
            'amount_total_deduct': 0,
            'amount_cash_order': 0,
            'amount_cred_order': total_facturado,
            'amount_cash_cancel': 0,
            'amount_cred_cancel': 0,                    
            'amount_cash_refund': 0,
            'amount_cred_refund': 0,
            'deductions_line': deductions,
          }

    #Notas Credito
    totalnc = _get_order_refund_bs(cr, uid, zona, desde, hasta)
    if totalnc:
        vals['amount_cred_refund'] = totalnc
    #print "VALS_COMMISS",vals
    #return True
        
    #Totales Ventas Bs.---------------------------------------------------------------------------------------
    vals['credit_total'] = vals['amount_cred_order'] - vals['amount_cred_refund']
    vals['cash_total'] = 0
    vals['sale_total'] = vals['credit_total'] + vals['cash_total']
    vals['cash_pay']  = 0
    vals['pay_total'] = 0
    vals['cash_percent'] = 0
    vals['cash_pay']     = 0
    percent_done         = 0
    if cuota_month > 0:
        vals['sale_percent'] = vals['sale_total'] / cuota_month * 100
        if vals['sale_percent'] < parameters_zone.percent_min:
            vals['sale_percent'] = 0
        if vals['sale_percent'] > parameters_zone.percent_max:
            vals['sale_percent'] = parameters_zone.percent_max 
        if vals['sale_percent']:
            vals['pay_total'] = vals['sale_percent'] * parameters_zone.value_total /100
    vals['amount_base'] = vals['pay_total'] + vals['cash_pay']
    #Total Ventas por Cajas - Grupos ------------------------------------------------------
    vals['amount_group'] = 0
    groups = []
    qbase = 0
    qty   = 0
    porcent = 0
    tbscajas = 0
    totalgralcajas = 0
    total_grupos = _get_det_group(cr, uid, zona,desde,hasta)
    total_ncgrp =_get_order_refund_group(cr, uid, zona,desde,hasta)
    #total_ncgrp = False
    if total_ncgrp:
        cntgrp = 0
        for ncgrp in total_ncgrp:
            cntgrp = -1
            for gp in total_grupos:
                cntgrp += 1
                if ncgrp[0] == gp[0]:
                    total_grupos[cntgrp][2] = total_grupos[cntgrp][2] - ncgrp[2]
                    break
    for p in parameters_zone.parameters_line:
        #obtener Parametros del Grupo
        qbase = p.quota_amount
        qty_anual = p.quota_qty
        if qty_anual == 0:
            continue
        qty   = qty_anual * cuota_percent / 100
        qty   = round(qty)
        porcent = 0
        tbscajas = 0
        qty_sale   = 0
        for grp in total_grupos:
            if p.categ_salesman_id.id == grp[0]:
                qty_sale   = grp[2]
                if grp[2] and qty and qbase:
                    porcent = grp[2] / qty * 100
                    if porcent > p.max:
                        porcent = p.max
                    if porcent < p.min:
                        porcent = 0
                    if porcent >= p.min:
                        tbscajas = qbase * porcent / 100
                        totalgralcajas += tbscajas
                break
        groups.append((0,0,{'category_id':p.categ_salesman_id.id,'name':p.categ_salesman_id.description,'cuota_year':qty_anual,'quota_qty': qty,'percent_quota': porcent,'quota_amount': qbase,'quantity': qty_sale,'amount': tbscajas }))
    if groups:
        vals['group_line'] =  groups
        vals['amount_group'] = totalgralcajas       
    #Subtotal Ventas-----------------------------------------------------------------------
    vals['commission_base'] = vals['amount_base'] + vals['amount_group']
    vals['daily_salary'] = vals['commission_base'] / 30
    vals['amount_holiday'] = vals['daily_salary'] * vals['number_days'] 
    vals['amount_total_asig'] = vals['commission_base'] + vals['amount_holiday']
    #Deducciones
    totaldeductions  = 0
    if partner_id:
        vals['salesman_id'] = partner_id
        for d in datospartner.deductions_line:
            monto_deduc = 0
            if d.amount_total > 0:
                monto_deduc = d.amount_total
            if d.percent > 0 and vals['amount_total_asig'] > 0:
                monto_deduc = vals['amount_total_asig'] * d.percent / 100
            totaldeductions  += monto_deduc
            deductions.append((0,0,{'name':d.name ,'amount':monto_deduc ,'deductions_id':d.deduction_id.id }))
        vals['deductions_line'] = deductions
        vals['amount_total_deduct'] = totaldeductions
        vals['commission_pay'] = vals['amount_total_asig'] - vals['amount_total_deduct']
    #print "VALS",vals
    pooler.get_pool(cr.dbname).get('commissions.seller').create(cr, uid, vals, context)
    return True


#commissions_calculated_seller_zone------------------------------------------------------------------------------
#
#
def _commissions_calculated_seller_zone(self, cr, uid, data, context={}):
    #Cuotas
    cuota_percent = 0
    if not data:
        raise wizard.except_wizard(_('Error !'), _('No Existen Datos !!!'))
    form = data['form']
    period_id = form['period_id']
    zone_id = form['zone_id']
    dias = form['number_day']
    periodo = pooler.get_pool(cr.dbname).get('sale.commissionsperiod').browse(cr, uid, period_id, context)
    desde = periodo.date_start
    hasta = periodo.date_stop
    nomb = periodo.name
    if periodo.percent:
        cuota_percent = periodo.percent
    if not zone_id:
        raise wizard.except_wizard(_('Error !'), _('Indique la Zona !!!'))

    datos  = _commissions_calculated_seller(cr, uid, zone_id, desde,hasta, nomb, dias,period_id,cuota_percent)
    return {}
 

class commissions_invoice_calculated_zone(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : data_form, 'fields' : data_fields, 'state' : [('end', 'Cancel'),('finish', 'Siguiente', 'gtk-ok', True) ]}
		},
        'finish':{
            'actions':[_commissions_calculated_seller_zone],
            'result':{'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
        },		
	}

commissions_invoice_calculated_zone("commissions_invoice_zone")
