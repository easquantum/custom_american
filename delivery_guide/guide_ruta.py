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
from tools import config
import ir
import pooler
import time
from mx import DateTime

#delivery_guide_ruta-----------------------------------------------------------------------------------------------------------
# Esta tabla alamcena las rutas clasificada por almacen. Cada ruta debe especificar la tarifa para cada tipo de vehiculo   
#
class guide_ruta(osv.osv):
	_name = 'guide.ruta'
	_description = 'Ruta'	
	_columns = {
		'name': fields.char('Description', size=200, required=True),
		'code': fields.char('Codigo', size=20, required=True),	
		'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'),
		'note': fields.text('Notas'),
		'ruta_line': fields.one2many('guide.ruta.line', 'ruta_id', 'Ruta Tarifas'),
		'date_ruta': fields.date('Fecha Ruta'),
		'active' : fields.boolean('Activo'),
	}
	_defaults = {
	'active' : lambda *a: 1,
	'date_ruta': lambda *a: time.strftime('%Y-%m-%d'),
	 }
guide_ruta()
#-------------------------------------------------------------------------------------------------------------------------------------

#delivery_guide_ruta-----------------------------------------------------------------------------------------------------------
# Esta tabla alamcena las rutas clasificada por almacen. Cada ruta debe especificar la tarifa para cada tipo de vehiculo   
#
class guide_ruta_line(osv.osv):
	_name = 'guide.ruta.line'
	_description = 'Ruta linea'	
	_columns = {
		'name': fields.char('Description', size=64, required=True),
		'tipo_vehiculo_id': fields.many2one('guide.tipo.vehiculo', 'Tipo Vehiculo'),
		'ruta_id': fields.many2one('guide.ruta', 'Ruta Ref', ondelete='set null', select=True ),
		'category_fle_id': fields.many2one('product.category.fle', 'Categoria Flete'),
		'price': fields.float('Standard Price', digits=(16, int(config['price_accuracy']))),
	}
	_defaults = {	}
guide_ruta_line()

