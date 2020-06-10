# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007 - 2015 Corvus Latinoamerica, C.A. (http://corvus.com.ve) All Rights Reserved
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

import time
import locale
import wizard
import netsvc
import pooler
import tools
from osv.orm import browse_record
import base64
import os.path

#Formulario del Wizard - Datos Entrada------------------------------------------------------------------------------------------------
data_form = '''<?xml version="1.0"?>
<form string="Importar Cuotas de Ventas">
	<separator colspan="2" string="Seleccione al archivo"/>
	<newline/>
	<field name="fdata"/>
	<newline/>
	<field name="fname"/>
</form>'''

data_fields = {
	'fdata': {'string':'Archivo', 'type':'binary', 'filename':'fname','required':True },
	'fname': {'string':'Descripcion', 'type':'char',  'size':90 },
}


#Formulario del Wizard - Datos Salida-------------------------------------------------------------------------------------------------
_result_form = '''<?xml version="1.0"?>
<form string="Informacion">
    <label colspan="4" string="Archivo Procesado" align="0.0"/>
    <newline/>
    <separator colspan="4" string="Detalle:" />
    <newline/>
    <newline/>
    <newline/>
    <label colspan="4" string="a.- Procesados Correctamente:" align="0.0"/>
	<newline/>
	<field name="lines_proc"/>
	<newline/>
	<newline/>
	<newline/>
	<label colspan="4" string="b.- No Procesados:" align="0.0"/>
	<newline/>
	<newline/>
	<field  colspan="4" name="fail_lines"  nolabel="1"/>
	<newline/>
</form>''' 

_result_fields = {
	'lines_proc': {'string': 'Lineas Procesada','type': 'char','readonly': True},
	'fail_lines': {'string': 'Lineas No Procesada','type': 'text','readonly': True, 'size':100},
} 

def _import_cuotas(self, cr, uid, data, context):
    cont = 0
    file_data = data['form']['fdata']
    nf        = data['form']['fname']
    file_name = data['form']['fname']
    #Objetos Requeridos
    zone_obj      = pooler.get_pool(cr.dbname).get('res.partner.zone')
    parameters_zone_obj = pooler.get_pool(cr.dbname).get('parameters.seller.zone')
    
    #List
    val =base64.decodestring(file_data)
    lines = val.split("\n")
    flines = map( lambda x: x.split(';'), lines )
    list_fail = ''
    vals = {}
    for l in flines:
        #print "LIN",l
        if len(l) != 2:
            continue 
        zone_id = ''
        pzone_id = ''
        code	=	l[0].strip()
        amount_total = 0
        if not code:
            continue
        if l[1]:
            amount   = l[1].strip()
            if amount:
                amount_total   = amount.replace('.','')
                amount_total   = amount_total.replace(',','.')
        zone_id = zone_obj.search(cr, uid, [('code_zone','=',code)])
        if zone_id:
            pzone_id = parameters_zone_obj.search(cr, uid, [('zone_id','=',zone_id)])
        if pzone_id:
            cont += 1
            vals = {'amount_total':amount_total}
            pooler.get_pool(cr.dbname).get('parameters.seller.zone').write(cr, uid, pzone_id, vals)
        else:
            list_fail += code + ' \n'
        #print "CODEZ",zone_id,"  ",pzone_id

    return {'lines_proc':str(cont),'fail_lines':list_fail}

class commission_sale_import_cuota(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : data_form, 'fields' : data_fields, 'state' : [('end', 'Cancel'),('finish', 'Siguiente', 'gtk-ok', True) ]}
		},
        'finish':{
            'actions':[_import_cuotas],
            'result':{'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
        },		
	}

commission_sale_import_cuota("commission_import_cuota")
