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

#import wizard_refund
#WIZARD: GESTION FINANCIERA
import wizard_plan_contable
import wizard_move_import_file
import wizard_balance_general
import wizard_estado_resultados
import wizard_balance_comprobacion

#WIZARD: Compras de Gestion
import wizard_summary_purchasebysupplier
import wizard_libro_iva_compras_gestion 
import wizard_summary_purchase_supplier

#WIZARD: Compras de Gastos Administrativos
import wizard_retenciones_gastos_admin
import wizard_retenciones_por_proveedor
import wizard_declaracion_ivaco_seniat
import wizard_libro_compras_general
import wizard_libro_compras

#WIZARD: VENTAS
import wizard_invoice_print 
import wizard_customer_refund_print
import wizard_customer_invoice_esp_print
import wizard_ventas_netas_nacional
import wizard_ventas_netas_zona
import wizard_libro_ventas
import wizard_set_retention_customer
import wizard_customer_refund_internal_print
import wizard_customer_refund_manual_print

#WIZARD: PAGO EN COMPRA Y VENTAS
import wizard_pay_invoice
import wizard_recovery_invoice
import wizard_reconcile_select_credit
