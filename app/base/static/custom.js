/************************** 전표입력 초기화면 **************************/

/* 전표리스트 pagination 및 포맷팅*/
$(document).ready(function() {
    $('#transaction-table').DataTable( {
        "pagingType": "full_numbers",
        "columnDefs": [
                {
                  "render": $.fn.dataTable.render.number( ',', '.', 0, '','' ),
                  "targets":[3, 4,]
                }
            ],
        ordering: false,
        order: [[0, 'asc']],
        rowGroup: {
            startRender: null,
            endRender: function ( rows, group ) {
                var debitSum = rows
                    .data()
                    .pluck(3)
                    .reduce( function (a, b) {
                        return a + b*1;
                    }, 0);

                var creditSum = rows
                    .data()
                    .pluck(4)
                    .reduce( function (a, b) {
                        return a + b*1;
                    }, 0);

                return $('<tr/>')
                    .append( '<td colspan="3">합계금액</td>' )
                    .append( '<td class="_amount">'+debitSum.toFixed(0)+'</td>' )
                    .append( '<td class="_amount">'+creditSum.toFixed(0)+'</td>' )
                    .append( '<td/>' )
                    .append( '<td/>' )
                    .append( '<td>' );
            },
            dataSrc: 0
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

    var selectedProduct = product_data.filter(product => product[0] === selectedObject.value);
    var selectedTax = selectedProduct[0][2];
    var selectedCost = selectedProduct[0][3];

    if (selectedTax == "O") {
        document.getElementById(salesPurchaseTaxId).innerHTML = "<span class='badge bg-success'>과세</span>";
    } else {
        document.getElementById(salesPurchaseTaxId).innerHTML = "<span class='badge bg-danger'>면세</span>";
    }
    document.getElementById(salesPurchaseCostTdId).innerHTML = selectedCost.toLocaleString();
    document.getElementById(salesPurchaseCostInputId).value = selectedCost;
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
//TODO - 모든 행 삭제 후 추가버튼 실행시 작동 안하는 문제 해결 필요
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

/* [JQuery] 전표입력 양식에서 테이블의 새로운 품목 입력행 추가 */
//TODO - 모든 행 삭제 후 추가버튼 실행시 작동 안하는 문제 해결 필요
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


/* [JQuery] 전표입력 양식에서 테이블의 품목 입력행 삭제 */
$(document).ready(function() {
  $("#deposit-withdraw-button-delete-row").click(function(e) {
    e.preventDefault();
    var $tableBody = $("#deposit-withdraw-tbody");
    var $trLast = $tableBody.find("tr:last");

    // 행 삭제시 합계금액 업데이트
    var depositWithdrawSum = parseInt($("#deposit-withdraw-sum").html().split(",").join(""));
    console.log(depositWithdrawSum);
    var deletedAmount = parseInt($trLast.find("input").val());
    console.log(deletedAmount);
    var updatedAmount = depositWithdrawSum - deletedAmount;
    console.log(updatedAmount);

    $trLast.remove();
    $("#deposit-withdraw-sum").html(updatedAmount.toLocaleString());
    });
});


/* [JQuery] 전표입력 양식에서 입출금 금액 합계 표시*/
$(document).ready(function() {
    var depositWithdrawSum = 0;
    $("#deposit-withdraw-tbody tr input").change(function() {
        var getId = $(this).attr("id");
        var getData = parseInt($(this).val());
        depositWithdrawSum += getData;
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