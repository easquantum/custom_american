{
	"name" : "Custom American Distribution",
	"version" : "1.0",
	"author" : "Team Corvus",
	"website" : "http://corvus.com.ve/",
	"category" : "Generic Modules/Base",
	"description": "Customs - American Distibution.",
	"depends" : ["base","product","account","stock","purchase","sale"],
	"init_xml" : [
	#CUSTOM SEQUENCE
		'delivery_guide/guide_sequence.xml',
		'credit_collection/liquidation_sequence.xml',
		'custom_stock/custom_stock_sequence.xml',
		'retention/custom_invoice_retention_sequence.xml',
		'islr/retention_islr_sequence.xml',
		'custom_account/custom_facturas_ventas_sequence.xml',
                'custom_account/custom_notas_debito_sequence.xml',
                'custom_account/custom_notas_debito_ajust_sequence.xml',
                'custom_account/custom_notas_debito_check_sequence.xml',
                'custom_account/custom_notas_debito_prov_sequence.xml',
                'custom_account/custom_notas_credito_ajust_sequence.xml',
                'promociones/sale_promociones_sequence.xml',
                'promociones/sale_regalos_sequence.xml',
	],
	"demo_xml" : [	],
	"update_xml" : [
		#PARTNER
		"custom_partner/partner_state_city_view.xml", 
		"custom_partner/partner_suppliers_view.xml",
		"custom_partner/partner_zone_view.xml",
		"custom_partner/partner_type_view.xml",    
		"custom_partner/partner_customer_view.xml",
		"custom_partner/partner_curriers_view.xml",
                "custom_partner/parameters_seller_zone_view.xml",
		"custom_partner/partner_salesman_view.xml",
                "custom_partner/deductions_seller_view.xml",
		"custom_partner/custom_partner_report.xml", 
		"custom_partner/custom_partner_wizard.xml", 

		#PRINTER
		"custom_printer/printer_view.xml",
			
		#PRODUCT
		"custom_product/custom_product_view.xml",
		"custom_product/custom_product_fletes_view.xml",
		"custom_product/custom_product_promocion_view.xml",
		"custom_product/custom_product_wizard.xml",
		"custom_product/custom_product_report.xml",
	
		#ACCOUNT
		#vistas - Compras
		"custom_account/custom_invoice_supplier_sup_view.xml",
		"custom_account/custom_invoice_supplier_opr_view.xml",
		"custom_account/custom_invoice_supplier_gadm_view.xml",
		"custom_account/custom_invoice_supplier_refund_view.xml",
		"custom_account/custom_invoice_supplier_gadm_refund_view.xml",
		"custom_account/custom_invoice_supplier_refund_esp_view.xml",
		"custom_account/account_view.xml",
		#vistas - Ventas
		"custom_account/custom_invoice_customer_sup_view.xml",		
		"custom_account/custom_invoice_customer_opr_view.xml",		
		"custom_account/custom_invoice_customer_refund_view.xml",		
		"custom_account/custom_payment_term_view.xml",		
		"custom_account/account_retention_types_view.xml",		
		#Gestion Financiera
		"custom_account/account_payment_method_view.xml",
		"custom_account/custom_account_move_view.xml",
		"custom_account/custom_account_move_import_file_view.xml",
		#reporte - wizard
		"custom_account/custom_account_report.xml",
		"custom_account/custom_account_wizard.xml",
		"custom_account/custom_invoice_workflow.xml",

		#STOCK
		"custom_stock/custom_product_view.xml",
		"custom_stock/custom_stock_picking_in.xml",
		"custom_stock/custom_stock_picking_in_dev.xml",
		"custom_stock/custom_stock_picking_trasp_in.xml",
		"custom_stock/custom_stock_picking_trasp_out.xml",
		"custom_stock/custom_stock_picking_trans_in.xml",
		"custom_stock/custom_stock_picking_trans_out.xml",
		"custom_stock/custom_stock_picking_mues.xml",
		"custom_stock/custom_stock_picking_out_aju.xml",
		"custom_stock/custom_stock_picking_out.xml",
		"custom_stock/custom_stock_picking_in_aju.xml",
		"custom_stock/custom_stock_inventory_view.xml",
		"custom_stock/custom_stock_inventory_sup_view.xml",
		"custom_stock/custom_stock_inventory_open_view.xml",
		"custom_stock/custom_stock_picking_lost.xml",
		#reporte - wizard
		"custom_stock/custom_stock_report.xml",
		"custom_stock/custom_stock_wizard.xml",
		
	
		#PURCHASE
		"custom_purchase/custom_purchase_view.xml",
		"custom_purchase/custom_stock_picking_comp_view.xml",
		"custom_purchase/custom_purchase_report.xml",
		"custom_purchase/custom_stock_picking_trasp_out.xml",
		"custom_purchase/custom_stock_picking_mues.xml",
		"custom_purchase/custom_stock_picking_trans_in.xml",
		"custom_purchase/custom_stock_picking_trans_out.xml",
		"custom_purchase/custom_stock_picking_ajust_out.xml",


		#SALE
		"custom_sale/custom_sale_view.xml",
		"custom_sale/custom_sale_workflow.xml",
		"custom_sale/custom_stock_picking_ventas_view.xml",
		"custom_sale/commissions_seller_view.xml",
		"custom_sale/commissions_seller_invoice_view.xml",
                "custom_sale/commissions_collection_seller_view.xml",
                "custom_sale/commissions_collection_v2_view.xml",
		"custom_sale/custom_sale_report.xml",
		"custom_sale/custom_sale_wizard.xml",
		"custom_sale/commissions_period_view.xml",

		#NOTES SALE
		"custom_notes_sale/notes_sale_view.xml",
		
		#DELIVERY GUIDE
		"delivery_guide/guide_vehiculo_view.xml",
		"delivery_guide/product_category_fle_view.xml",
		"delivery_guide/guide_ruta_view.xml",
		"delivery_guide/guide_view.xml",
		"delivery_guide/guide_workflow.xml",
		"delivery_guide/guide_report.xml",
		"delivery_guide/guide_wizard.xml",

		#CREDIT COLLECTION
		"credit_collection/liquidation_view.xml", 		
		"credit_collection/credit_collection_report.xml",
		"credit_collection/liquidation_workflow.xml",
		"credit_collection/concept_invoice_customer_refund_view.xml",
		"credit_collection/custom_invoice_refund_credit_view.xml",
		"credit_collection/custom_invoice_refund_credit_manual_view.xml",
                "credit_collection/custom_invoice_refund_credit_out_aj_view.xml",
                "credit_collection/custom_invoice_refund_credit_in_view.xml",
                "credit_collection/custom_invoice_refund_credit_in_aj_view.xml",
                "credit_collection/custom_invoice_refund_credit_in_ch_view.xml",

		#PERIOD
		"period/period_wizard.xml",
		"period/period_view.xml", 		
		
		#RETENTION
		'retention/retention_workflow.xml',
		"retention/retention_configure_view.xml",
		"retention/retention_view.xml",
		"retention/retention_client_view.xml",
		"retention/retention_report.xml",

		#RETENTION ISLR
		"islr/islr_person_types_view.xml",
		"islr/islr_types_view.xml",
		"islr/islr_view.xml",
		"islr/islr_workflow.xml",
		"islr/islr_report.xml",
		"islr/islr_wizard.xml",

		#SECURITY
        	"security/custom_product/cust_product_security.xml",
	        'security/custom_product/ir.model.access.csv',
        	"security/custom_stock/cust_stock_security_group.xml",
        	"security/custom_stock/cust_stock_security_menu.xml",
	        'security/custom_stock/ir.model.access.csv',

		#PROMOCIONES
		"promociones/conceptos_promociones.xml",
		"promociones/sale_promociones.xml",
		"promociones/sale_regalos.xml",
		"promociones/sale_promociones_workflow.xml",
		"promociones/sale_promociones_wizard.xml",
		"promociones/sale_promociones_report.xml",

	],
	"active": False,
	"installable": True,
}

