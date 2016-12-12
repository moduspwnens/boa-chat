'use strict';

app.controller('modalSimpleController', function($scope, $state, $uibModalInstance, config) {
  
  var onDismiss = function () {};
  
  $scope.dismissButtonTitle = "Dismiss";
  $scope.mainMessageText = "Operation completed successfully.";
  
  if (config.mode == "register-email-confirmed") {
    
    $scope.dismissButtonTitle = "Login";
    $scope.mainMessageText = "Your e-mail address has been confirmed successfully.";
    
    onDismiss = function() {
      $state.go("login");
    }
    
  }
  else if (config.mode == "update-email-confirmed") {
    
    $scope.dismissButtonTitle = "Profile";
    $scope.mainMessageText = "Your e-mail address has been confirmed successfully.";
    
    onDismiss = function() {
      $state.go("profile");
    }
    
  }
  else if (config.mode == "forgot-password-changed") {
    
    $scope.dismissButtonTitle = "Login";
    $scope.mainMessageText = "Your password has been changed successfully.";
    
    onDismiss = function() {
      $state.go("login");
    }
    
  }
  else if (config.mode == "authenticated-password-changed") {
    
    $scope.dismissButtonTitle = "Profile";
    $scope.mainMessageText = "Your password has been changed successfully.";
    
    onDismiss = function() {
      $state.go("profile");
    }
    
  }
  
  $scope.dismissButtonClicked = function() {
    $uibModalInstance.close();
    onDismiss();
  }
  
});