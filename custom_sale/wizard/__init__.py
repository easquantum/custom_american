# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Corvus Latinoamerica, C.A. 
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

#Comisiones de Ventas Order
import wizard_commissions_calculated_zone
import wizard_commissions_calculated_territory
import wizard_commissions_calculated_division

#Comisiones de Ventas Invoice
import wizard_commissions_invoice_cal_zone
import wizard_commissions_invoice_cal_territory
import wizard_commissions_invoice_cal_division

#Import files
import wizard_commissions_sale_import_cuota
import wizard_commissions_sale_import_cuota_group

#Comisiones Cobranza
import wizard_commissions_collection_calculated

#Archivo comisiones Banco
import wizard_commissions_file
import wizard_commissions_collection_file

#Comisiones Cobranza 2015
import wizard_commissions_collection_cal_zone
import wizard_commissions_collection_cal_territory
import wizard_commissions_collection_cal_division

#Commission Periodos
import wizard_commissions_make_period
import wizard_commissions_year_close
import wizard_commissions_period_close

#Importar Archivos de Pedidos
import wizard_order_sale_line_import_file
