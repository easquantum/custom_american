from report import report_sxw
from osv import osv
import pooler

class product_category_listprice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(product_category_listprice, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_products_information': self._get_produtcs_information,
            'get_partner': self._get_partner,
        })

    def _get_produtcs_information(self,partner_id):
        resp = []
        if partner_id: 
            sql = """	
            SELECT	c.id,c.name,t.name,p.variants,p.default_code,t.list_price  
            FROM       product_supplierinfo AS s
            INNER JOIN product_product      AS p ON s.product_id=p.id
            INNER JOIN product_template     AS t ON p.product_tmpl_id=t.id
            INNER JOIN group_category_rel   AS r ON s.product_id=r.product_id
            INNER JOIN product_category     AS c ON r.grp_id=c.id 	
            WHERE	s.name in ( %s )
            ORDER BY c.name,t.name;""" %partner_id
            #print sql
            self.cr.execute(sql)
            catg_id = 0
            for reg in self.cr.fetchall():
                if catg_id==reg[0]: 
                    resp.append({"codigo":reg[4],"nomb":reg[2],"ref":reg[3],"precio":reg[5]}) 
                else:
                    catg_id = reg[0]
                    resp.append({"codigo":'',"nomb":'',"ref":'',"precio":''})
                    resp.append({"codigo":'',"nomb":reg[1],"ref":'',"precio":''})
                    resp.append({"codigo":reg[4],"nomb":reg[2],"ref":reg[3],"precio":reg[5]})
            return resp

    def _get_partner(self,partner_id):
        partner = []
        if not partner_id:
            return ''
        partner	= pooler.get_pool(self.cr.dbname).get('res.partner').read(self.cr, self.uid, [partner_id],['name'])[0]
        if partner:
            nomb = partner['name']
        return nomb
		
report_sxw.report_sxw('report.product_categ_listprice','product.category','addons/custom_american/custom_product/report/product_category_listprice.rml',parser=product_category_listprice, header=False )
