'use strict';

app.controller('forgotVerifyController', function($scope, $state, $stateParams, $cookieStore, $uibModal, webchatService, errorModalDefaultAlert) {
  
  $scope.$state = $state;
  
  $scope.emailAddress = $stateParams.emailAddress;
  
  if ($scope.emailAddress == undefined || $scope.emailAddress == null || $scope.emailAddress.length < 3) {
    errorModalDefaultAlert("E-mail address must be present in URL path.");
    $state.go("forgot");
  }
  
  $scope.forgotPasswordVerificationFormSubmitted = function() {
    
    if ($scope.password !== $scope.passwordConfirm) {
      errorModalDefaultAlert("Passwords entered do not match. Please try again.");
      return;
    }
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.changePasswordWithResetCode($scope.emailAddress, $scope.password, $scope.code)
      .then(function(responseObject) {
        $scope.ajaxOperationInProgress = false;
        
        console.log("Password changed successfully.");
        
        $uibModal.open({
          templateUrl: 'modal-simple.html',
          controller: 'modalSimpleController',
          resolve: {
            config: function() {
              return {
                mode: 'forgot-password-changed'
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
          errorModalDefaultAlert("An unexpected error occurred. Please try again.");
        }
      });
  }
  
});