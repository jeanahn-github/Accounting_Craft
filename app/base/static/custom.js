///* Transaction 초기화면에서 전표유형 선택시 전표양식 modal 폼 Trigger */
//function triggerModalForm() {
//
//    var radios = document.getElementsByName('transaction-inlineRadioOptions');
//    var radio_value;
//    for(var i = 0; i < radios.length; i++) {
//        if(radios[i].checked){
//            radio_value = radios[i].value;
//        }
//    }
//    console.log(radio_value);
//    document.getElementById("transactionCreateModalLabel").innerHTML = radio_value
//}

/* 전표입력 양식에서 품목 선택시 과세여부, 단가 정보 전달 */
function selectedProductDetail(selectedObject) {

    // 새로운 행 요소의 id 추적
    //TODO: HTML element Node 탐색 단순화 필요
    var salesTaxId = selectedObject.parentElement.nextElementSibling.id;
    var salesCostId = selectedObject.parentElement.nextElementSibling.nextElementSibling.id;

    console.log(salesTaxId, salesCostId);

    var selectedProduct = product_data.filter(product => product[0] === selectedObject.value);

    var selectedTax = selectedProduct[0][2];
    var selectedCost = selectedProduct[0][3];

    //TODO: 과세/면세 표시를 button, text, badget 등의 element로 표시
    document.getElementById(salesTaxId).innerHTML = selectedTax;
    document.getElementById(salesCostId).innerHTML = selectedCost;

}


/* 전표입력 양식에서 수량 입력시 공급가, 부가세, 결재금액 자동계산 */
function salesAmountCalculation(selectedObject) {

    // 수량 필드를 기준으로 상대적 노드를 통해 새로운 행 요소의 id 추적
    //TODO: HTML element Node 탐색 단순화 필요
    var salesTaxId = selectedObject.parentElement.previousElementSibling.previousElementSibling.id;
    var salesCostId = selectedObject.parentElement.previousElementSibling.id;
    var salesQuantityId = selectedObject.id;
    var salesAmountTdId = selectedObject.parentElement.nextElementSibling.id;
    var salesAmountInputId = selectedObject.parentElement.nextElementSibling.nextElementSibling.id;
    var salesVatAmountTdId = selectedObject.parentElement.nextElementSibling.nextElementSibling.nextElementSibling.id;
    var salesVatAmountInputId = selectedObject.parentElement.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling.id;
    var salesItemSumId = selectedObject.parentElement.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling.id;

        // 공급가와 부가세 금액 계산을 위한 과세여부, 수량, 단가 데이터 가져오기
    var salesTax = document.getElementById(salesTaxId).innerHTML;
    var salesQuantity = document.getElementById(salesQuantityId).value;
    var salesCost = document.getElementById(salesCostId).innerHTML;

    var salesTotalCost = salesQuantity * salesCost;

    if (salesTax === "O") {
        var salesAmount = Math.round(salesTotalCost / 1.1);
        var salesVatAmount = salesTotalCost - salesAmount;
    } else {
        var salesAmount = salesTotalCost;
        var salesVatAmount = 0;
    }

    var salesItemSum = salesAmount + salesVatAmount;

    document.getElementById(salesAmountTdId).innerHTML = salesAmount;
    document.getElementById(salesAmountInputId).value = salesAmount;

    document.getElementById(salesVatAmountTdId).innerHTML = salesVatAmount;
    document.getElementById(salesVatAmountInputId).value = salesVatAmount;

    document.getElementById(salesItemSumId).innerHTML = salesItemSum;
}


/* [JQuery] 전표입력 양식에서 테이블의 새로운 품목 입력행 추가 */
//TODO - 모든 행 삭제 후 추가버튼 실행시 작동 안하는 문제 해결 필요
$(document).ready(function() {

  //1. Initialise our variable to keep count of the rows added
  var rowcount = 1;

  $("#button-add-row").click(function(e) {

    e.preventDefault();
    var $tableBody = $("#sales-table-body");
    var $trLast = $tableBody.find("tr:last");

    // 2. Create the new id with the row count
    var newId = "sales-table-row_" + rowcount;

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

  $("#button-delete-row").click(function(e) {

    e.preventDefault();
    var $tableBody = $("#sales-table-body");
    var $trLast = $tableBody.find("tr:last");

    // 행 삭제시 합계금액 업데이트
    var salesTotalSum = parseInt($("#sales-sum-total").html());
    var deletedAmount = parseInt($trLast.find("td:last").html());
    var updatedAmount = salesTotalSum - deletedAmount;

    $trLast.remove();
    $("#sales-sum-total").html(updatedAmount);

    });
});


/* [JQuery] 전표입력 양식에서 테이블의 품목들의 합계금액 표시*/
$(document).ready(function() {

    var sumDataArray = {};
    var salesTotalSum;

    $("#sales-table-body tr td").change(function() {

        //TODO: 수량, 공급가, 부가세에 대한 합도 표시 필요
        //TODO: selector 단순화 필요
        var getId = $(this).next().next().next().next().next().attr("id");
        var getData = parseInt($(this).next().next().next().next().next().html());

        sumDataArray[getId] = getData;

        salesTotalSum = 0

        for (var key in sumDataArray) {
            salesTotalSum += sumDataArray[key];
        };

        $("#sales-sum-total").html(salesTotalSum);

    });
});


/* 전표입력 양식에서 취소 버튼 클릭시 input 데이터 삭제 */
function salesFormReset() {
    document.getElementById("sales-form").reset();
    document.getElementById("sales-tax").innerHTML = "";
    document.getElementById("sales-cost").innerHTML = "";
    document.getElementById("sales-td-amount").innerHTML = "";
    document.getElementById("sales-vat-td-amount").innerHTML = "";
    document.getElementById("sales-item-sum").innerHTML = "";
    document.getElementById("sales-sum-total").innerHTML = "";
}

