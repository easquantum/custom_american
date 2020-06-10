# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007-2009 Corvus Latinoamerica (http://corvus.com.ve) All Rights Reserved.
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
##############################################################################

from osv import fields,osv
import tools
import ir
import pooler


#guide_tipo_vehiculo---------------------------------------------------------------------------------------------------------
# Esta tabla alamcena los tipos de vehiculos, que se usaran en el transporte de productos.  
#
class guide_tipo_vehiculo(osv.osv):
	_name = 'guide.tipo.vehiculo'
	_description = 'Tipos de Vehiculo'	
	_columns = {
		'name': fields.char('Description', size=64, required=True),	
	}
	_defaults = {	}
guide_tipo_vehiculo()
#-------------------------------------------------------------------------------------------------------------------------------------


#delivery_guide_vehiculo---------------------------------------------------------------------------------------------------------
#Esta tabla alamcena los vehiculos, que se usaran en el transporte de los productos.  
#
class guide_vehiculo(osv.osv):
	_name = 'guide.vehiculo'
	_description = 'Vehiculo de Carga'	
	_columns = {
		'name': fields.char('Description', size=64, required=True),
		'active': fields.boolean('Active'),
		'serial_carroceria': fields.char('Serial Carroceria', size=64),
		'serial_motor': fields.char('Serial motor', size=64),
		'placa': fields.char('Placa', size=64),			
		'marca': fields.char('Marca', size=64),			
		'modelo': fields.char('Modelo', size=64),
		'color': fields.char('Color', size=64),
		'tipo_id': fields.many2one('guide.tipo.vehiculo', 'Tipo', required=True),
		'carrier_company_id': fields.many2one('res.partner', 'Carrier Company', required=True),
		'driver_id': fields.many2one('res.partner', 'Driver', required=True),
		'note': fields.text('Notas'),
		'weight': fields.float('Peso Bruto'),
	}
	_defaults = {
		'active': lambda *a: True,	
	}
guide_vehiculo()
#-------------------------------------------------------------------------------------------------------------------------------------
