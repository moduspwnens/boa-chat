'use strict';

app.controller('modalSimpleController', function($scope, $state, $uibModalInstance, $cookieStore, config) {
  
  var onDismiss = function () {};
  
  $scope.modalTitle = "Success!";
  if (config.hasOwnProperty("modalTitle")) {
    $scope.modalTitle = config.modalTitle;
  }
  
  $scope.mainIconClass = "glyphicon-ok";
  
  
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
  else if (config.mode == "login-required") {
    
    $scope.dismissButtonTitle = "Log In";
    $scope.mainMessageText = config.message;
    $scope.mainIconClass = "glyphicon-warning-sign";
    
    $cookieStore.put("login-sent-from", undefined);
    
    onDismiss = function() {
      $cookieStore.put("login-sent-from", window.location.pathname + window.location.hash);
      $state.go("login");
    }
    
  }
  else if (config.mode == "invite-tutorial") {
    
    $scope.modalTitle = "Invite";
    $scope.dismissButtonTitle = "Understood";
    $scope.mainIconClass = "glyphicon-user";
    
    $scope.mainMessageText = "To invite another user to this room, simply share its URL.";
    
    onDismiss = function() {
      $cookieStore.put("invite-tutorial-shown", true);
    }
  }
  
  else if (config.mode == "error-404") {
    
    $scope.modalTitle = "Oops!";
    $scope.mainIconClass = "glyphicon-warning-sign";
    
    $scope.mainMessageText = "The page you requested was not found.";
    $scope.dismissButtonTitle = "Home";
    
    onDismiss = function() {
      window.location = "/";
    }
    
  }
  
  else if (config.mode == "error-default") {
    
    $scope.mainMessageText = config.message;
    $scope.mainIconClass = "glyphicon-remove";
    
    onDismiss = function() {
      
    }
    
  }
  
  $scope.dismissButtonClicked = function() {
    $uibModalInstance.close();
    onDismiss();
  }
  
});