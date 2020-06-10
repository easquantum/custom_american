from report import report_sxw
from osv import osv
import pooler

class product_bycategory(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(product_bycategory, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'get_products_information': self._get_produtcs_information,
		})
	
		
	def _get_produtcs_information(self,category_id,subcateg):
		resp = []
		if category_id:
			ids_str = category_id
			if subcateg: 
				catg_ids = self.pool.get('product.category').search(self.cr, self.uid, [('parent_id', 'child_of', [category_id])])
				ids_str = ','.join(map(str,catg_ids)) 
			sql = """	
			SELECT	c.id,c.name,t.name,p.variants,p.default_code 
			FROM		product_template AS t
			INNER JOIN product_product AS p ON t.id=p.product_tmpl_id 
			INNER JOIN product_category AS c ON t.categ_id=c.id  
			WHERE	t.categ_id in ( %s )
			ORDER BY c.name,t.name;""" %ids_str
			#print sql
			self.cr.execute(sql)
			catg_id = 0
			for reg in self.cr.fetchall():
				if catg_id==reg[0]: 
					resp.append({"catg":'',"nomb":reg[4] + ' '+reg[2],"ref":reg[3]})
				else:
					catg_id = reg[0]
					resp.append({"catg":reg[1],"nomb":reg[4] + ' '+reg[2],"ref":reg[3]})
		return resp

report_sxw.report_sxw('report.product_by_category','product.category','addons/custom_american/custom_product/report/product_category.rml',parser=product_bycategory, header=False )
