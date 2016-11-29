'use strict';

app.controller('registerController', function($scope, $http, $state, webchatService) {
  
  $scope.$state = $state;
  
  $scope.registerFormSubmitted = function() {
    
    if ($scope.password !== $scope.passwordConfirm) {
      alert("Password fields don't match.");
      return false;
    }
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.registerUser($scope.email, $scope.password)
      .then(function(userId) {
        $scope.ajaxOperationInProgress = false;
        
        console.log("Registration successful", userId);
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