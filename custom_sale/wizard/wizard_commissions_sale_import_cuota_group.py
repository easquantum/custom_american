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
<form string="Importar Cuotas Cajas">
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

def _import_cuotas_group(self, cr, uid, data, context):
    cont = 0
    file_data = data['form']['fdata']
    nf        = data['form']['fname']
    file_name = data['form']['fname']
    #Objetos Requeridos
    zone_obj      = pooler.get_pool(cr.dbname).get('res.partner.zone')
    category_obj = pooler.get_pool(cr.dbname).get('product_category_salesman')
    parameters_zone_obj = pooler.get_pool(cr.dbname).get('parameters.seller.zone')
    parameters_group_obj = pooler.get_pool(cr.dbname).get('parameters.seller')
    
    #List
    val =base64.decodestring(file_data)
    lines = val.split("\n")
    flines = map( lambda x: x.split(';'), lines )
    list_fail = ''
    cont = 0
    vals = {}
    for l in flines:
        #print "LIN",l,cont
        if len(l) != 3:
            continue 
        zone_id = ''
        group_id = ''
        pzone_id = ''
        pgroup_id = ''
        code_zone	= ''
        code_group	= ''
        quota = 0
        quota_qty = 0
        group  = ''
        if l[1]:
            code_zone	=	l[1].strip()
            zone_id  = zone_obj.search(cr, uid, [('code_zone','=',code_zone)])
        if l[0]:
            code_group	=	l[0].strip()
            sqlg = "SELECT id FROM product_category_salesman WHERE  name='%s'"%code_group
            #print sqlg 
            cr.execute (sqlg)
            group  = cr.fetchall()
        #print "ZONE",code_zone,"  GRP ",code_group
        if not code_zone:
            continue
        if not code_group:
            continue
        if l[2]:
            quota   = l[2].strip()
            if quota:
                quota_qty   = quota.replace('.','')
                quota_qty   = quota_qty.replace(',','.')
        if group and group[0]:
            group_id = group[0][0]
        if zone_id :
            pzone_id = parameters_zone_obj.search(cr, uid, [('zone_id','=',zone_id)])
        if zone_id and group_id:
            pgroup_id = parameters_group_obj.search(cr, uid, [('parameter_zone_id','=',pzone_id),('categ_salesman_id','=',group_id)])
        if pgroup_id:
            cont += 1
            vals = {'quota_qty':quota_qty}
            pooler.get_pool(cr.dbname).get('parameters.seller').write(cr, uid, pgroup_id, vals)
        else:
            list_fail += code_zone +'  -> '+ code_group +' \n'
    return {'lines_proc':str(cont),'fail_lines':list_fail}

class commission_sale_import_cuota_group(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : data_form, 'fields' : data_fields, 'state' : [('end', 'Cancel'),('finish', 'Siguiente', 'gtk-ok', True) ]}
		},
        'finish':{
            'actions':[_import_cuotas_group],
            'result':{'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
        },		
	}

commission_sale_import_cuota_group("commission_import_cuota_group")
