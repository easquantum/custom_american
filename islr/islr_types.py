##############################################################################
#
# Copyright (c) 2007 - 2010 Corvus Latinoamerica, C.A. (http://corvus.com.ve) All Rights Reserved
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
import tools
import netsvc
from osv import fields,osv,orm
from tools import config
import mx.DateTime
import pooler
from osv.orm import browse_record

class account_islr_tax_type(osv.osv):
    _name = "account.islr.tax.type"
    _description = "Islr Taxing type"
    _columns = {
        'name': fields.char('Name',size=64,required=True) ,
        'code': fields.char('Concept Code',size=10,required=True) ,        
        'porcentaje': fields.float('Porcentaje') ,       
        'monto_maximo': fields.float('Monto Maximo') ,       
        'sustraendo': fields.float('Sustraendo') ,             
        'unit_tributaria': fields.float('Unidades Tributarias') ,
        'factor': fields.float('Factor') ,
        'date_islr': fields.date('ISLR Date'),
        'active': fields.boolean('Activo'),
        'person_type_id': fields.many2one('account.islr.person.type','Person Types Islr', required=True),
        'account_id': fields.many2one('account.account', 'Account', domain=[('type','<>','view'), ('type', '<>', 'closed')]),
        #Campos de la estructura vieja no se usan--------------------------------------
        'porcentaje_j': fields.float('Porcentaje Juridico') ,       
        'monto_maximo_j': fields.float('Monto Maximo Juridico') ,       
        'descuento_j': fields.float('Descuento Juridico') ,       
        'porcentaje_n': fields.float('Porcentaje Natural') ,       
        'monto_maximo_n': fields.float('Monto Maximo Natural') ,       
        'descuento_n': fields.float('Descuento Natural') ,
     }
    _defaults = {
        'porcentaje': lambda *a: 0.0,
        'sustraendo': lambda *a: 0.0,
        'monto_maximo': lambda *a: 0.0,
        'date_islr': lambda *a: time.strftime('%Y-%m-%d'),
        'active': lambda *a: 1,
    }
    
    ##name_search--------------------------------------------------------------------------------------------
    #Se Sobreescibe el metodo para permitir buscar por el codigo del impuesto 
    #
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        ids = self.search(cr, user, [('code','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids = self.search(cr, user, [('code',operator,name)]+ args, limit=limit, context=context)
            ids += self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context)
        return result

    ##compute_parameters-------------------------------------------------------------------------------------
    #
    #
    def compute_parameters(self, cr, uid, ids, context={}):
        if not ids:
            return True
        sustraendo = 0
        minimo     = 0
        datos = self.pool.get('account.islr.tax.type').read(cr, uid, ids, ['unit_tributaria','factor','porcentaje'])
        if datos and datos[0]:
            if datos[0]['unit_tributaria'] and  datos[0]['factor'] and  datos[0]['porcentaje']:
                sustraendo = datos[0]['unit_tributaria'] * datos[0]['factor'] * datos[0]['porcentaje'] / 100
                minimo = datos[0]['unit_tributaria'] * datos[0]['factor']
                self.pool.get('account.islr.tax.type').write(cr, uid, ids, {'sustraendo':sustraendo,'monto_maximo':minimo  })
        return True
account_islr_tax_type()