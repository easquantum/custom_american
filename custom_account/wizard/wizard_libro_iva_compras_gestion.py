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
import wizard
import netsvc
import pooler
from osv.orm import browse_record

dat_form = '''<?xml version="1.0"?>
<form string="Libro Especial IVA Compras">
	<separator colspan="2" string="Fecha"/>
	<newline/>
	<field name="date1"/>
	<field name="date2"/>
</form>''' 


dat_fields = {
	'date1': {'string':'Desde', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-01-01')},
	'date2': {'string':'Hasta', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
}


class libro_iva_compras(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : dat_form, 'fields' : dat_fields, 'state' : [('end', 'Cancel'),('report', 'Listado') ]}
		},
		'report' : {
			'actions' : [],
			'result': {'type': 'print', 'report': 'libro_iva_compras_gestion', 'state': 'end'}
		},
	}

libro_iva_compras("libro_iva_compras_gestion") 
