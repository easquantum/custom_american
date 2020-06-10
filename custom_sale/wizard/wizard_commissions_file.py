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
import codecs
from osv.orm import browse_record
import mx.DateTime


commissions_form = '''<?xml version="1.0"?>
	<form string="Crear Archivo Banco de Comisiones">
		<separator colspan="4" string="Periodo Facturacion"/>
	    <newline/>
	    <field name="period_id"/>
	</form> 
'''

commissions_fields = {
	#'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'period.generalperiod','required':True},
	'period_id': {'string':'Periodo', 'type':'many2one', 'relation':'sale.commissionsperiod','required':True},
}

_message_form1 = '''<?xml version="1.0"?>
						<form string="Informacion">
							 <label string=" OK: Archivo Creado   !!!" colspan="2"/>
							<newline/>
						</form>''' 


#commissions_file_seller-------------------------------------------------------------------------------------------
#
#
def _commissions_file_seller(self, cr, uid, data, context={}):
    resp ='message'
    saltoln	= chr(13)
    if not data:
        return {'resultado':"No hay datos...!"}
    form = data['form']
    period_id = form['period_id']
    #periodo = pooler.get_pool(cr.dbname).get('period.generalperiod').browse(cr, uid, period_id, context)
    periodo = pooler.get_pool(cr.dbname).get('sale.commissionsperiod').browse(cr, uid, period_id, context)
    desde = periodo.date_start
    hasta = periodo.date_stop
    nomb = periodo.name
    #ruta =  "/home/public/" # Ruta Desarrollo
    ruta =  "/opt/openerp/reportes/personal/" # Ruta Server
    sql = """
    SELECT b.acc_number,p.vat,c.commission_pay,p.name   
    FROM commissions_seller AS c
    INNER JOIN res_partner AS p ON c.salesman_id=p.id 
    INNER JOIN res_partner_bank AS b ON p.id=b.partner_id 
    WHERE c.commission_period_id=%d;"""%period_id
    cr.execute (sql)
    result = cr.fetchall()
    if not result:
        raise wizard.except_wizard(_('Error !'), _('No existes datos!!!'))

    filename	= ruta+'comisiones.txt'
    output		= codecs.open(filename,"w", "utf-8")
    for d in result:
        cta = '02'
        ci  = ''
        monto = 0
        nombre = ''
        if d[0]:
            cta += d[0]
        if d[1]:
            ci = d[1]
            ci = ci.replace('V','') 
        if d[2]:
            monto = d[2]
        cta = cta.zfill(22)
        ci  = ci.strip()
        ci  = ci.zfill(8)
        ci  = 'V'+ci
        monto = locale.format('%.2f',  monto, grouping=True)
        monto	= monto.replace(',','')
        monto = monto.zfill(17)
        monto = monto.rjust(24)
        nombre = d[3]
        nombre = nombre.ljust(43)
        output.write(cta+ci+monto+nombre+'\r\n')
    output.close()
    return resp

class commissions_create_file(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':commissions_form, 'fields':commissions_fields, 'state': [('end', 'Cancelar'),('createfile', 'Aceptar')]}
		},

		'createfile': {
			'actions': [],
			'result' : {'type' : 'choice', 'next_state': _commissions_file_seller }
		},
		'message' : {
			'actions' : [],
			'result': {'type':'form', 'arch':_message_form1, 'fields':commissions_fields, 'state':[('end','OK')]}
		},
	}
commissions_create_file("commissions_file_bank")
