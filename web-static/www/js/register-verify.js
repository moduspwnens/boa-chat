'use strict';

app.controller('registerVerifyController', function($scope, $state, $stateParams, $cookieStore, $uibModal, webchatService) {
  
  $scope.$state = $state;
  
  var registrationId = $stateParams.registrationId;
  
  var registrationEmailMap = $cookieStore.get("registration-email-map") || {};
  $scope.registrationEmail = registrationEmailMap[registrationId];
  
  
  $scope.registrationVerificationFormSubmitted = function() {
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.confirmUserEmailAddress(registrationId, $scope.code)
      .then(function() {
        $scope.ajaxOperationInProgress = false;
        
        console.log("E-mail address confirmed successfully.");
        
        $cookieStore.put("last-logged-in-email", $scope.registrationEmail);
        
        $uibModal.open({
          templateUrl: 'modal-registration-confirmed.html',
          controller: 'modalSimpleController'
        });
        
      })
      .catch(function(errorReason) {
        $scope.ajaxOperationInProgress = false;
        
        if (errorReason != "Other") {
          alert(errorReason);
        }
        else {
          alert("An unexpected error occurred when trying to register.");
        }
        
        focusCodeInputField();
      })
  }
  
  var focusCodeInputField = function() {
    window.setTimeout(function() {
      document.getElementById("inputCode").focus();
    }, 0);
  }
  
});