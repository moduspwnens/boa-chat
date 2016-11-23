'use strict';

app.controller('loginController', function($scope, $http, $state, webchatService) {
  
  $scope.formMode = "login";
  
  $scope.mainFormSubmitted = function() {
    if ( $scope.formMode == "login" ) {
      console.log("log in");
      console.log($scope.email);
      console.log($scope.password);
    }
    else {
      console.log("create account");
      console.log($scope.email);
      console.log($scope.password);
      console.log($scope.passwordConfirm);
    }
  }
  
  var updateFormSettingsToMatchFormMode = function() {
    if ($scope.formMode == "login") {
      $scope.title = "Log In";
      $scope.mainActionButtonTitle = "Log in";
      $scope.secondaryButtonTitle = "Create account";
    }
    else {
      $scope.title = "Create account";
      $scope.mainActionButtonTitle = "Create account";
      $scope.secondaryButtonTitle = "Back to log in";
    }
  }
  
  var focusEmailField = function() {
    window.setTimeout(function() {
      document.getElementById("inputEmail").focus();
    }, 0);
  }
  
  $scope.switchFormTypeButtonClicked = function() {
    if ($scope.formMode == "login") {
      $scope.formMode = "create";
    }
    else {
      $scope.formMode = "login";
    }
    updateFormSettingsToMatchFormMode();
    focusEmailField();
  }
  
  updateFormSettingsToMatchFormMode();
});