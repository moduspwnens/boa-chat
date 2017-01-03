'use strict';

app.controller('emailVerifyController', function($scope, $state, $stateParams, $cookieStore, $uibModal, webchatService, errorModalDefaultAlert) {
  
  $scope.$state = $state;
  
  $scope.mode = $stateParams.mode;
  
  var registrationId = $stateParams.uniqueId;
  
  if ($stateParams.mode == "register") {
    var registrationEmailMap = $cookieStore.get("registration-email-map") || {};
    $scope.emailAddress = registrationEmailMap[registrationId];
  }
  
  $scope.emailVerificationFormSubmitted = function() {
    
    $scope.ajaxOperationInProgress = true;
    
    if ($stateParams.mode == "register") {
      
      webchatService.confirmRegistrationEmailAddress(registrationId, $scope.code)
        .then(function(emailAddress) {
          $scope.ajaxOperationInProgress = false;
        
          console.log("E-mail address confirmed successfully.");
        
          $cookieStore.put("last-logged-in-email", emailAddress);
        
          $uibModal.open({
            templateUrl: 'modal-simple.html',
            controller: 'modalSimpleController',
            resolve: {
              config: function() {
                return {
                  mode: 'register-email-confirmed'
                }
              }
            }
          });
        
        })
        .catch(function(errorReason) {
          $scope.ajaxOperationInProgress = false;
        
          if (errorReason != "Other") {
            errorModalDefaultAlert(errorReason);
          }
          else {
            errorModalDefaultAlert("An unexpected error occurred when trying to confirm your e-mail address.");
          }
        
          focusCodeInputField();
        })
    }
    else {
      
      webchatService.confirmChangedEmailAddress($scope.code)
        .then(function(emailAddress) {
          $scope.ajaxOperationInProgress = false;
      
          console.log("E-mail address confirmed successfully.");
      
          $cookieStore.put("last-logged-in-email", emailAddress);
          
          var loginObject = $cookieStore.get("login");
          loginObject["user"]["email-address"] = emailAddress;
          $cookieStore.put("login", loginObject);
      
          $uibModal.open({
            templateUrl: 'modal-simple.html',
            controller: 'modalSimpleController',
            resolve: {
              config: function() {
                return {
                  mode: 'update-email-confirmed'
                }
              }
            }
          });
      
        })
        .catch(function(errorReason) {
          $scope.ajaxOperationInProgress = false;
      
          if (errorReason != "Other") {
            errorModalDefaultAlert(errorReason);
          }
          else {
            errorModalDefaultAlert("An unexpected error occurred when trying to confirm your e-mail address.");
          }
      
          focusCodeInputField();
        })
    }
  }
  
  var focusCodeInputField = function() {
    window.setTimeout(function() {
      document.getElementById("inputCode").focus();
    }, 0);
  }
  
});