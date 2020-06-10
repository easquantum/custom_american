# -*- coding: utf-8 -*-
##############################################################################
# 
#    Corvus Latinoamerica, Open Source Management Solution
#    Copyright (C) 2009 / 2012 (http://corvus.com.ve) All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#
##############################################################################

import tools
from osv import osv, fields

##account_retention_tax_configure------------------------------------------------------------------
#Esta tabla permite registrar las cuentas contables que se usaran por defecto al momento
#de realizar los comprobantes de retencion.
class account_retention_configure(osv.osv):
    _name = "account.retention.configure"
    _description = "Retention Tax Configure"
    _columns = {
        'name': fields.char('Description',size=64),       
        'account_id': fields.many2one('account.account', 'Account', required=True, domain=[('type','!=','view')]),
        'account_payable': fields.boolean('Por Pagar'), 
        'account_receivable': fields.boolean('Por Cobrar'),
     }
    _defaults = {
        'account_payable': lambda *a: 0,
        'account_receivable': lambda *a: 0,
    }
account_retention_configure() 