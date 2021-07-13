from app.home import blueprint
from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from functools import reduce
from sqlalchemy import func

from app.base.models import ChartOfAccount, Partner, Project, Product, Transaction, JournalEntry
from app import db
from app.home.constant import SALES_ACCOUNT, ACCOUNT_RECEIVABLE, DEPOSITS_ON_DEMAND, NOTES_RECEIVABLE, CASH, PREPAID_EXPENSE, VAT_WITHHELD

@blueprint.route('/index')
@login_required
def index():
    return render_template('index.html', segment = 'index')

# Transactions

@blueprint.route('/transactions', methods=["GET", "POST"])
@login_required
def transaction_init():

    """ 전표 리스트 데이터 Display """

    # 1. JournalEntry, Transaction, ChartOfAccount 테이블을 join하여 계정과목별로 합산된 데이터 읽어오기
    results = db.session.query(JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)).select_from(JournalEntry).join(Transaction).join(ChartOfAccount).group_by(JournalEntry.document_number, Transaction.account_code).all()

    # 2. List Comprehension 이용해 display 항목을 구성
    documents_data = [(journal_entry.document_number, journal_entry.document_date, chart_of_account.account_name, sum_amount, journal_entry.document_description, journal_entry.user_name) for journal_entry, transaction, chart_of_account, sum_amount in results]

    """ 전표유형 선택시 해당전표 화면으로 이동 """

    if request.method == "POST":

        # form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환
        document_type = request.form['document-type']

        if document_type == 'S':
            return redirect(url_for('home_blueprint.transaction_sales'))
        else:
            return redirect(url_for('home_blueprint.transaction_sales'))

    return render_template('/transaction/transaction_init.html', segment = 'transactions', documents=documents_data)


@blueprint.route('/transactions/sales', methods=["GET", "POST"])
@login_required
def transaction_sales():

    """ 매출전표 입력양식의 리스트 항목 구성 """

    partner_items = Partner.query.filter(Partner.partner_type == "S")
    project_items = Project.query.all()
    product_items = Product.query.filter(Product.product_type == "S")

    partner_list = [(partner.partner_code, partner.partner_name) for partner in partner_items]
    project_list = [(project.project_code, project.project_name) for project in project_items]
    product_list = [(product.product_code, product.product_name, product.product_vat, product.product_cost) for product in product_items]

    if request.method == "POST":

        """ form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환 """

        sales_transactions_data = request.form

        """ Journal Entry 테이블 입력 """

        # ImmutableMultiDict으로부터 Journal Entry 데이터 추출
        document_date = sales_transactions_data.get("sales-date")
        partner = sales_transactions_data.get("sales-partner")
        project = sales_transactions_data.get("sales-project")
        payment_type = sales_transactions_data.get("sale-inlineRadioOptions")
        document_description = sales_transactions_data.get("sales-description")

        # 전표번호 자동생성
        doc_count = JournalEntry.query.filter(
            JournalEntry.document_type == "S", JournalEntry.document_date == document_date).count()
        document_number = "S-" + document_date.replace("-", "") + "-" + str(doc_count + 1)

        # Journal Entry 테이블 데이터 저장
        new_document = JournalEntry(
            document_number = document_number,
            document_type = "S",
            document_date = document_date,
            partner_code = partner,
            project_code = project,
            payment_type = payment_type,
            document_description = document_description,
            user_name = current_user.username
        )
        db.session.add(new_document)
        db.session.commit()

        """ Transaction 테이블 입력 """

        # ImmutableMultiDict으로부터 Transaction 테이블 필드를 위해 동일한 전표에 포함된 복수의 품목, 수량, 금액을 리스트로 변환
        sales_product_list = sales_transactions_data.getlist("sales-product")
        sales_quantity_list = sales_transactions_data.getlist("sales-quantity")
        sales_amount_list = sales_transactions_data.getlist("sales-amount")
        sales_vat_amount_list = sales_transactions_data.getlist("sales-vat-amount")

        # 결재유형별 계정과목 자동생성
        if payment_type == "AR":                    # 외상거래
            account = ACCOUNT_RECEIVABLE
        elif payment_type == "BT":                  # 계좌이체
            account = DEPOSITS_ON_DEMAND
        elif payment_type == "CC":                  # 신용카드
            account = NOTES_RECEIVABLE
        elif payment_type == "CA":                  # 현금
            account = CASH
        elif payment_type == "GC":                  # 상품권
            account = PREPAID_EXPENSE
        else:                                       # E-머니
            account = DEPOSITS_ON_DEMAND

        # Transaction 테이블 데이터 저장

        # 1. 매출계정 금액 계상
        new_transaction_sales = Transaction(
            document_number = document_number,
            account_code = SALES_ACCOUNT,
            transaction_amount = -sum([int(amount) for amount in sales_amount_list])
        )
        db.session.add(new_transaction_sales)
        db.session.commit()

        # 2. 지불유형별, 품목별 자산계정 금액 계상
        for i in range(len(sales_product_list)):
            new_transaction_assets = Transaction(
                document_number = document_number,
                product_code = sales_product_list[i],
                account_code = account,
                transaction_quantity= sales_quantity_list[i],
                transaction_amount= int(sales_amount_list[i]) + int(sales_vat_amount_list[i])
            )
            db.session.add(new_transaction_assets)
            db.session.commit()

        # 3. 부가세 예수금 계정 금액 계상
        new_transaction_vat = Transaction(
            document_number = document_number,
            account_code = VAT_WITHHELD,
            transaction_amount = -sum([int(amount) for amount in sales_vat_amount_list])
        )
        db.session.add(new_transaction_vat)
        db.session.commit()

        return redirect(url_for('home_blueprint.transaction_init'))

    return render_template('/transaction/transaction_sales.html', segment='transactions', partner_items=partner_list, project_items=project_list, product_items=product_list)




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
