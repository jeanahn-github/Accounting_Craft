""" 자동분계용 계정과목 """
# TODO: 세팅 메뉴에서 설정토록 변경

# 매출전표
SALES_ACCOUNT_GOOD = "41001"     # 상품매출액
SALES_ACCOUNT_PRODUCT = "41002"  # 제품매출액


ACCOUNT_RECEIVABLE = "11105"     # 외상거래: 외상매출금
DEPOSITS_ON_DEMAND = "11102"     # 계좌이체, E-머니: 보통예금
NOTES_RECEIVABLE = "11110"       # 신용카드: 미수금
CASH = "11101"                   # 현금
PREPAID_EXPENSE = "11112"        # 상품권: 선급비용

VAT_WITHHELD = "21004"           # 부가세 예수금


# 매입전표
INVENTORY_GOOD = "11201"        # 상품재고
INVENTORY_PRODUCT = "11202"     # 제품재고
INVENTORY_MATERIAL = "11204"    # 원재료재고

ACCOUNT_PAYABLE = "21001"        # 외상매입금
ACCRUED_PAYABLE = "21007"        # 신용카드: 미지급금

PREPAID_VAT = "11113"            # 부가세 대급금

# 입금전표

