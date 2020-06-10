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

import time
import locale
import wizard
import netsvc
import pooler

from osv.orm import browse_record

data_form = '''<?xml version="1.0"?>
	<form string="Listado de Promociones">
    	<separator colspan="4" string="Periodo"/>
    	<newline/>
    	<field name="date1"/>
    	<field name="date2"/>
    	<separator colspan="4" string="Tipo"/>
	    <field name="type"/>
	</form> 
'''

data_fields = {
	'date1': {'string':'Desde', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-01')},
	'date2': {'string':'Hasta', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
	'type': {'string':'Tipo:', 'type':'selection', 'required':True, 'selection':[('promocion','Promocion'),('regalo','Regalo')]},
}

class promocion_by_periodo(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':data_form, 'fields':data_fields, 'state': [('end', 'Cancelar'),('report', 'Aceptar')]}
		},

		'report': {
			'actions': [],
			'result': {'type':'print', 'report':'list_promocion', 'state': 'end'}
		},
	}

promocion_by_periodo("sale_promocion_by_periodo")