from report import report_sxw
from osv import osv
import pooler

class product_bycategory_commissions(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(product_bycategory_commissions, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_products_information': self._get_produtcs_information,
        })

    def _get_produtcs_information(self,category_id,allcateg):
        resp = []
        if category_id:
	        condiction = 'categ_salesman_id ='+str(category_id)
        else:
            condiction = 'categ_salesman_id != 0'
        sql = """	
        SELECT	c.id,c.name,t.name,p.variants,p.default_code 
        FROM		product_product AS p
        INNER JOIN  product_template AS t ON p.product_tmpl_id=t.id 
        INNER JOIN product_category_salesman AS c ON p.categ_salesman_id=c.id  
        WHERE	 %s 
        ORDER BY c.name,t.name;""" %condiction
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

report_sxw.report_sxw('report.product_categ_commissions','product.category.salesman','addons/custom_american/custom_product/report/product_category_commissions.rml',parser=product_bycategory_commissions, header=False )
