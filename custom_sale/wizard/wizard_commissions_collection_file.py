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


commissions_form = '''<?xml version="1.0"?>
	<form string="Crear Archivo de Comisiones Cobranza">
		<separator colspan="4" string="Fechas"/>
	    <newline/>
	    <field name="date1"/>
	    <field name="date2"/>
	</form> 
'''

commissions_fields = {
	'date1': {'string':'Desde', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-01-01')},
	'date2': {'string':'Hasta', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
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
    saltoln	= chr(13)+chr(10)
    if not data:
        return {'resultado':"No hay datos...!"}
    form = data['form']
    desde = form['date1']
    hasta = form['date2']
    ruta =  "/home/public/" # Ruta Desarrollo
    ruta =  "/opt/openerp/reportes/credito/" # Ruta Server
    sql = """
    SELECT c.date_start,c.date_stop,p.vat,c.commission_pay    
    FROM commissions_collection_seller AS c
    INNER JOIN res_partner AS p ON c.salesman_id=p.id 
    WHERE c.date_start>='%s' AND c.date_stop<='%s';"""%(desde,hasta)
    cr.execute (sql)
    result = cr.fetchall()
    if not result:
        raise wizard.except_wizard(_('Error !'), _('No existes datos!!!'))

    filename	= ruta+'cobranza.txt'
    output		= open(filename,"w")
    for d in result:
        fi = ''
        fechai = ''
        ff = ''
        fechaf = ''
        ci  = ''
        monto = 0
        if d[0]:
            fi = d[0].split('-')
            fechai		= fi[2] +'-' + fi[1] +'-' + fi[0]
        if d[1]:
            ff = d[1].split('-')
            fechaf		= ff[2] +'-' + ff[1] +'-' + ff[0]
        if d[2]:
            ci = d[2]
            ci = ci.replace('V','') 
        if d[3]:
            monto = d[3]
        monto = locale.format('%.2f',  monto, grouping=True)
        output.write(fechai+';'+fechaf+';'+ci+';05;1;'+monto+saltoln)
    output.close()
    return resp

class commissions_create_collection_file(wizard.interface):
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
commissions_create_collection_file("commissions_collection_file")
