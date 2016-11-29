'use strict';

app.controller('loginController', function($scope, $http, $state, $cookieStore, webchatService) {
  
  $scope.$state = $state;
  
  $scope.loginFormSubmitted = function() {
    console.log("Attempting login.");
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.logIn($scope.email, $scope.password)
      .then(function(response) {
        $scope.ajaxOperationInProgress = false;
        
        console.log("Login successful.");
        
        $state.go('home');
      })
      .catch(function(errorReason) {
        $scope.ajaxOperationInProgress = false;
        
        if (errorReason == "UserNotFound") {
          alert("No user found with the given e-mail address." + "\n\n" + "Note that the e-mail address must be confirmed to log in.");
          focusEmailField();
        }
        else if (errorReason == "PasswordIncorrect") {
          alert("The password entered is not correct.");
        }
        else {
          alert("An unexpected error occurred when trying to log in.");
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