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

range_form = '''<?xml version="1.0"?>
<form string="Compra por Proveedor">
	<separator colspan="4" string="Informacion General"/>
	<newline/>
	<field name="supplierid" colspan="4"/>
	<newline/>
	<field name="warehouseid"/>
	<newline/>
	<separator colspan="4" string="Periodo"/>
	<newline/>
	<field name="date1"/>
	<field name="date2"/>
</form>'''


TheFields = {
	'supplierid': {'string':'Proveedor', 'type':'many2one','relation': 'res.partner', 'required':True, 'domain':[('category_id','child_of',[2])], 'size':132 },
    'warehouseid':{'string':'Almacen', 'type':'many2one','relation': 'stock.warehouse', 'required':True, 'size':110 },
	'date1': {'string':'Desde', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-01-01')},
	'date2': {'string':'Hasta', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
}


class summary_purchase_supplier(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : range_form, 'fields' : TheFields, 'state' : [('end', 'Cancel'),('report', 'Listado') ]}
		},
		'report' : {
			'actions' : [],
			'result': {'type': 'print', 'report': 'summary_purchase_suppl', 'state': 'end'}
		},
	}

# Este argumento es el nombre del wizard en account_wizard.xml
summary_purchase_supplier("summary_purchase_suppl")
