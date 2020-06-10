from report import report_sxw
from osv import osv
import pooler

class plan_cuentas(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(plan_cuentas, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'get_plan_cuentas': self._get_plan_cuentas,
		})
	
		
	def _get_plan_cuentas(self,tipo,todo): 
		resp = [] 
		if tipo: 
			ids_str = tipo
		else:
			todo = True
		if todo: 
				catg_ids = self.pool.get('account.account.type').search(self.cr, self.uid, [('id', '>', 0)])			
				ids_str = ','.join(map(str,catg_ids))
		sql = """	
			SELECT	t.name,c.code,c.name
			FROM		account_account_type AS t 
			INNER JOIN  account_account AS c ON t.id=c.user_type  
			WHERE	t.id in ( %s )
			ORDER BY t.name,c.code;""" %ids_str
		#print sql 
		self.cr.execute(sql)
		tipo = ''
		for reg in self.cr.fetchall():
			if tipo==reg[0]: 
				resp.append({"catg":'',"nomb":reg[2],"ref":reg[1]})
			else:
				tipo = reg[0]
				resp.append({"catg":reg[0],"nomb":reg[2],"ref":reg[1]})
		return resp  

report_sxw.report_sxw('report.plan_contable','account.account','addons/custom_american/custom_product/report/plan_contable.rml',parser=plan_cuentas, header=False )
