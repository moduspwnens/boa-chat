'use strict';

app.controller('forgotController', function($scope, $http, $state, webchatService) {
  
  $scope.$state = $state;
  
  $scope.forgotPasswordFormSubmitted = function() {
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.requestPasswordResetCode($scope.email)
      .then(function(response) {
        $scope.ajaxOperationInProgress = false;
        
        $state.go('forgot-verify', {emailAddress: $scope.email})
      })
      .catch(function(errorReason) {
        $scope.ajaxOperationInProgress = false;
        
        if (errorReason != "Other") {
          alert(errorReason);
        }
        else {
          alert("An unexpected error occurred. Please try again.");
        }
      })
    
  }
  
  var focusElementById = function(elementId) {
    window.setTimeout(function() {
      document.getElementById(elementId).focus();
    }, 0);
  }
  
  var focusEmailField = function() {
    focusElementById("inputEmail");
  }
  
  focusEmailField();
  
});