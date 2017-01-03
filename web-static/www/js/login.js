'use strict';

app.controller('loginController', function($scope, $http, $state, $cookieStore, webchatService) {
  
  $scope.$state = $state;
  
  $scope.email = $cookieStore.get("last-logged-in-email");
  
  $scope.loginFormSubmitted = function() {
    console.log("Attempting login.");
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.logIn($scope.email, $scope.password)
      .then(function(response) {
        $scope.ajaxOperationInProgress = false;
        
        console.log("Login successful.");
        
        $cookieStore.put("last-logged-in-email", $scope.email);
        
        var loginSentFrom = $cookieStore.get("login-sent-from");
        
        if (!angular.isUndefined(loginSentFrom)) {
          console.log("Sending to page attempted to access that prompted login.");
          window.location = loginSentFrom;
          $cookieStore.put("login-sent-from", undefined);
        }
        else {
          $state.go('home');
        }
        
      })
      .catch(function(errorReason) {
        $scope.ajaxOperationInProgress = false;
        
        if (errorReason !== "Other") {
          alert(errorReason);
          focusEmailField();
        }
        else {
          alert("An unexpected error occurred when trying to log in.");
          focusEmailField();
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
  
  var focusPasswordField = function() {
    focusElementById("inputPassword");
  }
  
  if (!angular.isUndefined($scope.email)) {
    focusPasswordField();
  }
  
});