import time
from report import report_sxw
from osv import osv
import pooler

class rep_par_inv_prodxloc(report_sxw.rml_parse):


	def __init__(self, cr, uid, name, context):
		super(rep_par_inv_prodxloc, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'test': self._test,
			'set_form': self._set_form,
		})	

      	def _set_form(self,form):
		# Set wizard's data form
		self.form = form

      	def _test(self):

		print "supplierid: " + str(self.form['supplierid'])
		print "warehouseid: " + str(self.form['warehouseid'])

		
		
 
		supplierid	= self.form['supplierid'] 
		warehouseid	= self.form['warehouseid']


		# Get lot' ids 
		self.cr.execute('''
		 	select 
				lot_input_id, lot_stock_id, lot_output_id
                        from 
				stock_warehouse
			where 
				id=%d 
			'''%(warehouseid))

		

		warehouse = self.cr.dictfetchone()
		
		print "dict: " + str(warehouse)

		lot_ids = str(warehouse['lot_input_id']) + ',' + str(warehouse['lot_stock_id']) + ',' + str(warehouse['lot_output_id']) 

		print "dict: " + str(warehouse)

		# Get product's ids
		self.cr.execute('''
		 	select 
				product_id
                        from 
				product_supplierinfo
			where 
				name=%d 
			'''%(supplierid))

		result = self.cr.fetchall()


		product_ids = []

		for id in result:
			product_ids.append(id[0])


#		print "product_ids: " + str(product_ids)

#		product_objs = pooler.get_pool(self.cr.dbname).get('product.product').browse(self.cr, self.uid, product_ids)
		
#		product_objs =  self.pool.get('product.product').browse(self.cr, self.uid, product_ids)
		prod_read = pooler.get_pool(self.cr.dbname).get('product.product').read(self.cr, self.uid, product_ids,['code','name','variants'])

#		print "product_objs: ",prod_read
		res = []			
		for product in prod_read:

#			print 'productant: ', product._data[product._id]['name']
#			print 'product: ', dir(product._data[product._id])
			# SUM IN
			self.cr.execute('''
				select 
					sum(product_qty) 
				from 	stock_move
				where
					location_id not in (%s) and 
				 	location_dest_id in (%d) and
					product_id=%d and
					date <= '12-31-2007' and	
					state in ('done')'''%(lot_ids,warehouse['lot_input_id'],product['id']))
			
			in_qty = self.cr.fetchone()[0]

			if in_qty == None: 
				in_qty = 0

     
			# SUM OUT
			self.cr.execute('''
				select 
					sum(product_qty) 
				from 	stock_move
				where
					location_id  in (%d) and 
				 	location_dest_id not in (%s) and
					product_id=%d and
					date <= '12-31-2007' and	
					state in ('done')'''%(warehouse['lot_output_id'],lot_ids,product['id']))
			
			out_qty = self.cr.fetchone()[0]
			
			if out_qty == None:
				out_qty = 0


			lastmonth_net = in_qty-out_qty 

			#print "Neto Diciembre: " +  str(lastmonth_net)



			# Purchased items this month
			self.cr.execute('''
				select 
					sum(product_qty) 
				from 	stock_move
				where
					location_id in (5) and 
				 	location_dest_id in (%d) and
					product_id=%d and
					date >= '01-01-2008' and
					purchase_line_id is not null and	
					state in ('done')'''%(warehouse['lot_input_id'],product['id']))
			
			po_qty = self.cr.fetchone()[0]
			
			if po_qty == None:
				po_qty = 0
				

			# Moved in items this month
			self.cr.execute('''
				select 
					sum(product_qty) 
				from 	stock_move
				where
					location_id not in (%s) and 
					location_id not in (5) and 
				 	location_dest_id in (%d) and
					product_id=%d and
					date >= '01-01-2008' and
					state in ('done')'''%(lot_ids,warehouse['lot_input_id'],product['id']))
			
			mi_qty = self.cr.fetchone()[0]
			
			if mi_qty == None:
				mi_qty = 0
				

			# Moved out items this month
			self.cr.execute('''
				select 
					sum(product_qty) 
				from 	stock_move
				where
					location_id in (%d) and 
				 	location_dest_id not in (%s,6) and
					product_id=%d and
					date >= '01-01-2008' and
					state in ('done')'''%(warehouse['lot_output_id'],lot_ids,product['id']))
			
			mo_qty = self.cr.fetchone()[0]

			print "-->> " + str(mo_qty)
			print "warehouse['lot_output_id']: %d"%(warehouse['lot_output_id'])
			print "lot_ids: %s"%(lot_ids)
			print "product_id: %d"%product['id']
			
			
			if mo_qty == None:
				mo_qty = 0
							
			# Sold items this month 
			self.cr.execute('''
				select 
					sum(product_qty) 
				from 	stock_move
				where
					location_id in (%d) and 
				 	location_dest_id in (6) and
					product_id=%d and
					date >= '01-01-2008' and
					sale_line_id is not null and	
					state in ('done')'''%(warehouse['lot_output_id'],product['id']))
			
			so_qty = self.cr.fetchone()[0]

			
			if so_qty == None:
				so_qty = 0


			# This month's returns 
			self.cr.execute('''
				select 
					sum(product_qty) 
				from 	stock_move
				where
					location_id  in (%s) and 
				 	location_dest_id in ('5') and
					product_id=%d and
					date >= '01-01-2008' and	
					state in ('done')'''%(lot_ids,product['id']))
			
			return_qty = self.cr.fetchone()[0]

			if return_qty == None:
				return_qty = 0


			total = lastmonth_net + po_qty + mi_qty - mo_qty - return_qty - so_qty
			print 'code: ',product['code']
			print 'description: ',product['name']
			print 'reference: ',product['variants']
			print 'lastmonth: ',lastmonth_net
			print 'purchases: ',po_qty
			print 'move_in: ',mi_qty
			print 'move_out: ',mo_qty
			print 'returns: ',return_qty
			print 'sales: ',so_qty
			print 'total: ',total


			loc_ids = []
			location_obj = pooler.get_pool(self.cr.dbname).get('stock.location')
			loc_ids = location_obj.search(self.cr, self.uid,[('name', '=', 'Muestreo')])
			if loc_ids:				
				location_ids = location_obj.search(self.cr, self.uid, [('location_id', 'child_of', loc_ids)])
				location_ids_str = ','.join(map(str, location_ids))
			print 'ubica hijos Muestreo: ',location_ids_str



			# Muestreo items this month
			self.cr.execute('''
				select 
					sum(product_qty) 
				from 	stock_move
				where
				 	location_dest_id in (%s) and
					product_id=%d and
					date >= '01-01-2008' and
					state in ('done')'''%(location_ids_str,product['id']))
			
			mm_qty = self.cr.fetchone()[0]
			
			if mm_qty == None:
				mm_qty = 0

			print 'muestreo: ', mm_qty



			res.append({'code':product['code'],'description':product['name'],'reference':product['variants'],'lastmonth':lastmonth_net,'purchases':po_qty,'move_in':mi_qty,'move_out':mo_qty,'returns':return_qty,'muest':mm_qty,'sales':so_qty,'total':total})
		print 'prueba3'
		for x in res:
			print str(x['code']) + "|" + str(x['description']) + "|" + str(x['reference']) + "|" + str(x['lastmonth']) + "|" + str(x['purchases']) + "|" + str(x['move_in']) + "|" + str(x['move_out']) + "|" + str(x['returns']) + "|" + str(x['muest']) + "|" + str(x['sales']) + "|" + str(x['total'])			

		return res	

	def _get_supplier(self):
		supplierid = self.form['supplierid']

		# Get result
		return [pooler.get_pool(self.cr.dbname).get('res.partner').read(self.cr, self.uid, supplierid,['name','vat'])]

report_sxw.report_sxw('report.rep_nom_inv_prodxloc','product.supplierinfo','addons/custom_american/custom_stock/report/real_products_bylocation.rml',parser=rep_par_inv_prodxloc, header=False)      
      
