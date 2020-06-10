##############################################################################
#
# Copyright (c) 2007 Corvus Latinoamerica
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

datos_form = '''<?xml version="1.0"?>
<form string="Balance General">
    <separator colspan="4" string="Informacion Fiscal"/>
	<newline/>
	<field name="acc_id"/>
	<field name="num_level"/>
	<separator colspan="4" string="Periodo"/>
	<newline/>
	<field name="date1"/>
	<field name="date2"/>
</form>'''


datos_fields = {
    'acc_id': {'string': 'Cuenta', 'type': 'many2one', 'relation':'account.account', 'required':True},
    'num_level': {'string':'Nivel:', 'type':'selection', 'required':True, 'selection':[('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6')]},
	'date1': {'string':'Desde', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-01')},
	'date2': {'string':'Hasta', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},	
}


def _validate_form(self, cr, uid, data, context):
    nivel = 0
    acc_id    = data['form']['acc_id']
    num_level    = int(data['form']['num_level'])
    account		= pooler.get_pool(cr.dbname).get('account.account').read(cr, uid, [acc_id],['code'])[0]
    code = account['code'].split('.')
    if int(code[0]):
        nivel = 1
    if int(code[1]):
        nivel = 2
    if int(code[2]):
        nivel = 3
    if int(code[3]):
        nivel = 4
    if int(code[4]):
        nivel = 5
    if int(code[5]):
        nivel = 6
    if num_level != nivel:
        msg = 'La cuenta es nivel %d y el nivel seleccionado es:  %d . Debe estar en el mismo nivel'%(nivel,num_level)
        raise wizard.except_wizard(_('Alerta !'), _(msg) )
    return {}

class balance_general(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : datos_form, 'fields' : datos_fields, 'state' : [('end', 'Cancel'),('report', 'Listado') ]}
		},
		'report' : {
			'actions' : [_validate_form],
			'result': {'type': 'print', 'report': 'balance_general', 'state': 'end'}
		},
	}

balance_general("balance_general")
