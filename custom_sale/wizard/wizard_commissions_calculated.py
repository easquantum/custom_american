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


commissions_form = '''<?xml version="1.0"?>
	<form string="Calculo de Comisiones">
		<field name="zone_id"/>
		<field name="number_day"/>	
		<separator colspan="4" string="Periodo Facturacion"/>
	    <newline/>
	    <field name="period_id"/>
	</form> 
'''

commissions_fields = {
	'zone_id':   {'string':'Zona', 'type':'many2one', 'relation':'res.partner.zone','required':True},
	'number_day': {'string':'Nro. Domingos', 'type':'integer', 'required':True},
	#'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'period.generalperiod','required':True},
	'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'sale.commissionsperiod','required':True, 'domain':[('state','=','draft')]},
}

_message_form1 = '''<?xml version="1.0"?>
						<form string="Informacion">
							 <label string=" OK: Comisiones Procesadas   !!!" colspan="2"/>
							<newline/>
						</form>''' 

#get_order_cancel----------------------------------------------------------------------------------------------
# 
def _get_order_cancel_bs(cr, uid, zone,desde,hasta):
    totalc = {'ttperiodo_con':0,'ttperiodo_cred':0,'ttcanc_con':0,'ttcanc_cred':0}
    #Canceladas - Notas de Salida Canceladas del periodo o periodos anteriores
    sqlc = """
    SELECT o.id,p.id,o.date_order,t.contado,SUM(m.product_qty) as cajas,o.name  
    FROM       sale_order           AS o  
    INNER JOIN stock_picking        AS p ON o.id=p.sale_id
    INNER JOIN stock_move           AS m ON p.id=m.picking_id 
    INNER JOIN account_payment_term AS t ON o.payment_term=t.id 
    WHERE  o.code_zone_id=%d  AND p.date_cancel BETWEEN '%s' AND '%s' AND p.state='cancel' 
    GROUP BY o.id,p.id,o.date_order,t.contado,o.name
    ORDER BY o.date_order"""%(zone,desde,hasta) 
    #print sqlc 
    cr.execute (sqlc)
    datoscancel  = cr.fetchall()
    for dc in datoscancel:
        if dc[0] and dc[1]:
            #Se obtiene el monto para cada producto, NOTA: no se suma en el Query, por que la data 
            #no es consistente y puede dar un monto erredo...!!!
            sqline = "SELECT sale_line_id,product_qty FROM stock_move WHERE  picking_id=%d;"%dc[1]
            cr.execute (sqline)
            datosline  = cr.fetchall()
            total = 0
            for pck in datosline:
                sqlorder = "SELECT price_unit FROM sale_order_line WHERE  order_id=%d AND id=%d;"%(dc[0],pck[0])
                cr.execute (sqlorder)
                orderdat  = cr.fetchall() 
                subtotal = pck[1] * orderdat[0][0] 
                total += subtotal
            tmp = str(total)
            tmp = tmp.replace('.',',')
            #print dc[5],'; ',int(dc[4]),';',tmp  
            if total:
                if dc[2] < desde:                      #Canceladas Periodos Anteriores
                    if dc[3]: 
                        totalc['ttcanc_con'] += total
                    else:
                        totalc['ttcanc_cred'] += total
                elif dc[3]:                            #Canceladas en el Periodo
                    totalc['ttperiodo_con'] += total
                else:
                    totalc['ttperiodo_cred'] += total
    #print "Cancelado",totalc  
    return totalc

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
    totalnc = {'notacre':0,'notacash':0}
    for nc in datosnc:
        ttnc += nc[2]
        if nc[1]:
            totalnc['notacash'] += nc[2]
        else:
            totalnc['notacre'] += nc[2]
    #print "TOTAL-NC", ttnc
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
    WHERE a.internal=False AND a.type='out_refund' AND a.state!='cancel' AND a.code_zone_id=%d AND a.date_invoice BETWEEN '%s' AND '%s'
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
    SELECT p.categ_salesman_id,c.description, SUM(l.product_uom_qty) as cajas  
    FROM       sale_order                      AS o 
    INNER JOIN sale_order_line           AS l ON o.id=l.order_id 
    INNER JOIN product_product           AS p ON l.product_id=p.id
    INNER JOIN product_category_salesman AS c ON p.categ_salesman_id=c.id
    WHERE  o.state in ('progress','done') AND o.code_zone_id=%d AND o.date_order BETWEEN '%s' AND '%s'
    GROUP BY p.categ_salesman_id, c.description
    ORDER BY p.categ_salesman_id;"""%(zone,desde,hasta)
    #print sqldet
    cr.execute (sqldet)
    datosgroup    =[]
    for gps in cr.fetchall():
        datosgroup.append({0:gps[0],1:gps[1],2:gps[2]})   
    sqldetcancel = """
    SELECT p.categ_salesman_id,c.description, SUM(m.product_qty) as cajas  
    FROM       sale_order                AS o
    INNER JOIN stock_picking             AS s ON o.id=s.sale_id
    INNER JOIN stock_move                AS m ON s.id=m.picking_id 
    INNER JOIN product_product           AS p ON m.product_id=p.id
    INNER JOIN product_category_salesman AS c ON p.categ_salesman_id=c.id
    WHERE  o.code_zone_id=%d AND s.type='out' AND s.type2='def' AND s.state = 'cancel'  
    AND    s.date_cancel BETWEEN '%s' AND '%s'
    GROUP BY p.categ_salesman_id, c.description
    ORDER BY p.categ_salesman_id;"""%(zone,desde,hasta)
    cr.execute (sqldetcancel)
    for gcancel in cr.fetchall():
        c = -1
        for g in datosgroup:
            c += 1
            if gcancel[0] == g[0]:
                datosgroup[c][2] = g[2] - gcancel[2]
                break   
    return datosgroup
#commissions_calculated_seller------------------------------------------------------------------------------
#
#
def _commissions_calculated_seller(cr, uid,  zona, desde,hasta, nomb, dias,period_id,context={}):
    #Vendedor - para la zona
    obj_partner = pooler.get_pool(cr.dbname).get('res.partner')
    partner_id = pooler.get_pool(cr.dbname).get('res.partner').search(cr, uid, [('code_zone_id','=',zona),('salesman','=',1) ])
    if partner_id: 
        datospartner = obj_partner.browse(cr, uid, partner_id[0])
    else:
        return {'resultado':"No hay Vendedor Asignado a la zona...!"}
    #Obtener Pedidos procesados 
    sql = """
    SELECT o.code_zone_id,t.contado, SUM(l.product_uom_qty * l.price_unit ) as total  
    FROM sale_order                 AS o  
    INNER JOIN sale_order_line      AS l ON o.id=l.order_id 
    INNER JOIN account_payment_term AS t ON o.payment_term=t.id 
    WHERE o.state in ('progress','done') AND o.code_zone_id=%d AND o.date_order BETWEEN '%s' AND '%s'
    GROUP BY o.code_zone_id,t.contado"""%(zona,desde,hasta)
    #print sql 
    cr.execute (sql)
    datosped = cr.fetchall()
    deductions = []
    vals = {
            'name':nomb,
            'zone_id':zona,
            'commission_period_id':period_id,
            'date_period': time.strftime('%Y-%m-%d'),
            'number_days':dias,
            'deductions_line': deductions,
            'amount_total_deduct': 0,
            'amount_cash_order': 0,
            'amount_cred_order': 0,
            'amount_cash_cancel': 0,
            'amount_cred_cancel': 0,                    
            'amount_cash_refund': 0,
            'amount_cred_refund': 0,
          }
    if datosped:
        for ped in datosped:
            contado = ped[1]
            if contado:
                vals['amount_cash_order'] += ped[2]
            else:
                vals['amount_cred_order'] += ped[2]
        #Monto Cancelado y Notas Credito----------------------------------------------------------------------
        totalc  = _get_order_cancel_bs(cr, uid, zona, desde, hasta)
        totalnc = _get_order_refund_bs(cr, uid, zona, desde, hasta)
        vals['amount_cash_order'] -= totalc['ttperiodo_con']
        vals['amount_cred_order'] -= totalc['ttperiodo_cred']
        vals['amount_cash_cancel'] = totalc['ttcanc_con']
        vals['amount_cred_cancel'] = totalc['ttcanc_cred']
        vals['amount_cash_refund'] = totalnc['notacash']
        vals['amount_cred_refund'] = totalnc['notacre']
        
        #Totales Ventas Bs.---------------------------------------------------------------------------------------
        vals['credit_total'] = vals['amount_cred_order'] - vals['amount_cred_cancel'] - vals['amount_cred_refund']
        vals['cash_total'] = vals['amount_cash_order'] - vals['amount_cash_cancel'] - vals['amount_cash_refund']
        vals['sale_total'] = vals['credit_total'] + vals['cash_total']
        vals['cash_pay']  = 0
        vals['pay_total'] = 0
        if datospartner.amount_cash > 0:
            vals['cash_percent'] = vals['cash_total'] /  datospartner.amount_cash * 100
            if vals['cash_percent'] > datospartner.percent_max:
                vals['cash_percent'] = datospartner.percent_max
            vals['cash_pay'] = vals['cash_percent'] * datospartner.value_cash /100
        if datospartner.amount_total > 0:
            vals['sale_percent'] = vals['sale_total'] / datospartner.amount_total * 100
            if vals['sale_percent'] > datospartner.percent_max:
                vals['sale_percent'] = datospartner.percent_max 
            vals['pay_total'] = vals['sale_percent'] * datospartner.value_total /100
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
        for p in datospartner.parameters_line:
            #obtener Parametros del Grupo
            qbase = p.quota_amount
            qty   = p.quota_qty
            porcent = 0
            tbscajas = 0
            qty_sale   = 0
            for grp in total_grupos:
                if p.categ_salesman_id.id == grp[0]:
                    qbase = p.quota_amount
                    qty   = p.quota_qty
                    min = p.min
                    qty_sale   = grp[2]
                    if grp[2] and qty and qbase:
                        porcent = grp[2] / qty * 100
                        if porcent > p.max:
                            porcent = p.max
                        #print grp[2],' - ', qty,'---',porcent
                        if porcent >= p.min:
                            tbscajas = qbase * porcent / 100
                            totalgralcajas += tbscajas
                    break
            groups.append((0,0,{'category_id':p.categ_salesman_id.id,'name':p.categ_salesman_id.description,'quantity': qty_sale,'quota_amount': qbase,'quota_qty': qty,'percent_quota': porcent,'amount': tbscajas }))
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
            vals['salesman_id'] = partner_id[0]
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
        pooler.get_pool(cr.dbname).get('commissions.seller').create(cr, uid, vals, context)
    return True


#commissions_calculated_seller_zone------------------------------------------------------------------------------
#
#
def _commissions_calculated_seller_zone(self, cr, uid, data, context={}):
    resp ='message'
    if not data:
        return {'resultado':"No hay datos...!"}
    form = data['form']
    period_id = form['period_id']
    zone_id = form['zone_id']
    dias = form['number_day']
    #periodo = pooler.get_pool(cr.dbname).get('period.generalperiod').browse(cr, uid, period_id, context)
    periodo = pooler.get_pool(cr.dbname).get('sale.commissionsperiod').browse(cr, uid, period_id, context)
    desde = periodo.date_start
    hasta = periodo.date_stop
    nomb = periodo.name
    zone_ids = []
    if not zone_id:
        zone_ids = pooler.get_pool(cr.dbname).get('res.partner.zone').search(cr, uid, [('type','=','zone')])
    else:
        zone_ids.append(zone_id)
    for zone in zone_ids:
        datos  = _commissions_calculated_seller(cr, uid, zone, desde,hasta, nomb, dias,period_id)
    return resp

class commissions_calculated(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':commissions_form, 'fields':commissions_fields, 'state': [('end', 'Cancelar'),('calculated', 'Aceptar')]}
		},

		'calculated': {
			'actions': [],
			'result' : {'type' : 'choice', 'next_state': _commissions_calculated_seller_zone }
		},
		'message' : {
			'actions' : [],
			'result': {'type':'form', 'arch':_message_form1, 'fields':commissions_fields, 'state':[('end','OK')]}
		},
	}
commissions_calculated("commissions_seller")
