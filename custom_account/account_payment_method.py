import netsvc
from osv import osv, fields

'''
    Payment Number significa el numero de pago, si el pago es en efectivo no deberia tener este campo,
    e.j: Numero del cheque con el que se pago.
    el numero de tarjeta de credito no se guarda completo. Solo los ultimos 4 digitos.
'''
class account_payment_method(osv.osv):
    _name = 'account.payment.method'
    _description = 'payment_method'
    _columns={
        'payment_type': fields.selection((('DP','Deposito'), ('CH','Cheque'),('EF','Efectivo'),('TR','Transferencia'),('OT','Otros'),),'Payment Method',required=True),
        'payment_number': fields.char('Payment Number', size=32),
        'amount': fields.float('Amount',required=True),
        'invoice_id': fields.many2one('account.invoice','account.invoice.id'),
        'account_id': fields.many2one('account.account','Cuenta'),
        'control_number': fields.char('Recibo Oficial', size=32),
        'ro': fields.boolean('RO'),
        'date_payment': fields.date('Payment Date'),
        'bank_id': fields.many2one('res.bank', 'Bank'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'document_number': fields.char('Documento Nro', size=32),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', readonly=True, select=True),
    }
    _defaults = {
        'ro':lambda *a: True
        }
account_payment_method()
