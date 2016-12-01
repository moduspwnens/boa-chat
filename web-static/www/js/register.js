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
        
        $state.go('register-verify', { registrationId: registrationId });
        
      })
      .catch(function(errorReason) {
        $scope.ajaxOperationInProgress = false;
        
        if (errorReason == "UserNotFound") {
          alert("No user found with the given e-mail address." + "\n\n" + "Note that the e-mail address must be confirmed to log in.");
          focusEmailField();
        }
        else {
          alert("An unexpected error occurred when trying to register.");
          focusEmailField();
        }
      })
  }
});