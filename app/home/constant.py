""" 자동분계용 계정과목 """
# TODO: 세팅 메뉴에서 설정토록 변경

# 매출전표
SALES_ACCOUNT = "41000"          # 매출

ACCOUNT_RECEIVABLE = "11103"     # 외상거래: 외상매출금
DEPOSITS_ON_DEMAND = "11102"     # 계좌이체, E-머니: 보통예금
NOTES_RECEIVABLE = "11104"       # 신용카드: 미수금
CASH = "11101"                   # 현금
PREPAID_EXPENSE = "11105"        # 상품권: 선급비용

VAT_WITHHELD = "21001"           # 부가세 예수금


# 매입전표
INVENTORY = "12001"              # 재고자산

ACCOUNT_PAYABLE = "21002"        # 외상매입금
ACCRUED_PAYABLE = "21003"        # 신용카드: 미지급금

PREPAID_VAT = "11106"            # 부가세 대급금

# 입금전표
