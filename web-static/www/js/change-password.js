'use strict';

app.controller('changePasswordController', function($scope, $http, $state, $cookieStore, $uibModal, webchatService) {
  
  $scope.$state = $state;
  
  var loginObject = $cookieStore.get("login");
  if (angular.isUndefined(loginObject)) {
    console.log("User is not logged in.");
    $state.go('home');
    return;
  }
  
  $scope.changePasswordFormSubmitted = function() {
    
    if ($scope.password !== $scope.passwordConfirm) {
      alert("New password fields don't match.");
      return false;
    }
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.changePasswordWithExistingPassword($scope.oldPassword, $scope.password)
      .then(function() {
        $scope.ajaxOperationInProgress = false;
        
        $uibModal.open({
          templateUrl: 'modal-simple.html',
          controller: 'modalSimpleController',
          resolve: {
            config: function() {
              return {
                mode: 'authenticated-password-changed'
              }
            }
          }
        });
        
      })
      .catch(function(errorReason) {
        $scope.ajaxOperationInProgress = false;
        
        if (errorReason !== "Other") {
          alert(errorReason);
        }
        else {
          alert("An unexpected error occurred when trying to register.");
          
        }
      })
  }
});