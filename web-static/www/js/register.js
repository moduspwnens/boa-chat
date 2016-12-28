'use strict';

app.controller('registerController', function($scope, $http, $state, $cookieStore, webchatService) {
  
  $scope.$state = $state;
  
  $scope.registerFormSubmitted = function() {
    
    if ($scope.password !== $scope.passwordConfirm) {
      alert("Password fields don't match.");
      return false;
    }
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.registerUser($scope.email, $scope.password)
      .then(function(registrationId) {
        $scope.ajaxOperationInProgress = false;
        
        var registrationEmailMap = $cookieStore.get("registration-email-map") || {};
        registrationEmailMap[registrationId] = $scope.email;
        $cookieStore.put("registration-email-map", registrationEmailMap);
        
        $state.go('email-verify', { mode: 'register', uniqueId: registrationId });
        
      })
      .catch(function(errorReason) {
        $scope.ajaxOperationInProgress = false;
        
        if (errorReason != "Other") {
          alert(errorReason);
          focusEmailField();
        }
        else {
          alert("An unexpected error occurred when trying to register.");
          focusEmailField();
        }
      })
  }
  
  var focusEmailField = function() {
    window.setTimeout(function() {
      document.getElementById("inputEmail").focus();
    }, 0);
  }
});