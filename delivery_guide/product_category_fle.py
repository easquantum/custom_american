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

#product_category_fle---------------------------------------------------------------------------------------------------------
#Esta tabla alamcena las categoarias que agrupan a los productos, para establecer la tarifa del flete.  
#
class product_category_fle(osv.osv):
	_name = 'product.category.fle'
	_description = 'Categoria product fletes'	
	_columns = {
		'name': fields.char('Description', size=64, required=True),
		'code': fields.char('Code', size=64),
	}
	_defaults = {
			
	}
product_category_fle()
#---------------------------------------------------------------------------------------------------------------------------------


#product_category_fle---------------------------------------------------------------------------------------------------------
#Se agrega el campo 'id_flete' a la tabla de productos  
#
class product_product(osv.osv):
	_inherit = 'product.product'
	_columns = {
		'id_flete': fields.many2one('product.category.fle', 'Categoria Flete'),
	}
product_product()
#---------------------------------------------------------------------------------------------------------------------------------
