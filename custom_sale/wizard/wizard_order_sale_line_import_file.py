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
import locale
import wizard
import netsvc
import pooler
import tools
from osv.orm import browse_record
import base64
import os.path

#Formulario del Wizard - Datos Entrada------------------------------------------------------------------------------------------------
data_form = '''<?xml version="1.0"?>
<form string="Importar Pedido de Ventas">
	<separator colspan="2" string="Seleccione al archivo"/>
	<newline/>
	<field name="fdata"/>
	<newline/>
	<field name="fname"/>
</form>'''

data_fields = {
	'fdata': {'string':'Archivo', 'type':'binary', 'filename':'fname','required':True },
	'fname': {'string':'Descripcion', 'type':'char',  'size':90 },
}


#Formulario del Wizard - Datos Salida-------------------------------------------------------------------------------------------------
_result_form = '''<?xml version="1.0"?>
<form string="Informacion">
    <label colspan="4" string="Resultados obtenidos de la importacion:" align="0.0"/>
    <newline/>
    <separator colspan="4" string="Archivo Procesado Corectamente" />
    <newline/>
    <newline/>
    <newline/>
    <label colspan="4" string="a.- Lineas de Productos Procesados:" align="0.0"/>
	<newline/>
	<field name="lines_proc"/>
	<newline/>
	<newline/>
	<newline/>
	<label colspan="4" string="b.- Codigos EAN No Registrados:" align="0.0"/>
	<newline/>
	<newline/>
	<field  colspan="4" name="fail_lines"  nolabel="1"/>
	<newline/>
</form>''' 

_result_fields = {
	'lines_proc': {'string': 'Lineas Procesada','type': 'char','readonly': True},
	'fail_lines': {'string': 'Lineas No Procesada','type': 'text','readonly': True, 'size':100},
} 

def _order_import_file(self, cr, uid, data, context):
    cont = 0
    ruta = '/home/public/' 
    file_data = data['form']['fdata']
    nf        = data['form']['fname']
    file_name = ruta + data['form']['fname']
    order_id = data['id']
    #Objetos Requeridos
    sale_obj      = pooler.get_pool(cr.dbname).get('sale.order')
    sale_line_obj = pooler.get_pool(cr.dbname).get('sale.order.line')
    #Procesando el Pedido
    order = sale_obj.browse(cr, uid, order_id)
    if not order_id:
        raise wizard.except_wizard(_('Error !'), _('Debe pulsar el Boton Guardar, antes de procesar el archivo..!') )
    
    #Lista de precios
    pricelist   = order.pricelist_id.id or order.partner_id.property_product_pricelist.id
    if not pricelist:
        raise wizard.except_wizard(_('Error !'), _('El Cliente debe tener asignada una lista de precios...!') )
    pricelist_vers = 0
    pricelist_item = 0
    sql = """
    SELECT pi.id
    FROM product_pricelist               AS pl
    INNER JOIN product_pricelist_version AS pv ON pl.id=pv.pricelist_id
    INNER JOIN product_pricelist_item    AS pi ON pv.id=pi.price_version_id
    WHERE pl.id=%s
    """%pricelist
    cr.execute (sql)
    prlist = cr.fetchall()
    if prlist and prlist[0]:
        pricelist_item = prlist[0][0] 
    #Terminos de Pago
    payment_term = order.payment_term.id
    sql = """
    SELECT t.tax_id,p.name
    FROM       account_payment_term    AS p
    INNER JOIN account_payment_tax_rel AS t ON p.id=t.paymenterm_id
    WHERE p.id=%s
    """%payment_term
    cr.execute (sql)
    payment_term_list = cr.fetchall()
    #Procesando el Archivo
    val =base64.decodestring(file_data)
    lines = val.split("\n")
    flines = map( lambda x: x.split(','), lines )
    list_fail_prod = ''
    order_num      = ''
    for l in flines:
        code_ean     = ''
        product      = []
        tax_ids      = []
        name_desc    = ''
        qty          = 0
        uom          = 0        
        price        = 0
        price_standard = 0
        if not l[0]:
            continue
        #print "SQL",sql #cr.execute (sql)  #result = cr.fetchall() #name_desc = l[1].strip()
        if l[0] and l[0]=='E' and l[1]:
            order_num = l[1]
        if l[0] and l[0]=='D' and l[1]:
            code_ean = l[1].strip()
            #Se obtiene la informacion del Producto
            sql = """
            SELECT p.id,p.default_code,t.name,t.list_price,t.uom_id 
            FROM product_product AS p
            INNER JOIN product_template AS t ON p.product_tmpl_id=t.id
            WHERE ean13='%s' 
            """%code_ean
            #print "SQL",sql
            cr.execute (sql)
            product = cr.fetchall()
            if product and product[0]:
                product_id     = product[0][0]
                name_desc      = '[' + product[0][1] + '] ' + product[0][2]
                price_standard = product[0][3]
                uom            = product[0][4]
                #Se obtiene los Impuestos asignados al Producto
                sql = """
                SELECT tax_id 
                FROM product_taxes_rel 
                WHERE prod_id=%d 
                """%product_id
                #print "SQL",sql
                cr.execute (sql)
                tax_rel = cr.fetchall()
                if tax_rel and tax_rel[0]:
                    for t in tax_rel:
                        tax_ids.append(t[0])
                if payment_term_list and payment_term_list[0]:
                    for p in payment_term_list:
                        tax_ids.append(p[0])
                cont += 1
                qty_unit = 0
                cajas    = 0
                unidades = 0
                if l[7]:
                    price = float(l[7])
                if l[4]:
                    cajas    =  float(l[4])
                    qty      =  float(l[4])
                if l[13]:
                    unidad =  l[13]
                    unidad =  unidad.strip()
                    if unidad:
                        unidades =  float(unidad)
                if unidades and cajas!=unidades:
                    qty_unit = unidades/cajas
                    price = price * qty_unit
                    #print "CAJAS=",cajas," UNID=",unidades,"UXC=",qty_unit," P =",price
                line_id = sale_line_obj.create(cr, uid,{'order_id':order_id,'product_uos_qty': qty,'price_standard':price_standard,'pricelist_item_id': pricelist_item,'name': name_desc, 'product_uom': uom,'price_unit': price,'product_uom_qty': qty,'delay': 7.0,'discount': False,'tax_id': [(6, 0, tax_ids)],'product_uos': False,'product_packaging': False,'address_allotment_id': False,'type': u'make_to_stock', 'product_id': product_id})
            else:
                list_fail_prod += l[2] + ' \n'
    if order_num:
        order_num = 'O/C:'+order_num
        ord_sale  = sale_obj.write(cr,uid, [order_id], {'nota_atencion':order_num},context)
    #Se guarda el Arvhivo procesado---------------------------------------------------------------- 
    #output		= open(file_name,"w")
    #output.write(val)
    #output.close()
    return {'lines_proc':str(cont),'fail_lines':list_fail_prod}

class order_sale_line_import_file(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : data_form, 'fields' : data_fields, 'state' : [('end', 'Cancel'),('finish', 'Siguiente', 'gtk-ok', True) ]}
		},
        'finish':{
            'actions':[_order_import_file],
            'result':{'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
        },		
	}

order_sale_line_import_file("order_sale_line_from_file")
