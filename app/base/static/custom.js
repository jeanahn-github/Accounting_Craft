/************************** 공통 **************************/

/* HTML 입력 폼에서 Enter key 입력시 Submit 버튼 실행 금지 */
$(document).ready(function() {
  $(window).keydown(function(event){
    if(event.keyCode == 13) {
      event.preventDefault();
      return false;
    }
  });
});


/************************** 전표입력 초기화면 **************************/

/* 전표리스트 pagination 및 포맷팅*/
$(document).ready(function() {
    $('#transaction-table').DataTable( {
        columnDefs: [
                {
                  "render": $.fn.dataTable.render.number( ',', '.', 0, '','' ),
                  "targets":[3, 4,]
                }
            ],
        ordering: false,
        rowGroup: {
            dataSrc: 0,
            startRender: null,
            endRender: function ( rows, group ) {

                var documentRows = rows.rows().data().filter(function(value) {
                    return value[0] === group? true : false;
                });

                var debitSum = documentRows.pluck(3).reduce(function (a, b) {
                        return a + b*1;
                }, 0);

                var creditSum = documentRows.pluck(4).reduce(function (a, b) {
                        return a + b*1;
                }, 0);

                return $('<tr/>')
                    .append( '<td colspan="3">전표 합계</td>' )
                    .append( '<td class="_amount">'+debitSum.toLocaleString()+'</td>' )
                    .append( '<td class="_amount">'+creditSum.toLocaleString()+'</td>' )
                    .append( '<td/>' )
                    .append( '<td/>' )
                    .append( '<td>' );
            },
        }
    } );
} );


/************************** 매출-매입 전표 **************************/

/* 매출-매입 전표 광역변수 선언*/
var salesPurchaseSumDataArray = {};

/* 전표입력 양식에서 품목 선택시 과세여부, 단가 정보 전달 */
function selectedProductDetail(selectedObject) {

    // 새로운 행 요소의 id 추적
    //TODO: HTML element Node 탐색 단순화 필요
    var salesPurchaseTaxId = selectedObject.parentElement.nextElementSibling.id;
    var salesPurchaseCostTdId = selectedObject.parentElement.nextElementSibling.nextElementSibling.id;
    var salesPurchaseCostInputId = selectedObject.parentElement.nextElementSibling.nextElementSibling.nextElementSibling.id;
    // template의 <script> 태그에서 product_data 사전 정의
    var selectedProduct = product_data.filter(product => product[0] === selectedObject.value);
    var selectedTax = selectedProduct[0][2];
    var selectedCost = selectedProduct[0][3];
    var selectedPrice = selectedProduct[0][4];

    if (selectedTax == "O") {
        document.getElementById(salesPurchaseTaxId).innerHTML = "<span class='badge bg-success'>과세</span>";
    } else {
        document.getElementById(salesPurchaseTaxId).innerHTML = "<span class='badge bg-danger'>면세</span>";
    };

    //매출전표인 경우 판매가를, 매입전표인 경우 원가를 적용(template의 <script> 태그에서 document_type 사전 정의)
    if (document_type == "SA") {
        // toLocaleString() 메소드를 이용해 금액에 콤마 표시
        document.getElementById(salesPurchaseCostTdId).innerHTML = selectedPrice.toLocaleString();
        document.getElementById(salesPurchaseCostInputId).value = selectedPrice;
    } else {
        document.getElementById(salesPurchaseCostTdId).innerHTML = selectedCost.toLocaleString();
        document.getElementById(salesPurchaseCostInputId).value = selectedCost;
    };
}


/* 전표입력 양식에서 수량 입력시 공급가, 부가세, 결재금액 자동계산 */
function salesPurchaseAmountCalculation(selectedObject) {

    // 수량 필드를 기준으로 상대적 노드를 통해 새로운 행 요소의 id 추적
    //TODO: HTML element Node 탐색 단순화 필요
    var salesPurchaseTaxId = selectedObject.parentElement.previousElementSibling.previousElementSibling.previousElementSibling.id;
    var salesPurchaseCostInputId = selectedObject.parentElement.previousElementSibling.id;
    var salesPurchaseQuantityId = selectedObject.id;
    var salesPurchaseAmountTdId = selectedObject.parentElement.nextElementSibling.id;
    var salesPurchaseAmountInputId = selectedObject.parentElement.nextElementSibling.nextElementSibling.id;
    var salesPurchaseVatAmountTdId = selectedObject.parentElement.nextElementSibling.nextElementSibling.nextElementSibling.id;
    var salesPurchaseVatAmountInputId = selectedObject.parentElement.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling.id;
    var salesPurchaseItemSumId = selectedObject.parentElement.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling.id;
    var salesPurchaseItemSumInputId = selectedObject.parentElement.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling.id;

    // 공급가와 부가세 금액 계산을 위한 과세여부, 수량, 단가 데이터 가져오기
    var salesPurchaseTax = document.getElementById(salesPurchaseTaxId).children[0].innerHTML;
    var salesPurchaseQuantity = document.getElementById(salesPurchaseQuantityId).value;
    var salesPurchaseCost = document.getElementById(salesPurchaseCostInputId).value;

    var salesPurchaseTotalCost = salesPurchaseQuantity * salesPurchaseCost;

    if (salesPurchaseTax == "과세") {
        var salesPurchaseAmount = Math.round(salesPurchaseTotalCost / 1.1);
        var salesPurchaseVatAmount = salesPurchaseTotalCost - salesPurchaseAmount;
    } else {
        var salesPurchaseAmount = salesPurchaseTotalCost;
        var salesPurchaseVatAmount = 0;
    }

    var salesPurchaseItemSum = salesPurchaseAmount + salesPurchaseVatAmount;

    document.getElementById(salesPurchaseAmountTdId).innerHTML = salesPurchaseAmount.toLocaleString();
    document.getElementById(salesPurchaseAmountInputId).value = salesPurchaseAmount;

    document.getElementById(salesPurchaseVatAmountTdId).innerHTML = salesPurchaseVatAmount.toLocaleString();
    document.getElementById(salesPurchaseVatAmountInputId).value = salesPurchaseVatAmount;

    document.getElementById(salesPurchaseItemSumId).innerHTML = salesPurchaseItemSum.toLocaleString();
    document.getElementById(salesPurchaseItemSumInputId).value = salesPurchaseItemSum;

}


/* [JQuery] 전표입력 양식에서 테이블의 새로운 품목 입력행 추가 */
$(document).ready(function() {

  //1. Initialise our variable to keep count of the rows added
  var rowcount = 1;

  $("#sales-purchase-button-add-row").click(function(e) {

    e.preventDefault();
    var $tableBody = $("#sales-purchase-table-body");
    var $trLast = $tableBody.find("tr:last");

    // 2. Create the new id with the row count
    var newId = "sales-purchase-table-row_" + rowcount;

    // 3. clone the row with our new id and clear new row's contents
    var $trNew = $trLast.clone(true).prop({ id: newId });

    $trNew.find(":input").val("");
    $trNew.find("td").not("td:has(input)").html("");

    // 4. rename each input and give an id
    $.each($trNew.find(":input, td"), function(i, val) {

      oldId = $(this).attr('id');
      inputParts = oldId.split("_");

      $(this).attr('id', String(inputParts[0]) +'_' + rowcount);

    });

    $trLast.after($trNew);

    rowcount++;
  });
});


/* [JQuery] 전표입력 양식에서 테이블의 품목 입력행 삭제 */
$(document).ready(function() {

  $("#sales-purchase-button-delete-row").click(function(e) {

    e.preventDefault();
    var $tableBody = $("#sales-purchase-table-body");
    var $trFirst = $tableBody.find("tr:first");
    var $trLast = $tableBody.find("tr:last");

    // 행 삭제시 합계금액 업데이트
    //TODO: 빈행 삭제시 합계금액 NaN 표시 에러 수정 필요
    var salesPurchaseTotalSum = parseInt($("#sales-purchase-sum-total").html().split(",").join(""));
    var deletedAmount = parseInt($trLast.find("td:last").html().split(",").join(""));
    var updatedAmount = salesPurchaseTotalSum - deletedAmount;

    if ($trLast.attr('id') == $trFirst.attr('id')) {
        $("#sales-purchase-table-body").find("input[type=number], input[type=hidden]").each(function () {
            $(this).val("");
        });

        $("#sales-purchase-table-body").find("select").each(function () {
            $(this).val($(this).find("option[selected]").val());
        });
        $("#sales-purchase-tax").html("");
        $("#sales-purchase-cost-td").html("");
        $("#sales-purchase-td-amount").html("");
        $("#sales-purchase-vat-td-amount").html("");
        $("#sales-purchase-item-sum").html("");
        $("#sales-purchase-sum-total").html("");

        // 결재금액 합계 계산을 위한 array 초기화
        salesPurchaseSumDataArray = {};

    } else {
        $trLast.remove();
        $("#sales-purchase-sum-total").html(updatedAmount.toLocaleString());
    };

  });
});

/* [JQuery] 전표입력 양식에서 테이블의 전체 품목들의 합계금액 표시*/
//TODO: 수량, 공급가, 부가세에 대한 합도 표시 필요
$(document).ready(function(myValue) {

    $("#sales-purchase-table-row td").change(function() {

        //TODO: selector 단순화 필요
        //품목별 합계금액에 대한 hidden input 폼의 id와 value를 가져옴
        var getId = $(this).next().next().next().next().next().next().attr("id");
        var getData = parseInt($(this).next().next().next().next().next().next().val());

        salesPurchaseSumDataArray[getId] = getData;

        var salesPurchaseTotalSum = 0

        for (var key in salesPurchaseSumDataArray) {
            salesPurchaseTotalSum += salesPurchaseSumDataArray[key];
        };

        $("#sales-purchase-sum-total").html(salesPurchaseTotalSum.toLocaleString());

    });
});


/* 전표입력 양식에서 취소 버튼 클릭시 input 데이터 삭제 */
$(document).ready(function() {
  $("#sales-purchase-reset-button").click(function(e) {
    e.preventDefault();

    //품목입력 테이블의 첫 행 제외한 모든 행 삭제
    var $tableBody = $("#sales-purchase-table-body");
    var $trRemove = $tableBody.find("tr:not(:first)");
    $trRemove.remove();

    $("#sales-purchase-form").find("input[type=text], input[type=date], input[type=number], input[type=hidden]").each(function () {
        $(this).val("");
    });
    $("#sales-purchase-inlineRadio1").prop('checked', true);
    $("#sales-purchase-form").find("select").each(function () {
        $(this).val($(this).find("option[selected]").val());
    });
    $("#sales-purchase-tax").html("");
    $("#sales-purchase-cost-td").html("");
    $("#sales-purchase-td-amount").html("");
    $("#sales-purchase-vat-td-amount").html("");
    $("#sales-purchase-item-sum").html("");
    $("#sales-purchase-sum-total").html("");
  });
});


/************************** 입금-출금 전표 **************************/

/* 입금-출금 전표 광역변수 선언 */
var depositWithdrawSumArray = {};

/* [JQuery] 전표입력 양식에서 테이블의 새로운 입력행 추가 */
$(document).ready(function() {

  //1. Initialise our variable to keep count of the rows added
  var rowcount = 1;

  $("#deposit-withdraw-button-add-row").click(function(e) {

    e.preventDefault();
    var $tableBody = $("#deposit-withdraw-tbody");
    var $trLast = $tableBody.find("tr:last");

    // 2. Create the new id with the row count
    var newId = "deposit-withdraw-table-row_" + rowcount;

    // 3. clone the row with our new id and clear new row's contents
    var $trNew = $trLast.clone(true).prop({ id: newId });
    $trNew.find(":input").val("");
    $trNew.find("td").not("td:has(input)").html("");

    // 4. rename each input and give an id
    $.each($trNew.find(":input, td"), function(i, val) {

      oldId = $(this).attr('id');
      inputParts = oldId.split("_");
      $(this).attr('id', String(inputParts[0]) +'_' + rowcount);
    });
    $trLast.after($trNew);
    rowcount++;
  });
});


/* [JQuery] 전표입력 양식에서 테이블의 입력행 삭제 */
$(document).ready(function() {
  $("#deposit-withdraw-button-delete-row").click(function(e) {

    e.preventDefault();

    var $tableBody = $("#deposit-withdraw-tbody");
    var $trFirst = $tableBody.find("tr:first");
    var $trLast = $tableBody.find("tr:last");

    // 행 삭제시 합계금액 업데이트
    //TODO: 빈행 삭제시 합계금액 NaN 표시 에러 수정 필요
    var depositWithdrawSum = parseInt($("#deposit-withdraw-sum").html().split(",").join(""));
    var deletedAmount = parseInt($trLast.find("input").val());
    var updatedAmount = depositWithdrawSum - deletedAmount;

    if ($trLast.attr('id') == $trFirst.attr('id')) {
        $("#deposit-withdraw-tbody").find("input[type=number]").each(function () {
            $(this).val("");
        });

        $("#deposit-withdraw-tbody").find("select").each(function () {
            $(this).val($(this).find("option[selected]").val());
        });
        $("#deposit-withdraw-sum").html("");

        // 합계금액 초기화
        depositWithdrawSumArray = {};

    } else {
        $trLast.remove();
        $("#deposit-withdraw-sum").html(updatedAmount.toLocaleString());
    };
  });
});


/* [JQuery] 전표입력 양식에서 입출금 금액 합계 표시*/
$(document).ready(function() {

    $("#deposit-withdraw-tbody tr input").change(function() {
        var getId = $(this).attr("id");
        var getData = parseInt($(this).val());

        depositWithdrawSumArray[getId] = getData;

        var depositWithdrawSum = 0;

        for (var key in depositWithdrawSumArray) {
            depositWithdrawSum += depositWithdrawSumArray[key];
        };

        $("#deposit-withdraw-sum").html(depositWithdrawSum.toLocaleString());
    });
});


/* 전표입력 양식에서 취소 버튼 클릭시 폼 데이터 삭제 */
$(document).ready(function() {
  $("#deposit-withdraw-reset-button").click(function(e) {
    e.preventDefault();
    $("#deposit-withdraw-form").find("input[type=text], input[type=date], input[type=number], select").each(function () {
                        $(this).val($(this).find("option[selected]").val());
                    });

    $("#deposit-withdraw-sum").html("0");
    });
});


/************************** 대체 전표 **************************/

/* 대체전표 광역변수 선언 */
var replacementDebitSumArray = {};
var replacementCreditSumArray = {};


/* [JQuery] 전표입력 양식에서 테이블의 새로운 입력행 추가 */
$(document).ready(function() {

  //1. Initialise our variable to keep count of the rows added
  var rowcount = 1;

  $("#replacement-debit-button-add-row, #replacement-credit-button-add-row").click(function(e) {

    e.preventDefault();

    if (e.currentTarget.id == "replacement-debit-button-add-row") {
        var $tableBody = $("#replacement-debit-tbody");
    } else {
        var $tableBody = $("#replacement-credit-tbody");
    };

    var $trLast = $tableBody.find("tr:last");

    // 2. Create the new id with the row count
    if (e.currentTarget.id == "replacement-debit-button-add-row") {
        var newId = "replacement-debit-table-row_" + rowcount;
    } else {
        var newId = "replacement-credit-table-row_" + rowcount;
    };

    // 3. clone the row with our new id and clear new row's contents
    var $trNew = $trLast.clone(true).prop({ id: newId });
    $trNew.find(":input").val("");
    $trNew.find("td").not("td:has(input)").html("");

    // 4. rename each input and give an id
    $.each($trNew.find(":input, td"), function(i, val) {

      oldId = $(this).attr('id');
      inputParts = oldId.split("_");
      $(this).attr('id', String(inputParts[0]) +'_' + rowcount);
    });
    $trLast.after($trNew);
    rowcount++;
  });
});


/* [JQuery] 전표입력 양식에서 테이블의 입력행 삭제 */
$(document).ready(function() {

  $("#replacement-debit-button-delete-row, #replacement-credit-button-delete-row").click(function(e) {

    e.preventDefault();

    if (e.currentTarget.id == "replacement-debit-button-delete-row") {
        var $tableBody = $("#replacement-debit-tbody");
    } else {
        var $tableBody = $("#replacement-credit-tbody");
    };
    var $trFirst = $tableBody.find("tr:first");
    var $trLast = $tableBody.find("tr:last");

    // 행 삭제시 합계금액 업데이트
    //TODO: 빈행 삭제시 합계금액 NaN 표시 에러 수정 필요
    if (e.currentTarget.id == "replacement-debit-button-delete-row") {
        var replacementDebitSum = parseInt($("#replacement-debit-sum").html().split(",").join(""));
        var deletedAmount = parseInt($trLast.find("input").val());
        var updatedAmount = replacementDebitSum - deletedAmount;
    } else {
        var replacementCreditSum = parseInt($("#replacement-credit-sum").html().split(",").join(""));
        var deletedAmount = parseInt($trLast.find("input").val());
        var updatedAmount = replacementCreditSum - deletedAmount;
    };

    if ($trLast.attr('id') == $trFirst.attr('id')) {
        $tableBody.find("input[type=number]").each(function () {
            $(this).val("");
        });

        $tableBody.find("select").each(function () {
            $(this).val($(this).find("option[selected]").val());
        });
        if (e.currentTarget.id == "replacement-debit-button-delete-row") {
            $("#replacement-debit-sum").html("");
        } else {
            $("#replacement-credit-sum").html("");
        };
        //합계금액 초기화
        replacementDebitSumArray = {};
        replacementCreditSumArray = {};

    } else {
        $trLast.remove();

        if (e.currentTarget.id == "replacement-debit-button-delete-row") {
            $("#replacement-debit-sum").html(updatedAmount.toLocaleString());
        } else {
            $("#replacement-credit-sum").html(updatedAmount.toLocaleString());
        };
    };
  });
});


/* [JQuery] 전표입력 양식에서 차변-대변 금액 합계 표시*/
$(document).ready(function() {

    $("#replacement-debit-tbody tr input, #replacement-credit-tbody tr input").change(function(e) {

        e.preventDefault();

        if (e.currentTarget.name == "replacement-debit-amount-input") {
            var getDebitId = $(this).attr("id");
            var getDebitData = parseInt($(this).val());
            replacementDebitSumArray[getDebitId] = getDebitData;
            var replacementDebitSum = 0;
            for (var key in replacementDebitSumArray) {
                replacementDebitSum += replacementDebitSumArray[key];
            };
            $("#replacement-debit-sum").html(replacementDebitSum.toLocaleString());
        } else {
            var getCreditId = $(this).attr("id");
            var getCreditData = parseInt($(this).val());
            replacementCreditSumArray[getCreditId] = getCreditData;
            var replacementCreditSum = 0;
            for (var key in replacementCreditSumArray) {
                replacementCreditSum += replacementCreditSumArray[key];
            };
            $("#replacement-credit-sum").html(replacementCreditSum.toLocaleString());
        };
    });
});


/* 전표입력 양식에서 취소 버튼 클릭시 폼 데이터 삭제 */
$(document).ready(function() {
  $("#replacement-reset-button").click(function(e) {

    e.preventDefault();

    $("#replacement-form").find("input[type=text], input[type=date], input[type=number], select").each(function () {
                        $(this).val($(this).find("option[selected]").val());
                    });

    $("#replacement-debit-sum").html("0");
    $("#replacement-credit-sum").html("0");
  });
});


/* 전표입력 양식에서 차변금액 합계와 대변금액 합계의 일치 여부 확인 */
function CheckDebitCreditAmount() {

    if ($("#replacement-debit-sum").html() != ($("#replacement-credit-sum").html())) {
        alert("차변금액 합계와 대변금액 합계가 일치하지 않습니다.")
        return false;
    };
}


/************************** Ledgers **************************/

/* 계정원장 및 거래처원장 pagination 및 포맷팅*/
$(document).ready(function() {
    $('._ledger-table').DataTable( {
        columnDefs: [
                {
                  "render": $.fn.dataTable.render.number( ',', '.', 0, '','' ),
                  "targets":[4, 5,]
                }
            ],
        ordering: false,
        rowGroup: {
            dataSrc: 0,
            startRender: null,
            endRender: function ( rows, group ) {

                var monthRows = rows.rows().data().filter(function(value) {
                    return value[0] === group ? true : false;
                });

                var monthDebitSum = monthRows.pluck(4).reduce( function (a, b) {
                        return a + b*1;
                    }, 0);

                var monthCreditSum = monthRows.pluck(5).reduce( function (a, b) {
                        return a + b*1;
                    }, 0);

                return $('<tr/>')
                    .append( '<td colspan="3">월계</td>' )
                    .append( '<td class="_amount">'+monthDebitSum.toLocaleString()+'</td>' )
                    .append( '<td class="_amount">'+monthCreditSum.toLocaleString()+'</td>' )
                    .append( '<td/>' );
            }
        }
    } );

} );

/* 거래처원장 거래처유형 선택시 해당 거래처 리스트 표시*/
$(function() {
    $('input:radio[name="ledger-partner-radios"]').change(function() {
        $('#ledger-partner-partner option').remove();
        if ($(this).val() == 'S') {
            $.each(partner_sales_data, function(key,value) {
                $('#ledger-partner-partner').append($('<option>',
                {value: value[0], text: value[0]+"|"+value[1]}));
            });
        } else {
            $.each(partner_purchase_data, function(key,value) {
                $('#ledger-partner-partner').append($('<option>',
                {value: value[0], text: value[0]+"|"+value[1]}));
            });
        }
    });
});


/************************** Reports **************************/

/* 시산표 합계금액 계산 및 표시*/
$(document).ready(function() {

    var tbody = document.getElementById("report-trial-tbody");
    var sumDebitBalance = 0;
    var sumDebit = 0;
    var sumCredit = 0;
    var sumCreditBalance=0;

    try {
        for(var i=0; i < tbody.rows.length; i++) {

             var debitBalanceTd = tbody.rows[i].cells[0];
             var debitSumTd = tbody.rows[i].cells[1];
             var creditSumTd = tbody.rows[i].cells[3];
             var creditBalanceTd = tbody.rows[i].cells[4];

             sumDebitBalance += parseInt(debitBalanceTd.innerHTML);
             sumDebit += parseInt(debitSumTd.innerHTML);
             sumCredit += parseInt(creditSumTd.innerHTML);
             sumCreditBalance += parseInt(creditBalanceTd.innerHTML);

             debitBalanceTd.innerHTML = parseInt(debitBalanceTd.innerHTML).toLocaleString();
             debitSumTd.innerHTML = parseInt(debitSumTd.innerHTML).toLocaleString();
             creditSumTd.innerHTML = parseInt(creditSumTd.innerHTML).toLocaleString();
             creditBalanceTd.innerHTML = parseInt(creditBalanceTd.innerHTML).toLocaleString();
        };

        document.getElementById("report-trial-debit-balance").innerHTML = sumDebitBalance.toLocaleString();
        document.getElementById("report-trial-debit-sum").innerHTML = sumDebit.toLocaleString();
        document.getElementById("report-trial-credit-sum").innerHTML = sumCredit.toLocaleString();
        document.getElementById("report-trial-credit-balance").innerHTML = sumCreditBalance.toLocaleString();

    } catch(error) {
        if (error instanceof TypeError) {
            return true;
        } else {
            console.error(error);
        }
    }
})

/* 재무제표의 금액셀(_amount 클래스)의 천단위 콤마 표시 */
$(document).ready(function() {

    var amount_cells = $('._financial-statements').find('._amount');

    for (var i=0, len=amount_cells.length|0; i<len; i=i+1|0) {
        amount_cells[i].innerHTML = amount_cells[i].textContent.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
});
