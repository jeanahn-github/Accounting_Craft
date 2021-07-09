from app.home import blueprint
from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user

from app.base.models import Partner, Project, Product, Transaction, JournalEntry

@blueprint.route('/index')
@login_required
def index():
    return render_template('index.html', segment = 'index')

# Transactions

@blueprint.route('/transactions', methods=["GET", "POST"])
@login_required
def transactions():
    partner_items = Partner.query.all()
    project_items = Project.query.all()
    product_items = Product.query.all()

    partner_list = [(partner.partner_code, partner.partner_name) for partner in partner_items]
    project_list = [(project.project_code, project.project_name) for project in project_items]
    product_list = [(product.product_code, product.product_name, product.product_vat, product.product_cost) for product in product_items]

    if request.method == "POST":

        # form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환
        sales_transactions_data = request.form
        print(sales_transactions_data)
        #
        # # Journal Entry 테이블 필드를 위한 데이터 추출
        # date = sales_transactions_data["sales-date"]
        # partner = sales_transactions_data["sales-partner"]
        # project = sales_transactions_data["sales-project"]
        # document_type = sales_transactions_data["sale-inlineRadioOptions"]
        # description = sales_transactions_data["sales-description"]
        #
        #
        # # 전표번호 자동생성
        # doc_count = JournalEntry.query.filter(
        #     JournalEntry.document_type == form.type.data and Transaction.document_date == form.date.data).count()
        # doc_num = form.type.data + "-" + str(form.date.data) + "-" + str(doc_count + 1)
        # docunemt_number =
        #
        #
        #
        #
        #
        # # 동일한 전표에 포함된 복수의 품목과 수량을 리스트로 변환
        # sales_product_list = sales_transactions_data.getlist("sales-product")
        # sales_quantity_list = sales_transactions_data.getlist("sales-quantity")
        # sales_amount_list = sales_transactions_data.getlist("sales-amount")
        # sales_vat_amount_list = sales_transactions_data.getlist("sales-vat-amount")
        #
        #
        #
        #
        #
        # # 입력한 품목의 갯수를 이용하여 transaction 갯수를 파악
        # number_of_transactions = len(sales_product_list)
        #
        # for i in range(number_of_transactions):
        #
        #     product = sales_product_list[i]
        #     quantity = sales_quantity_list[i]
        #     amount = sales_amount_list[i]
        #     vat = sales_vat_amount_list[i]
        #
        #
        #
        #
        #
        # # transaction 테이블에 저장 위해 계정과목 자동생성
        # for i in range(len(number_of_transactions)):
        #     if sales_transaction_result[i][3] == "외상거래":
        #         account = ""  # 외상매출금
        #     elif sales_transaction_result[i][3] == "외상거래":
        #
        #
        #
        #
        # # transaction 각각의 전표데이터를 리스트로 변환
        # sales_transaction_result = [(sales_transactions_data["sales-date"], sales_transactions_data["sales-partner"],sales_transactions_data["sales-project"], sales_transactions_data["sale-inlineRadioOptions"],sales_transactions_data["sales-description"], sales_product_list[i], sales_quantity_list[i], sales_amount_list[i], sales_vat_amount_list[i]) for i in range(number_of_transactions)]
        #
        # # for i in range(number_of_transactions):
        # #     sales_date = sales_transactions_data["sales-date"]
        # #     sales_partner = sales_transactions_data["sales-partner"]
        # #     sales_project = sales_transactions_data["sales-project"]
        # #     sales_description = sales_transactions_data["sales-description"]
        # #     sales_product = sales_product_list[i]
        # #     sales_quantity = sales_quantity_list[i]
        #
        #
        #
        #




    return render_template('transactions.html', segment = 'transactions', partner_items=partner_list, project_items=project_list, product_items=product_list)






# Closing

@blueprint.route('/closing')
@login_required
def closing():
    return render_template('closing.html', segment = 'closing')

@blueprint.route('/reports/account')
@login_required
def reports_account():
    return render_template('reports/account.html', segment = 'reports_account')

@blueprint.route('/reports/partner')
@login_required
def reports_partner():
    return render_template('reports/partner.html', segment = 'reports_partner')

@blueprint.route('/reports/trial')
@login_required
def reports_trial():
    return render_template('reports/trial.html', segment = 'reports_trial')

@blueprint.route('/reports/bs')
@login_required
def reports_bs():
    return render_template('reports/bs.html', segment = 'reports_bs')

@blueprint.route('/reports/pl')
@login_required
def reports_pl():
    return render_template('reports/pl.html', segment = 'reports_pl')


# @blueprint.route('/<template>')
# @login_required
# def route_template(template):
#     try:
#         if not template.endswith('.html'):
#             template += '.html'
#
#         # Detect the current page
#         segment = get_segment(request)
#
#         # Serve the file (if exists) from app/templates/FILE.html
#         return render_template(template, segment = segment)
#
#     except TemplateNotFound:
#         return render_template('error/page-404.html'), 404
#
#     except:
#         return render_template('error/page-500.html'), 500
#
#
# # Helper - Extract current page name from request
# def get_segment(request):
#     try:
#         segment = request.path.split('/')[-1]
#         if segment == '':
#             segment = 'index'
#         return segment
#     except:
#         return None
