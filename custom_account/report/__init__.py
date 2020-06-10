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

#Reportes Gestion Financiera
import plan_contable
import report_comprobante_contable
import balance_general
import estado_resultados
import balance_comprobacion

#Reportes Compras Gestion
import report_comprobante_compra
import report_comprobante_compra_precios
import report_nota_debito
import summary_purchasebysupplier
import libro_iva_compras_gestion
import summary_purchase_supplier

#Reportes Compras Gastos Administrativos
import retenciones_gastos_admin
import retenciones_por_proveedor
import libro_compras_general
import libro_compras
import declaracion_ivaco_seniat

#Reportes Ventas
import report_factura_ventas
import report_nota_credito
import ventas_netas_nacional
import ventas_netas_zona
import libro_ventas
