from app.home import blueprint
from flask import render_template, redirect, url_for, request, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_
from calendar import _monthlen

from app.base.models import ChartOfAccount, Partner, Project, Product, Transaction, JournalEntry, BankAccount
from app import db
from app.home.constant import SALES_ACCOUNT_GOOD, SALES_ACCOUNT_PRODUCT, ACCOUNT_RECEIVABLE, DEPOSITS_ON_DEMAND, \
    NOTES_RECEIVABLE, CASH, PREPAID_EXPENSE, VAT_WITHHELD, INVENTORY_GOOD, INVENTORY_PRODUCT, INVENTORY_MATERIAL, \
    ACCOUNT_PAYABLE, ACCRUED_PAYABLE, PREPAID_VAT


@blueprint.route('/index')
@login_required
def index():
    return render_template('index.html', segment = 'index')


"""
Transactions
"""


@blueprint.route('/transactions', methods = ["GET", "POST"])
@login_required
def transaction_init():

    """ 전표 리스트 데이터 Display """

    # 1. JournalEntry, Transaction, ChartOfAccount 테이블을 join하여 계정과목별로 합산된 데이터 읽어오기
    results = db.session.query(JournalEntry, Transaction, ChartOfAccount,
                               func.sum(Transaction.transaction_amount)).select_from(JournalEntry).join(
        Transaction).join(ChartOfAccount).group_by(JournalEntry.document_number, Transaction.account_code).order_by(
        JournalEntry.document_date.desc()).all()

    # 2. List Comprehension 이용해 display 항목을 추출
    results_list_of_tuple = [(journal_entry.document_number, journal_entry.document_date, chart_of_account.account_name,
                              sum_amount, journal_entry.document_description, journal_entry.user_name) for
                             journal_entry, transaction, chart_of_account, sum_amount in results]

    # 3. 전표번호를 key값으로 dic data로 변환
    documents_data = {}
    for doc_num, doc_date, account, amount, desc, user in results_list_of_tuple:
        documents_data.setdefault(doc_num, []).append((doc_date, account, amount, desc, user))

    """ 전표유형 선택시 해당전표 화면으로 이동 """

    if request.method == "POST":

        # form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환
        document_type = request.form['document-type']
        session['document_type'] = document_type

        if document_type == 'SA' or document_type == 'PU':
            return redirect(url_for('home_blueprint.transaction_sales_purchase'))
        elif document_type == 'DE' or document_type == 'WI':
            return redirect(url_for('home_blueprint.transaction_deposit_withdraw'))
        else:
            return redirect(url_for('home_blueprint.transaction_replacement'))

    return render_template('/transaction/transaction_init.html', segment = 'transactions', documents = documents_data)


@blueprint.route('/transactions/sales_purchase', methods = ["GET", "POST"])
@login_required
def transaction_sales_purchase():

    """ 매출-매입전표 입력양식의 거래처와 프로젝트의 리스트 항목 구성 """

    document_type = session.get('document_type', None)

    if document_type == "SA":
        partner_items = Partner.query.filter(Partner.partner_type == "S")
        project_items = Project.query.all()
        product_items = Product.query.filter(or_(Product.product_type == "SS", Product.product_type == "SP"))
    else:
        partner_items = Partner.query.filter(Partner.partner_type == "P")
        project_items = Project.query.all()
        product_items = Product.query.filter(or_(Product.product_type == "PP", Product.product_type == "SP"))

    partner_list = [(partner.partner_code, partner.partner_name) for partner in partner_items]
    project_list = [(project.project_code, project.project_name) for project in project_items]
    product_list = [
        (product.product_code, product.product_name, product.product_vat, product.product_cost, product.product_price)
        for product in product_items]

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
        sales_purchase_item_list = transactions_data.getlist("sales-purchase-product")
        sales_purchase_quantity_list = transactions_data.getlist("sales-purchase-quantity")
        sales_purchase_amount_list = transactions_data.getlist("sales-purchase-amount")
        sales_purchase_vat_amount_list = transactions_data.getlist("sales-purchase-vat-amount")

        # 결재유형별 계정과목 자동생성
        if document_type == "SA":
            if payment_type == "AR":  # 외상거래
                account = ACCOUNT_RECEIVABLE
            elif payment_type == "BT":  # 계좌이체
                account = DEPOSITS_ON_DEMAND
            elif payment_type == "CC":  # 신용카드
                account = NOTES_RECEIVABLE
            elif payment_type == "CA":  # 현금
                account = CASH
            elif payment_type == "GC":  # 상품권
                account = PREPAID_EXPENSE
            else:  # E-머니
                account = DEPOSITS_ON_DEMAND
        else:
            if payment_type == "AR":  # 외상거래
                account = ACCOUNT_PAYABLE
            elif payment_type == "BT":  # 계좌이체
                account = DEPOSITS_ON_DEMAND
            elif payment_type == "CC":  # 신용카드
                account = ACCRUED_PAYABLE
            elif payment_type == "CA":  # 현금
                account = CASH
            elif payment_type == "GC":  # 상품권
                account = PREPAID_EXPENSE
            else:  # E-머니
                account = DEPOSITS_ON_DEMAND

        # Transaction 테이블 데이터 저장
        for i in range(len(sales_purchase_item_list)):
            # TODO: product_code 하드코딩 개선 필요

            # 매출전표
            if document_type == "SA":

                # 1. 매출계정 금액 계상
                if int(sales_purchase_item_list[i]) < 20000:
                    new_transaction = Transaction(
                        document_number = document_number,
                        product_code = sales_purchase_item_list[i],
                        account_code = SALES_ACCOUNT_PRODUCT,
                        transaction_quantity = sales_purchase_quantity_list[i],
                        transaction_amount = -int(sales_purchase_amount_list[i])
                        # transaction_amount = -sum([int(amount) for amount in sales_purchase_amount_list])
                    )
                    db.session.add(new_transaction)
                    db.session.commit()

                if int(sales_purchase_item_list[i]) >= 20000:
                    new_transaction = Transaction(
                        document_number = document_number,
                        product_code = sales_purchase_item_list[i],
                        account_code = SALES_ACCOUNT_GOOD,
                        transaction_quantity = sales_purchase_quantity_list[i],
                        transaction_amount = -int(sales_purchase_amount_list[i])
                        # transaction_amount = -sum([int(amount) for amount in sales_purchase_amount_list])
                    )
                    db.session.add(new_transaction)
                    db.session.commit()

                # 2. 지불유형별, 품목별 자산 계정 금액 계상
                new_transaction = Transaction(
                    document_number = document_number,
                    product_code = sales_purchase_item_list[i],
                    account_code = account,
                    transaction_quantity = sales_purchase_quantity_list[i],
                    transaction_amount = int(sales_purchase_amount_list[i]) + int(sales_purchase_vat_amount_list[i])
                )
                db.session.add(new_transaction)
                db.session.commit()

                # 3. 부가세 계정 금액 계상
                if int(sales_purchase_vat_amount_list[i]) != 0:
                    new_transaction = Transaction(
                        document_number = document_number,
                        product_code = sales_purchase_item_list[i],
                        account_code = VAT_WITHHELD,
                        transaction_quantity = sales_purchase_quantity_list[i],
                        transaction_amount = -int(sales_purchase_vat_amount_list[i])
                    )
                    db.session.add(new_transaction)
                    db.session.commit()

            # 매입전표
            else:

                # 1. 매입계정 금액 계상
                if 20000 <= int(sales_purchase_item_list[i]) < 30000:
                    new_transaction = Transaction(
                        document_number = document_number,
                        product_code = sales_purchase_item_list[i],
                        account_code = INVENTORY_GOOD,
                        transaction_quantity = sales_purchase_quantity_list[i],
                        transaction_amount = int(sales_purchase_amount_list[i])
                        # transaction_amount = -sum([int(amount) for amount in sales_purchase_amount_list])
                    )
                    db.session.add(new_transaction)
                    db.session.commit()

                if int(sales_purchase_item_list[i]) >= 30000:
                    new_transaction = Transaction(
                        document_number = document_number,
                        product_code = sales_purchase_item_list[i],
                        account_code = INVENTORY_MATERIAL,
                        transaction_quantity = sales_purchase_quantity_list[i],
                        transaction_amount = int(sales_purchase_amount_list[i])
                        # transaction_amount = -sum([int(amount) for amount in sales_purchase_amount_list])
                    )
                    db.session.add(new_transaction)
                    db.session.commit()

                # 2. 지불유형별, 품목별 부채 계정 금액 계상
                new_transaction = Transaction(
                    document_number = document_number,
                    product_code = sales_purchase_item_list[i],
                    account_code = account,
                    transaction_quantity = sales_purchase_quantity_list[i],
                    transaction_amount = -int(sales_purchase_amount_list[i]) - int(sales_purchase_vat_amount_list[i])
                )
                db.session.add(new_transaction)
                db.session.commit()

                # 3. 부가세 계정 금액 계상
                if int(sales_purchase_vat_amount_list[i]) != 0:
                    new_transaction = Transaction(
                        document_number = document_number,
                        product_code = sales_purchase_item_list[i],
                        account_code = PREPAID_VAT,
                        transaction_quantity = sales_purchase_quantity_list[i],
                        transaction_amount = int(sales_purchase_vat_amount_list[i])
                    )
                    db.session.add(new_transaction)
                    db.session.commit()

        return redirect(url_for('home_blueprint.transaction_init'))

    return render_template('/transaction/transaction_sales_purchase.html', segment = 'transactions',
                           partner_items = partner_list, project_items = project_list, product_items = product_list,
                           document_type = document_type)


@blueprint.route('/transactions/deposit_withdraw', methods = ["GET", "POST"])
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
    bank_account_list = [(bank_account.bank_account_number, bank_account.bank_account_name) for bank_account in
                         bank_accounts]
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

        if document_type == "DE":
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
            if document_type == "DE":
                new_transaction = Transaction(
                    document_number = document_number,
                    account_code = deposit_withdraw_coa_list[i],
                    transaction_amount = -int(deposit_withdraw_amount_list[i])
                )
                db.session.add(new_transaction)
                db.session.commit()
            else:
                new_transaction = Transaction(
                    document_number = document_number,
                    account_code = deposit_withdraw_coa_list[i],
                    transaction_amount = int(deposit_withdraw_amount_list[i])
                )
                db.session.add(new_transaction)
                db.session.commit()

        return redirect(url_for('home_blueprint.transaction_init'))

    return render_template('/transaction/transaction_deposit_withdraw.html', segment = 'transactions',
                           partner_items = partner_list, project_items = project_list,
                           bank_accounts = bank_account_list, coa_accounts = coa_account_list,
                           document_type = document_type)


@blueprint.route('/transactions/replacement', methods = ["GET", "POST"])
@login_required
def transaction_replacement():

    """ 대체전표 입력양식의 거래처, 프로젝트의 리스트 항목 구성 """

    document_type = session.get('document_type', None)

    partner_items = Partner.query.all()
    project_items = Project.query.all()
    coa_accounts = ChartOfAccount.query.all()

    partner_list = [(partner.partner_code, partner.partner_name) for partner in partner_items]
    project_list = [(project.project_code, project.project_name) for project in project_items]
    coa_account_list = [(coa_account.account_code, coa_account.account_name) for coa_account in coa_accounts]

    if request.method == "POST":

        """ form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환 """

        transactions_data = request.form

        # ImmutableMultiDict으로부터 데이터 추출
        document_date = transactions_data.get("replacement-date")
        partner = transactions_data.get("replacement-partner")
        project = transactions_data.get("replacement-project")
        document_description = transactions_data.get("replacement-description")
        replacement_debit_coa_list = transactions_data.getlist("replacement-debit-coa-select")
        replacement_debit_amount_list = transactions_data.getlist("replacement-debit-amount-input")
        replacement_credit_coa_list = transactions_data.getlist("replacement-credit-coa-select")
        replacement_credit_amount_list = transactions_data.getlist("replacement-credit-amount-input")

        """ Journal Entry 테이블 입력 """

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
            document_description = document_description,
            user_name = current_user.username,
        )
        db.session.add(new_document)
        db.session.commit()

        """ Transaction 테이블 입력 """

        for i in range(len(replacement_debit_coa_list)):
            new_transaction = Transaction(
                document_number = document_number,
                account_code = replacement_debit_coa_list[i],
                transaction_amount = int(replacement_debit_amount_list[i])
            )
            db.session.add(new_transaction)
            db.session.commit()

        for i in range(len(replacement_credit_coa_list)):
            new_transaction = Transaction(
                document_number = document_number,
                account_code = replacement_credit_coa_list[i],
                transaction_amount = -int(replacement_credit_amount_list[i])
            )
            db.session.add(new_transaction)
            db.session.commit()

        return redirect(url_for('home_blueprint.transaction_init'))

    return render_template('/transaction/transaction_replacement.html', segment = 'transactions',
                           partner_items = partner_list, project_items = project_list, coa_accounts = coa_account_list)


"""
Closing
"""


@blueprint.route('/closing')
@login_required
def closing():
    return render_template('closing.html', segment = 'closing')


"""
Ledgers
"""

@blueprint.route('/ledgers/bank', methods = ["GET", "POST"])
@login_required
def ledger_bank():

    return render_template('ledgers/ledger_bank.html', segment = 'ledger_bank')


@blueprint.route('/ledgers/inventory', methods = ["GET", "POST"])
@login_required
def ledger_inventory():

    return render_template('ledgers/ledger_inventory.html', segment = 'ledger_inventory')


@blueprint.route('/ledgers/account', methods = ["GET", "POST"])
@login_required
def ledger_account():

    """ 계정원장의 계정과목 리스트 항목 구성 """
    coa_accounts = ChartOfAccount.query.all()
    coa_account_list = [(coa_account.account_code, coa_account.account_name) for coa_account in coa_accounts]

    """ 조회결과 display """

    inquiry_account_name = ""
    from_date = ""
    to_date = ""
    final_results = []

    if request.method == "POST":

        # form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환
        inquiry_conditions = request.form

        inquiry_account = inquiry_conditions.get("ledger-account-account")
        from_date = inquiry_conditions.get("ledger-account-from-date")
        to_date = inquiry_conditions.get("ledger-account-to-date")

        # 조회 계정과목 표시를 위한 데이터 추출
        inquiry_account_name = ChartOfAccount.query.filter(
            ChartOfAccount.account_code == inquiry_account).first().account_name

        # sqalchemy의 and_와 with_entities를 이용하여 조회조건에 맞는 전표번호 추출
        inquiry_document = db.session.query(Transaction, JournalEntry, ChartOfAccount).join(JournalEntry).join(
            ChartOfAccount).filter(and_(JournalEntry.document_date >= from_date, JournalEntry.document_date <= to_date,
                                        Transaction.account_code == inquiry_account)).with_entities(
            Transaction.document_number).all()

        # list of tuple을 list로 변환
        inquiry_document_number = [''.join(tuple) for tuple in inquiry_document]

        # 조회 전표번호에 포함된 거래내역 중에서 조회 계정과목 거래를 제외한 결과 추출
        inquiry_results = []

        for doc_num in inquiry_document_number:
            result_transaction = db.session.query(JournalEntry, Transaction, ChartOfAccount).join(
                JournalEntry).join(ChartOfAccount).filter(
                and_(Transaction.document_number == doc_num, Transaction.account_code != inquiry_account)).order_by(
                JournalEntry.document_date.asc()).all()

            inquiry_results += result_transaction

        # List Comprehension 이용해 display 항목을 추출(월별합계를 위해 년월데이터 추가 및 금액 부호는 반대로)
        final_results = [[journal_entry.document_date.replace("-", "")[0:6], journal_entry.document_date,
                          chart_of_account.account_name, journal_entry.document_description,
                          -transaction.transaction_amount] for journal_entry, transaction, chart_of_account in
                         inquiry_results]

    # TODO: 거래처원장 이월금액과 잔액 및 누계금액 추가

    return render_template('ledgers/ledger_account.html', segment = 'ledger_account', coa_accounts = coa_account_list,
                           inquiry_result = final_results, inquiry_account = inquiry_account_name,
                           from_date = from_date, to_date = to_date)


@blueprint.route('/ledgers/partner', methods = ["GET", "POST"])
@login_required
def ledger_partner():

    """ 거래처원장의 거래처 리스트 항목 구성 """
    partner_sales = Partner.query.filter(Partner.partner_type == "S").all()
    partner_purchase = Partner.query.filter(Partner.partner_type == "P").all()
    partner_sales_list = [(partner.partner_code, partner.partner_name) for partner in partner_sales]
    partner_purchase_list = [(partner.partner_code, partner.partner_name) for partner in partner_purchase]

    coa_accounts = db.session.query(Transaction, JournalEntry, ChartOfAccount).join(JournalEntry).join(
        ChartOfAccount).filter(JournalEntry.partner_code != "none").all()
    coa_list = [(chart_of_account.account_code, chart_of_account.account_name) for
                transaction, journal_entry, chart_of_account in coa_accounts]
    coa_remove_duplicate_list = [t for t in (set(tuple(i) for i in coa_list))]

    """ 조회결과 display """

    inquiry_partner_name = ""
    inquiry_coa_name = ""
    from_date = ""
    to_date = ""
    final_results = []

    if request.method == "POST":
        # form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환
        inquiry_conditions = request.form

        inquiry_partner = inquiry_conditions.get("ledger-partner-partner")
        inquiry_coa = inquiry_conditions.get("ledger-partner-coa")
        from_date = inquiry_conditions.get("ledger-partner-from-date")
        to_date = inquiry_conditions.get("ledger-partner-to-date")

        # 조회 거래처 표시를 위한 데이터 추출
        inquiry_partner_name = Partner.query.filter(Partner.partner_code == inquiry_partner).first().partner_name

        # sqalchemy의 and_를 이용하여 조회조건에 맞는 거래 추출
        if inquiry_coa == "all":
            inquiry_transactions = db.session.query(Transaction, JournalEntry, ChartOfAccount).join(JournalEntry).join(
                ChartOfAccount).filter(
                and_(JournalEntry.document_date >= from_date, JournalEntry.document_date <= to_date,
                     JournalEntry.partner_code == inquiry_partner)).all()
            inquiry_coa_name = "전체"

        else:
            inquiry_transactions = db.session.query(Transaction, JournalEntry, ChartOfAccount).join(JournalEntry).join(
                ChartOfAccount).filter(
                and_(JournalEntry.document_date >= from_date, JournalEntry.document_date <= to_date,
                     JournalEntry.partner_code == inquiry_partner, Transaction.account_code == inquiry_coa)).all()
            inquiry_coa_name = ChartOfAccount.query.filter(
                ChartOfAccount.account_code == inquiry_coa).first().account_name

        # List Comprehension 이용해 display 항목을 추출(월별합계를 위해 년월데이터 추가)
        final_results = [[journal_entry.document_date.replace("-", "")[0:6], journal_entry.document_date,
                          journal_entry.document_description, chart_of_account.account_name,
                          transaction.transaction_amount] for transaction, journal_entry, chart_of_account in
                         inquiry_transactions]

    # TODO: 계정원장 이월금액과 잔액 및 누계금액 추가

    return render_template('ledgers/ledger_partner.html', segment = 'ledger_partner',
                           partner_sales_items = partner_sales_list, partner_purchase_items = partner_purchase_list,
                           coa_items = coa_remove_duplicate_list, inquiry_result = final_results,
                           inquiry_partner = inquiry_partner_name, inquiry_coa = inquiry_coa_name,
                           from_date = from_date, to_date = to_date)


"""
Reports
"""


@blueprint.route('/reports/trial', methods = ["GET", "POST"])
@login_required
def report_trial():

    """ 시산표의 프로젝트 리스트 항목 구성 """
    projects = Project.query.all()
    project_list = [(project.project_code, project.project_name) for project in projects]

    year = ""
    month = ""
    day = ""
    inquiry_project_name = ""
    final_results = []

    if request.method == "POST":

        # form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환
        inquiry_conditions = request.form

        inquiry_project = inquiry_conditions.get("report-trial-project")
        inquiry_month = inquiry_conditions.get("report-trial-month")

        # calendar module의 _monthlen()을 이용하여 조회화면의 기간 표시
        year_month = inquiry_month.split("-")
        length_of_month = _monthlen(int(year_month[0]), int(year_month[1]))
        year = year_month[0]
        month = year_month[1]
        day = length_of_month

        # 조회 프로젝트 표시를 위한 데이터 추출
        if inquiry_project != "all":
            inquiry_project_name = Project.query.filter(Project.project_code == inquiry_project).first().project_name
        else:
            inquiry_project_name = "전체"

        # sqalchemy의 and_를 이용하여 조회조건에 맞는 거래 추출
        from_date = str(year) + "-01-01"
        to_date = str(year) + "-" + str(month) + "-" + str(day)

        if inquiry_project == "all":
            # 계정별/차대별 합계 금액
            inquiry_transactions_debit_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= from_date,
                JournalEntry.document_date <= to_date),
                Transaction.transaction_amount > 0
            ) \
                .group_by(ChartOfAccount.account_code) \
                .all()
            inquiry_transactions_credit_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= from_date,
                JournalEntry.document_date <= to_date),
                Transaction.transaction_amount < 0
            ) \
                .group_by(ChartOfAccount.account_code) \
                .all()
        else:
            inquiry_transactions_debit_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= from_date,
                JournalEntry.document_date <= to_date),
                JournalEntry.project_code == inquiry_project,
                Transaction.transaction_amount > 0
            ) \
                .group_by(ChartOfAccount.account_code) \
                .all()
            inquiry_transactions_credit_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= from_date,
                JournalEntry.document_date <= to_date),
                JournalEntry.project_code == inquiry_project,
                Transaction.transaction_amount < 0
            ) \
                .group_by(ChartOfAccount.account_code) \
                .all()

        # List Comprehension 이용해 display 항목을 추출
        final_results_debit_sum = {chart_of_account.account_code: sum_amount for
                                   journal_entry, transaction, chart_of_account, sum_amount in
                                   inquiry_transactions_debit_sum}
        final_results_credit_sum = {chart_of_account.account_code: sum_amount for
                                    journal_entry, transaction, chart_of_account, sum_amount in
                                    inquiry_transactions_credit_sum}
        final_results_balance = {key: final_results_debit_sum.get(key, 0) + final_results_credit_sum.get(key, 0) for key
                                 in set(final_results_debit_sum) | set(final_results_credit_sum)}

        print(final_results_debit_sum)
        print(final_results_credit_sum)
        print(final_results_balance)

        # 잔액을 기준으로 계정의 차변, 대변 합계와 잔액 데이터 결합
        merge_results = {}
        for key in set(final_results_balance.keys()):
            try:
                merge_results.setdefault(key, []).append(final_results_debit_sum[key])
            except KeyError:
                merge_results.setdefault(key, []).append(0)
            try:
                merge_results.setdefault(key, []).append(final_results_credit_sum[key])
            except KeyError:
                merge_results.setdefault(key, []).append(0)
            merge_results.setdefault(key, []).append(final_results_balance[key])

        # 계정코드를 기준으로 정렬
        sorted_results = sorted(merge_results.items())

        # 계정과목 이름을 추출
        sorted_account_name = []
        for item in sorted_results:
            account_name = ChartOfAccount.query.filter(ChartOfAccount.account_code == item[0]).first().account_name
            sorted_account_name.append(account_name)

        # 계정과목 이름 기준으로 정렬된 최종 결과
        for i in range(len(sorted_results)):
            final_results.append((sorted_account_name[i], sorted_results[i][1]))

        print(final_results)

    return render_template('reports/report_trial.html', segment = 'report_trial', projects = project_list,
                           inquiry_result = final_results, inquiry_project = inquiry_project_name, year = year,
                           to_month = month, to_day = day)


@blueprint.route('/reports/bs', methods = ["GET", "POST"])
@login_required
def report_bs():

    """ 재무상태표의 프로젝트 리스트 항목 구성 """

    projects = Project.query.all()
    project_list = [(project.project_code, project.project_name) for project in projects]

    """ 재무상태표 display """

    # 재무상태표 정보 표시
    current_year = ""
    prior_year = ""
    current_month = ""
    current_day = ""
    inquiry_project_name = ""
    final_results = []
    sums_of_account_cur = []
    sums_of_account_pre = []

    if request.method == "POST":

        # form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환
        inquiry_conditions = request.form

        inquiry_project = inquiry_conditions.get("report-bs-project")
        inquiry_month = inquiry_conditions.get("report-bs-month")

        # calendar module의 _monthlen()을 이용하여 조회화면의 기간 표시
        current_year_month = inquiry_month.split("-")
        length_of_month = _monthlen(int(current_year_month[0]), int(current_year_month[1]))
        current_year = current_year_month[0]
        prior_year = str(int(current_year) - 1)
        current_month = current_year_month[1]
        current_day = str(length_of_month)

        # 조회 프로젝트 표시를 위한 데이터 추출
        if inquiry_project != "all":
            inquiry_project_name = Project.query.filter(Project.project_code == inquiry_project).first().project_name
        else:
            inquiry_project_name = "전체"

        # sqalchemy의 and_를 이용하여 조회조건에 맞는 거래 추출
        current_from_date = current_year + "-01-01"
        current_to_date = current_year + "-" + current_month + "-" + current_day
        prior_from_date = prior_year + "-01-01"
        prior_to_date = prior_year + "-12-31"

        if inquiry_project == "all":
            # 자산-부채-자본 계정별 합계 금액
            current_inquiry_transactions_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= current_from_date,
                JournalEntry.document_date <= current_to_date),
                Transaction.account_code < 40000) \
                .group_by(ChartOfAccount.account_code) \
                .all()
            prior_inquiry_transactions_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= prior_from_date,
                JournalEntry.document_date <= prior_to_date),
                Transaction.account_code < 40000) \
                .group_by(ChartOfAccount.account_code) \
                .all()
        else:
            current_inquiry_transactions_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= current_from_date,
                JournalEntry.document_date <= current_to_date),
                Transaction.account_code < 40000,
                JournalEntry.project_code == inquiry_project, ) \
                .group_by(ChartOfAccount.account_code) \
                .all()
            prior_inquiry_transactions_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= prior_from_date,
                JournalEntry.document_date <= prior_to_date),
                Transaction.account_code < 40000,
                JournalEntry.project_code == inquiry_project, ) \
                .group_by(ChartOfAccount.account_code) \
                .all()

        # List Comprehension 이용해 display 항목을 추출
        current_final_results = {chart_of_account.account_code: [chart_of_account.account_name, sum_amount] for
                                 journal_entry, transaction, chart_of_account, sum_amount in
                                 current_inquiry_transactions_sum}
        prior_final_results = {chart_of_account.account_code: [chart_of_account.account_name, sum_amount] for
                                  journal_entry, transaction, chart_of_account, sum_amount in
                                  prior_inquiry_transactions_sum}

        # 당기와 전기 계정과목 코드를 키로 두 데이터 결합
        coa_accounts = sorted(set(current_final_results) | set(prior_final_results))

        for account in coa_accounts:
            if account in current_final_results.keys():
                if account in prior_final_results.keys():
                    final_results.append((account, current_final_results[account][0], current_final_results[account][1],
                                          prior_final_results[account][1]))
                else:
                    final_results.append(
                        (account, current_final_results[account][0], current_final_results[account][1], 0))
            else:
                final_results.append(
                    (account, prior_final_results[account][0], 0, prior_final_results[account][1]))

        # 재무상태표 합계 금액(TODO: list of tuple 합 단순화하기)
        quick_asset_cur = 0
        quick_asset_pre = 0
        inventory_cur = 0
        inventory_pre = 0
        tangible_asset_cur = 0
        tangible_asset_pre = 0
        intangible_asset_cur = 0
        intangible_asset_pre = 0
        investment_cur = 0
        investment_pre = 0
        current_liability_cur = 0
        current_liability_pre = 0
        non_current_liability_cur = 0
        non_current_liability_pre = 0
        capital_stock_cur = 0
        capital_stock_pre = 0
        capital_surplus_cur = 0
        capital_surplus_pre = 0
        retained_earning_cur = 0
        retained_earning_pre = 0
        capital_adjustment_cur = 0
        capital_adjustment_pre = 0

        for line in final_results:
            if line[0] < 11200:
                quick_asset_cur += line[2]
                quick_asset_pre += line[3]
            elif 11200 < line[0] < 11300:
                inventory_cur += line[2]
                inventory_pre += line[3]
            elif 12100 < line[0] < 12200:
                tangible_asset_cur += line[2]
                tangible_asset_pre += line[3]
            elif 12200 < line[0] < 12300:
                intangible_asset_cur += line[2]
                intangible_asset_pre += line[3]
            elif 12300 < line[0] < 12400:
                investment_cur += line[2]
                investment_pre += line[3]
            elif 21000 < line[0] < 22000:
                current_liability_cur += line[2]
                current_liability_pre += line[3]
            elif 22000 < line[0] < 23000:
                non_current_liability_cur += line[2]
                non_current_liability_pre += line[3]
            elif 31000 < line[0] < 32000:
                capital_stock_cur += line[2]
                capital_stock_pre += line[3]
            elif 32000 < line[0] < 33000:
                capital_surplus_cur += line[2]
                capital_surplus_pre += line[3]
            elif 33000 < line[0] < 34000:
                retained_earning_cur += line[2]
                retained_earning_pre += line[3]
            elif 34000 < line[0] < 35000:
                capital_adjustment_cur += line[2]
                capital_adjustment_pre += line[3]

        current_asset_cur = quick_asset_cur + inventory_cur
        non_current_asset_cur = tangible_asset_cur + intangible_asset_cur + investment_cur
        sum_of_asset_cur = current_asset_cur + non_current_asset_cur
        sum_of_liability_cur = current_liability_cur + non_current_liability_cur
        sum_of_capital_cur = capital_stock_cur + capital_surplus_cur + retained_earning_cur + capital_adjustment_cur
        sum_of_liability_and_capital_cur = sum_of_liability_cur + sum_of_capital_cur

        current_asset_pre = quick_asset_pre + inventory_pre
        non_current_asset_pre = tangible_asset_pre + intangible_asset_pre + investment_pre
        sum_of_asset_pre = current_asset_pre + non_current_asset_pre
        sum_of_liability_pre = current_liability_pre + non_current_liability_pre
        sum_of_capital_pre = capital_stock_pre + capital_surplus_pre + retained_earning_pre + capital_adjustment_pre
        sum_of_liability_and_capital_pre = sum_of_liability_pre + sum_of_capital_pre

        sums_of_account_cur = [current_asset_cur, quick_asset_cur, inventory_cur, non_current_asset_cur,
                               tangible_asset_cur, intangible_asset_cur, investment_cur, sum_of_asset_cur,
                               -current_liability_cur, -non_current_liability_cur, -sum_of_liability_cur,
                               -capital_stock_cur, -capital_surplus_cur, -retained_earning_cur, -capital_adjustment_cur,
                               -sum_of_capital_cur, -sum_of_liability_and_capital_cur]

        sums_of_account_pre = [current_asset_pre, quick_asset_pre, inventory_pre, non_current_asset_pre,
                               tangible_asset_pre, intangible_asset_pre, investment_pre, sum_of_asset_pre,
                               -current_liability_pre, -non_current_liability_pre, -sum_of_liability_pre,
                               -capital_stock_pre, -capital_surplus_pre, -retained_earning_pre, -capital_adjustment_pre,
                               -sum_of_capital_pre, -sum_of_liability_and_capital_pre]

    return render_template('reports/report_bs.html', segment = 'report_bs', projects = project_list,
                           inquiry_result = final_results, inquiry_project = inquiry_project_name,
                           current_year = current_year, prior_year = prior_year, to_month = current_month,
                           to_day = current_day, sum_account_cur = sums_of_account_cur, sum_account_pre = sums_of_account_pre)


@blueprint.route('/reports/pl', methods=["GET", "POST"])
@login_required
def report_pl():

    """ 손익계산서의 프로젝트 리스트 항목 구성 """

    projects = Project.query.all()
    project_list = [(project.project_code, project.project_name) for project in projects]

    """ 손익계산서 display """

    # 손익계산서 정보 표시
    current_year = ""
    prior_year = ""
    current_from_month = ""
    current_to_month = ""
    current_to_day = ""
    inquiry_project_name = ""
    final_results = []
    sums_of_account_cur = []
    sums_of_account_pre = []

    if request.method == "POST":

        # form 태그의 name 속성을 key값으로, input field값을 value로 하는 ImmutableMultiDict 반환
        inquiry_conditions = request.form

        inquiry_project = inquiry_conditions.get("report-pl-project")
        inquiry_from_month = inquiry_conditions.get("report-pl-from-month")
        inquiry_to_month = inquiry_conditions.get("report-pl-to-month")

        # calendar module의 _monthlen()을 이용하여 조회화면의 기간 표시
        current_year_from_month = inquiry_from_month.split("-")
        current_year_to_month = inquiry_to_month.split("-")
        length_of_month = _monthlen(int(current_year_to_month[0]), int(current_year_to_month[1]))
        current_year = current_year_to_month[0]
        prior_year = str(int(current_year) - 1)
        current_from_month = current_year_from_month[1]
        current_to_month = current_year_to_month[1]
        current_to_day = str(length_of_month)

        # 조회 프로젝트 표시를 위한 데이터 추출
        if inquiry_project != "all":
            inquiry_project_name = Project.query.filter(Project.project_code == inquiry_project).first().project_name
        else:
            inquiry_project_name = "전체"

        # sqalchemy의 and_를 이용하여 조회조건에 맞는 거래 추출
        current_from_date = current_year + "-" + current_from_month + "-01"
        current_to_date = current_year + "-" + current_to_month + "-" + current_to_day
        prior_from_date = prior_year + "-01-01"
        prior_to_date = prior_year + "-12-31"

        if inquiry_project == "all":
            # 수익-비용 계정별 합계 금액
            current_inquiry_transactions_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= current_from_date,
                JournalEntry.document_date <= current_to_date),
                and_(Transaction.account_code > 40000,
                Transaction.account_code < 80000)) \
                .group_by(ChartOfAccount.account_code) \
                .all()
            prior_inquiry_transactions_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= prior_from_date,
                JournalEntry.document_date <= prior_to_date),
                and_(Transaction.account_code > 40000,
                     Transaction.account_code < 80000)) \
                .group_by(ChartOfAccount.account_code) \
                .all()
        else:
            current_inquiry_transactions_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= current_from_date,
                JournalEntry.document_date <= current_to_date),
                and_(Transaction.account_code > 40000,
                     Transaction.account_code < 80000),
                JournalEntry.project_code == inquiry_project)\
                .group_by(ChartOfAccount.account_code) \
                .all()
            prior_inquiry_transactions_sum = db.session.query(
                JournalEntry, Transaction, ChartOfAccount, func.sum(Transaction.transaction_amount)) \
                .join(JournalEntry) \
                .join(ChartOfAccount) \
                .filter(and_(
                JournalEntry.document_date >= prior_from_date,
                JournalEntry.document_date <= prior_to_date),
                and_(Transaction.account_code > 40000,
                     Transaction.account_code < 80000),
                JournalEntry.project_code == inquiry_project, ) \
                .group_by(ChartOfAccount.account_code) \
                .all()

        # List Comprehension 이용해 display 항목을 추출
        current_final_results = {chart_of_account.account_code: [chart_of_account.account_name, sum_amount] for
                                 journal_entry, transaction, chart_of_account, sum_amount in
                                 current_inquiry_transactions_sum}
        prior_final_results = {chart_of_account.account_code: [chart_of_account.account_name, sum_amount] for
                                  journal_entry, transaction, chart_of_account, sum_amount in
                                  prior_inquiry_transactions_sum}

        # 당기와 전기 계정과목 코드를 키로 두 데이터 결합
        coa_accounts = sorted(set(current_final_results) | set(prior_final_results))

        for account in coa_accounts:
            if account in current_final_results.keys():
                if account in prior_final_results.keys():
                    final_results.append((account, current_final_results[account][0], current_final_results[account][1], prior_final_results[account][1]))
                else:
                    final_results.append(
                        (account, current_final_results[account][0], current_final_results[account][1], 0))
            else:
                final_results.append(
                    (account, prior_final_results[account][0], 0, prior_final_results[account][1]))

        # 손익계산서 합계 금액(TODO: list of tuple 합 단순화하기)
        sales_cur = 0
        sales_pre = 0
        cost_of_sales_cur = 0
        cost_of_sales_pre = 0
        gross_profit_cur = 0
        gross_profit_pre = 0
        sell_and_admin_expense_cur = 0
        sell_and_admin_expense_pre = 0
        operating_income_cur = 0
        operating_income_pre = 0
        non_operating_income_cur = 0
        non_operating_income_pre = 0
        non_operating_expense_cur = 0
        non_operating_expense_pre = 0
        ordinary_profit_cur = 0
        ordinary_profit_pre = 0
        extraordinary_income_cur = 0
        extraordinary_income_pre = 0
        extraordinary_expense_cur = 0
        extraordinary_expense_pre = 0
        earnings_before_tax_cur = 0
        earnings_before_tax_pre = 0
        income_tax_expense_cur = 0
        income_tax_expense_pre = 0
        net_income_cur = 0
        net_income_pre = 0

        for line in final_results:
            if 41000 < line[0] < 42000:
                sales_cur += line[2]
                sales_pre += line[3]
            elif 51000 < line[0] < 52000:
                cost_of_sales_cur += line[2]
                cost_of_sales_pre += line[3]
            elif 52000 < line[0] < 53000:
                sell_and_admin_expense_cur += line[2]
                sell_and_admin_expense_pre += line[3]
            elif 42000 < line[0] < 43000:
                non_operating_income_cur += line[2]
                non_operating_income_pre += line[3]
            elif 53000 < line[0] < 54000:
                non_operating_expense_cur += line[2]
                non_operating_expense_pre += line[3]
            elif 43000 < line[0] < 44000:
                extraordinary_income_cur += line[2]
                extraordinary_income_pre += line[3]
            elif 54000 < line[0] < 55000:
                extraordinary_expense_cur += line[2]
                extraordinary_expense_pre += line[3]
            elif 55000 < line[0] < 56000:
                income_tax_expense_cur += line[2]
                income_tax_expense_pre += line[3]

        gross_profit_cur = -sales_cur - cost_of_sales_cur
        operating_income_cur = gross_profit_cur - sell_and_admin_expense_cur
        ordinary_profit_cur = operating_income_cur - non_operating_income_cur - non_operating_expense_cur
        earnings_before_tax_cur = ordinary_profit_cur - extraordinary_income_cur - extraordinary_expense_cur
        net_income_cur = earnings_before_tax_cur - income_tax_expense_cur

        gross_profit_pre = -sales_pre - cost_of_sales_pre
        operating_income_pre = gross_profit_pre - sell_and_admin_expense_pre
        ordinary_profit_pre = operating_income_pre - non_operating_income_pre - non_operating_expense_pre
        earnings_before_tax_pre = ordinary_profit_pre - extraordinary_income_pre - extraordinary_expense_pre
        net_income_pre = earnings_before_tax_pre - income_tax_expense_pre

        sums_of_account_cur = [-sales_cur, cost_of_sales_cur, gross_profit_cur, sell_and_admin_expense_cur, operating_income_cur, -non_operating_income_cur, non_operating_expense_cur, ordinary_profit_cur, -extraordinary_income_cur, extraordinary_expense_cur, earnings_before_tax_cur, net_income_cur]

        sums_of_account_pre = [-sales_pre, cost_of_sales_pre, gross_profit_pre, sell_and_admin_expense_pre, operating_income_pre, -non_operating_income_pre, non_operating_expense_pre, ordinary_profit_pre, -extraordinary_income_pre, extraordinary_expense_pre, earnings_before_tax_pre, net_income_pre]

    return render_template('reports/report_pl.html', segment = 'report_pl', projects = project_list,
                           inquiry_result = final_results, inquiry_project = inquiry_project_name,
                           current_year = current_year, prior_year = prior_year, current_from_month=current_from_month, current_to_month = current_to_month,
                           current_to_day = current_to_day, sum_account_cur = sums_of_account_cur, sum_account_pre = sums_of_account_pre)


@blueprint.route('/reports/cost', methods=["GET", "POST"])
@login_required
def report_cost():
    return render_template('reports/report_cost.html', segment = 'report_cost')

"""
Settings
"""
