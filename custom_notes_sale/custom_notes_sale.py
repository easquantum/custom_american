# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007-2008 Corvus Latinoamerica (http://corvus.com.ve) All Rights Reserved.
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

import time
import tools
from osv import fields,osv,orm
import mx.DateTime
import pooler 

#------------------------------------------------------------------------
#Notas de Atencion: definen la prioridad de los pedidos y las facturas
#------------------------------------------------------------------------

class nota_atencion(osv.osv): 
	_name = 'nota.atencion'
	_description = 'Nota Atencion'	
	_columns = {
		'name': fields.char('Description', size=200, required=True),
		'code': fields.char('Code', size=8),	
	}
	_defaults = {
			
	}
nota_atencion() 