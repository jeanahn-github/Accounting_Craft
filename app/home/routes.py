from app.home import blueprint
from flask import render_template, redirect, url_for, request, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import func

from app.base.models import ChartOfAccount, Partner, Project, Product, Transaction, JournalEntry, BankAccount
from app import db
from app.home.constant import SALES_ACCOUNT, ACCOUNT_RECEIVABLE, DEPOSITS_ON_DEMAND, NOTES_RECEIVABLE, CASH, PREPAID_EXPENSE, VAT_WITHHELD, INVENTORY, ACCOUNT_PAYABLE, ACCRUED_PAYABLE, PREPAID_VAT

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
    results = db.session.query(JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)).select_from(JournalEntry).join(Transaction).join(ChartOfAccount).group_by(JournalEntry.document_number, Transaction.account_code).order_by(JournalEntry.document_date.desc()).all()

    # 2. List Comprehension 이용해 display 항목을 추출
    results_list_of_tuple = [(journal_entry.document_number, journal_entry.document_date, chart_of_account.account_name, sum_amount, journal_entry.document_description, journal_entry.user_name) for journal_entry, transaction, chart_of_account, sum_amount in results]

    # 3. 전표번호를 key값으로 dic data로 변환
    documents_data = {}
    for doc_num, doc_date, account, amount, desc, user in results_list_of_tuple:
        documents_data.setdefault(doc_num, []).append((doc_date, account, amount, desc, user))

    """ 전표유형 선택시 해당전표 화면으로 이동 """

    if request.method == "POST":

        # form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환
        document_type = request.form['document-type']
        session['document_type'] = document_type

        print(document_type)

        if document_type == 'S' or document_type == 'P':
            return redirect(url_for('home_blueprint.transaction_sales_purchase'))
        elif document_type == 'D' or document_type == 'W':
            return redirect(url_for('home_blueprint.transaction_deposit_withdraw'))
        else:
            return redirect(url_for('home_blueprint.transaction_replacement'))

    return render_template('/transaction/transaction_init.html', segment = 'transactions', documents=documents_data)


@blueprint.route('/transactions/sales_purchase', methods=["GET", "POST"])
@login_required
def transaction_sales_purchase():

    """ 매출-매입전표 입력양식의 거래처와 프로젝트의 리스트 항목 구성 """

    document_type = session.get('document_type', None)

    if document_type == "S":
        partner_items = Partner.query.filter(Partner.partner_type == "S")
        project_items = Project.query.all()
        product_items = Product.query.filter(Product.product_type == "S")
    else:
        partner_items = Partner.query.filter(Partner.partner_type == "P")
        project_items = Project.query.all()
        product_items = Product.query.filter(Product.product_type == "P")

    partner_list = [(partner.partner_code, partner.partner_name) for partner in partner_items]
    project_list = [(project.project_code, project.project_name) for project in project_items]
    product_list = [(product.product_code, product.product_name, product.product_vat, product.product_cost) for product in product_items]

    if request.method == "POST":

        """ form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환 """

        transactions_data = request.form

        """ Journal Entry 테이블 입력 """

        # ImmutableMultiDict으로부터 Journal Entry 데이터 추출
        document_date = transactions_data.get("sales-purchase-date")
        partner = transactions_data.get("sales-purchase-partner")
        project = transactions_data.get("sales-purchase-project")
        payment_type = transactions_data.get("sales-purchase-inlineRadioOptions")
        document_description = transactions_data.get("sales-purchase-description")

        # 전표번호 자동생성
        doc_count = JournalEntry.query.filter(
            JournalEntry.document_type == document_type, JournalEntry.document_date == document_date).count()
        document_number = document_type + "-" + document_date.replace("-", "") + "-" + str(doc_count + 1)

        # Journal Entry 테이블 데이터 저장
        new_document = JournalEntry(
            document_number = document_number,
            document_type = document_type,
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
        sales_purchase_product_list = transactions_data.getlist("sales-purchase-product")
        sales_purchase_quantity_list = transactions_data.getlist("sales-purchase-quantity")
        sales_purchase_amount_list = transactions_data.getlist("sales-purchase-amount")
        sales_purchase_vat_amount_list = transactions_data.getlist("sales-purchase-vat-amount")

        # 결재유형별 계정과목 자동생성
        if document_type == "S":
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
        else:
            if payment_type == "AR":                    # 외상거래
                account = ACCOUNT_PAYABLE
            elif payment_type == "BT":                  # 계좌이체
                account = DEPOSITS_ON_DEMAND
            elif payment_type == "CC":                  # 신용카드
                account = ACCRUED_PAYABLE
            elif payment_type == "CA":                  # 현금
                account = CASH
            elif payment_type == "GC":                  # 상품권
                account = PREPAID_EXPENSE
            else:                                       # E-머니
                account = DEPOSITS_ON_DEMAND

        # Transaction 테이블 데이터 저장

        # 1. 매출매입계정 금액 계상
        if document_type == "S":
            new_transaction = Transaction(
                document_number = document_number,
                account_code = SALES_ACCOUNT,
                transaction_amount = -sum([int(amount) for amount in sales_purchase_amount_list])
            )
            db.session.add(new_transaction)
            db.session.commit()
        else:
            new_transaction = Transaction(
                document_number = document_number,
                account_code = INVENTORY,
                transaction_amount = sum([int(amount) for amount in sales_purchase_amount_list])
            )
            db.session.add(new_transaction)
            db.session.commit()

        # 2. 지불유형별, 품목별 자산-부채 계정 금액 계상
        for i in range(len(sales_purchase_product_list)):
            if document_type == "S":
                new_transaction = Transaction(
                    document_number = document_number,
                    product_code = sales_purchase_product_list[i],
                    account_code = account,
                    transaction_quantity= sales_purchase_quantity_list[i],
                    transaction_amount= int(sales_purchase_amount_list[i]) + int(sales_purchase_vat_amount_list[i])
                )
                db.session.add(new_transaction)
                db.session.commit()
            else:
                new_transaction = Transaction(
                    document_number = document_number,
                    product_code = sales_purchase_product_list[i],
                    account_code = account,
                    transaction_quantity = sales_purchase_quantity_list[i],
                    transaction_amount = -int(sales_purchase_amount_list[i]) - int(sales_purchase_vat_amount_list[i])
                )
                db.session.add(new_transaction)
                db.session.commit()

        # 3. 부가세 계정 금액 계상
        sum_of_vat_amount = sum([int(amount) for amount in sales_purchase_vat_amount_list])

        if document_type == "S" and sum_of_vat_amount > 0:
            new_transaction = Transaction(
                document_number = document_number,
                account_code = VAT_WITHHELD,
                transaction_amount = -sum_of_vat_amount
                # transaction_amount = -sum([int(amount) for amount in sales_purchase_vat_amount_list])
            )
            db.session.add(new_transaction)
            db.session.commit()
        elif document_type == "P" and sum_of_vat_amount > 0:
            new_transaction = Transaction(
                document_number = document_number,
                account_code = PREPAID_VAT,
                transaction_amount = sum_of_vat_amount
            )
            db.session.add(new_transaction)
            db.session.commit()

        return redirect(url_for('home_blueprint.transaction_init'))

    return render_template('/transaction/transaction_sales_purchase.html', segment='transactions', partner_items=partner_list, project_items=project_list, product_items=product_list, document_type=document_type)


@blueprint.route('/transactions/deposit_withdraw', methods=["GET", "POST"])
@login_required
def transaction_deposit_withdraw():

    """ 입금-출금전표 입력양식의 거래처, 프로젝트, 은행계좌의 리스트 항목 구성 """

    document_type = session.get('document_type', None)

    partner_items = Partner.query.all()
    project_items = Project.query.all()
    bank_accounts = BankAccount.query.all()
    coa_accounts = ChartOfAccount.query.all()

    partner_list = [(partner.partner_code, partner.partner_name) for partner in partner_items]
    project_list = [(project.project_code, project.project_name) for project in project_items]
    bank_account_list = [(bank_account.bank_account_number, bank_account.bank_account_name) for bank_account in bank_accounts]
    coa_account_list = [(coa_account.account_code, coa_account.account_name) for coa_account in coa_accounts]

    if request.method == "POST":

        """ form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환 """

        transactions_data = request.form

        # ImmutableMultiDict으로부터 데이터 추출
        document_date = transactions_data.get("deposit-withdraw-date")
        partner = transactions_data.get("deposit-withdraw-partner")
        project = transactions_data.get("deposit-withdraw-project")
        bank_account = transactions_data.get("deposit-withdraw-bank-account")
        document_description = transactions_data.get("deposit-withdraw-description")
        deposit_withdraw_coa_list = transactions_data.getlist("deposit-withdraw-coa-select")
        deposit_withdraw_amount_list = transactions_data.getlist("deposit-withdraw-amount-input")

        """ Journal Entry 테이블 입력 """

        # 전표번호 자동생성
        doc_count = JournalEntry.query.filter(
            JournalEntry.document_type == document_type, JournalEntry.document_date == document_date).count()
        document_number = document_type + "-" + document_date.replace("-", "") + "-" + str(doc_count + 1)

        print(document_number)

        # Journal Entry 테이블 데이터 저장
        new_document = JournalEntry(
            document_number = document_number,
            document_type = document_type,
            document_date = document_date,
            partner_code = partner,
            project_code = project,
            bank_account_number = bank_account,
            document_description = document_description,
            user_name = current_user.username,
        )
        db.session.add(new_document)
        db.session.commit()

        """ Transaction 테이블 입력 """

        if document_type == "D":
            new_transaction = Transaction(
                document_number = document_number,
                account_code = DEPOSITS_ON_DEMAND,
                transaction_amount = sum([int(amount) for amount in deposit_withdraw_amount_list])
            )
            db.session.add(new_transaction)
            db.session.commit()
        else:
            new_transaction = Transaction(
                document_number = document_number,
                account_code = DEPOSITS_ON_DEMAND,
                transaction_amount = -sum([int(amount) for amount in deposit_withdraw_amount_list])
            )
            db.session.add(new_transaction)
            db.session.commit()

        for i in range(len(deposit_withdraw_coa_list)):
            if document_type == "D":
                new_transaction = Transaction(
                    document_number = document_number,
                    account_code = deposit_withdraw_coa_list[i],
                    transaction_amount= -int(deposit_withdraw_amount_list[i])
                )
                db.session.add(new_transaction)
                db.session.commit()
            else:
                new_transaction = Transaction(
                    document_number = document_number,
                    account_code = deposit_withdraw_coa_list[i],
                    transaction_amount= int(deposit_withdraw_amount_list[i])
                )
                db.session.add(new_transaction)
                db.session.commit()

        return redirect(url_for('home_blueprint.transaction_init'))

    return render_template('/transaction/transaction_deposit_withdraw.html', segment = 'transactions',
                           partner_items = partner_list, project_items = project_list, bank_accounts= bank_account_list, coa_accounts=coa_account_list, document_type = document_type)




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
