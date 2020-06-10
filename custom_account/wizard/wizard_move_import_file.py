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
<form string="Importar Asientos Contables">
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
    <label colspan="4" string="Resultados obtenidos de la importacion:" align="0.0"/>
    <newline/>
    <separator colspan="4" string="Archivo Procesado Corectamente" />
    <newline/>
    <newline/>
    <newline/>
    <label colspan="4" string="a.- Nro. de Cuentas Procesadas:" align="0.0"/>
	<newline/>
	<field name="lines_proc"/>
	<newline/>
	<newline/>
	<newline/>
	<label colspan="4" string="b.- Cuentas NO Procesadas:" align="0.0"/>
	<newline/>
	<newline/>
	<field  colspan="4" name="fail_acc"  nolabel="1"/>
	<newline/>
</form>''' 

_result_fields = {
	'lines_proc': {'string': 'Lineas Procesada','type': 'char','readonly': True},
	'fail_acc': {'string': 'Cuantas','type': 'text','readonly': True, 'size':100},
} 

def _import_account_move_file(self, cr, uid, data, context):
    cont = 0
    ruta = '/home/public/'
    ruta	= "/opt/openerp/reportes/personal/nomina/" # Ruta Server Produccion  
    file_data = data['form']['fdata']
    nf        = data['form']['fname']
    file_name = ruta + data['form']['fname']
    move_id = data['id']
    nomb= nf.split('.')
    if not move_id:
        raise wizard.except_wizard(_('Error !'), _('Debe pulsar el Boton Guardar, antes de procesar el archivo..!') )
    move_obj =  pooler.get_pool(cr.dbname).get('account.move')
    move_data = move_obj.browse(cr, uid, move_id)
    periodo   = move_data.period_id.id
    fecha     = move_data.date
    diario    = move_data.journal_id.id
    ref       = move_data.ref

    #Validaciones----------------------------------------------------------------------------------
    if nomb[1].lower() != 'csv':
        raise wizard.except_wizard(_('Error !'), _('El Archivo no es de tipo CSV, consulte al administrador ') )
    if os.path.exists(file_name):
        raise wizard.except_wizard(_('Error !'), _('El Archivo ya EXISTE por lo tanto no puede ser procesado') )


    #Procesando el Archivo-------------------------------------------------------------------------
    val =base64.decodestring(file_data)
    lines = val.split("\n")
    flines = map( lambda x: x.split(';'), lines )
    list_fail_acc = ''
    for l in flines:
        #print "LIN",l
        acc_id    = ''
        name_desc =''
        haber     = 0
        debe      = 0
        if not l[0]:
            continue
        cta_nro	=	l[0].strip()
        sql = "SELECT id,code,type FROM account_account WHERE code='%s' "%cta_nro
        #print "SQL",sql
        cr.execute (sql)
        result = cr.fetchall()
        #
        if l[1]:
            name_desc = l[1].strip()

        if not result:
            cod = cta_nro.split(".")
            if len(cod) == 6:
                list_fail_acc += cta_nro + ' \n' 
            continue
        if result and result[0]:
            cont += 1
            if result[0][2]=='view':
                list_fail_acc += cta_nro + ' (Vista) \n'
                continue
            acc_id = result[0][0]
        if l[2]:
            debit_debe   = l[2].strip()
            if debit_debe:
                debit_debe   = debit_debe.replace('.','')
                debit_debe   = debit_debe.replace(',','.')
                debe   = float(debit_debe)
        if l[3]:
            credit_haber = l[3].strip()
            if credit_haber:                
                credit_haber = credit_haber.replace('.','')
                credit_haber = credit_haber.replace(',','.')
                haber        = float(credit_haber)
        vals ={
        'move_id':move_id,
        'journal_id':diario,
        'period_id':periodo,
        'account_id':acc_id,
        'partner_id':1,
        'name': name_desc,
        'ref': ref,
        'date':fecha,
        'date_created':fecha,
        'credit':haber,
        'debit':debe,
        'state':'draft',
        'centralisation':'normal',
        'blocked':False
        }
        line_ids = pooler.get_pool(cr.dbname).get('account.move.line').create(cr, uid,vals)

    #Se guarda el Arvhivo procesado----------------------------------------------------------------
    output		= open(file_name,"w")
    output.write(val)
    output.close()
    move_obj.write(cr,uid, [move_id], {'file_name':nomb[0]},context)

    return {'lines_proc':str(cont),'fail_acc':list_fail_acc}

class account_move_import_file(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : data_form, 'fields' : data_fields, 'state' : [('end', 'Cancel'),('finish', 'Siguiente', 'gtk-ok', True) ]}
		},
        'finish':{
            'actions':[_import_account_move_file],
            'result':{'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
        },		
	}

account_move_import_file("move_import_file")
